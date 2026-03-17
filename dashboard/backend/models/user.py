"""User model — lightweight SQLite via stdlib sqlite3."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import bcrypt


@dataclass
class UserDB:
    id: int
    email: str
    password_hash: str
    tier: str  # "free" | "pro" | "enterprise"
    created_at: str
    last_login: Optional[str] = None

    def to_public(self) -> dict:
        """Return public-safe user dict (no password_hash)."""
        return {
            "id": self.id,
            "email": self.email,
            "tier": self.tier,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free',
    created_at TEXT NOT NULL,
    last_login TEXT
);
"""

_local = threading.local()


def _get_conn(db_path: str) -> sqlite3.Connection:
    """Get thread-local connection (SQLite is not thread-safe by default)."""
    key = f"conn_{db_path}"
    if not hasattr(_local, key) or getattr(_local, key) is None:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        setattr(_local, key, conn)
    return getattr(_local, key)


def create_tables(db_path: str) -> None:
    """Create users table if it doesn't exist."""
    conn = _get_conn(db_path)
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()


def create_user(
    db_path: str,
    email: str,
    password: str,
    tier: str = "free",
) -> UserDB:
    """Create a new user. Raises ValueError if email exists."""
    conn = _get_conn(db_path)
    now = datetime.now(timezone.utc).isoformat()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, tier, created_at) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), password_hash, tier, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"User with email '{email}' already exists")

    return UserDB(
        id=cursor.lastrowid,
        email=email.lower().strip(),
        password_hash=password_hash,
        tier=tier,
        created_at=now,
    )


def get_user_by_email(db_path: str, email: str) -> Optional[UserDB]:
    """Find user by email."""
    conn = _get_conn(db_path)
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    if row is None:
        return None
    return UserDB(**dict(row))


def get_user_by_id(db_path: str, user_id: int) -> Optional[UserDB]:
    """Find user by ID."""
    conn = _get_conn(db_path)
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    return UserDB(**dict(row))


def update_last_login(db_path: str, user_id: int) -> None:
    """Update user's last_login timestamp."""
    conn = _get_conn(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
    conn.commit()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def update_password(db_path: str, user_id: int, new_password: str) -> None:
    """Update user's password."""
    conn = _get_conn(db_path)
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
