"""API Key model — SQLite storage for Pro+ API keys."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .user import _get_conn


@dataclass
class ApiKeyDB:
    id: int
    user_id: int
    key_prefix: str  # First 8 chars for display: "chm_abc1..."
    key_hash: str  # SHA-256 hash of full key
    name: str
    created_at: str
    last_used: Optional[str] = None
    revoked: bool = False

    def to_public(self) -> dict:
        return {
            "id": self.id,
            "key_prefix": self.key_prefix,
            "name": self.name,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "revoked": self.revoked,
        }


_CREATE_API_KEYS_SQL = """
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key_prefix TEXT NOT NULL,
    key_hash TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL DEFAULT 'Default',
    created_at TEXT NOT NULL,
    last_used TEXT,
    revoked INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def create_api_keys_table(db_path: str) -> None:
    conn = _get_conn(db_path)
    conn.execute(_CREATE_API_KEYS_SQL)
    conn.commit()


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key(db_path: str, user_id: int, name: str = "Default") -> tuple[ApiKeyDB, str]:
    """Generate a new API key. Returns (record, raw_key).

    The raw key is only available at creation time.
    """
    raw_key = f"chm_{secrets.token_urlsafe(32)}"
    key_prefix = raw_key[:12] + "..."
    key_hash = _hash_key(raw_key)
    now = datetime.now(timezone.utc).isoformat()

    conn = _get_conn(db_path)
    cursor = conn.execute(
        "INSERT INTO api_keys (user_id, key_prefix, key_hash, name, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, key_prefix, key_hash, name, now),
    )
    conn.commit()

    record = ApiKeyDB(
        id=cursor.lastrowid,
        user_id=user_id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        name=name,
        created_at=now,
    )
    return record, raw_key


def list_api_keys(db_path: str, user_id: int) -> list[ApiKeyDB]:
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return [ApiKeyDB(**dict(row)) for row in rows]


def revoke_api_key(db_path: str, key_id: int, user_id: int) -> bool:
    """Revoke an API key. Returns True if found and revoked."""
    conn = _get_conn(db_path)
    cursor = conn.execute(
        "UPDATE api_keys SET revoked = 1 WHERE id = ? AND user_id = ?",
        (key_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def verify_api_key(db_path: str, raw_key: str) -> Optional[int]:
    """Verify an API key and return user_id if valid. Returns None if invalid."""
    key_hash = _hash_key(raw_key)
    conn = _get_conn(db_path)
    row = conn.execute(
        "SELECT user_id, revoked FROM api_keys WHERE key_hash = ?",
        (key_hash,),
    ).fetchone()

    if row is None or row["revoked"]:
        return None

    # Update last_used
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE api_keys SET last_used = ? WHERE key_hash = ?",
        (now, key_hash),
    )
    conn.commit()

    return row["user_id"]
