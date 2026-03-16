"""Leads router — collect contact/sales inquiries + admin user stats."""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..middleware.auth import get_current_user, require_tier

router = APIRouter(prefix="/leads", tags=["leads"])

_db_path: Optional[str] = None
_local = threading.local()

_CREATE_LEADS_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    name TEXT,
    company TEXT,
    plan TEXT,
    message TEXT,
    user_email TEXT,
    created_at TEXT NOT NULL
);
"""


def init_service(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    conn = _get_conn()
    conn.execute(_CREATE_LEADS_SQL)
    conn.commit()


def _get_conn() -> sqlite3.Connection:
    if _db_path is None:
        raise RuntimeError("Leads service not initialized")
    key = f"leads_conn_{_db_path}"
    if not hasattr(_local, key) or getattr(_local, key) is None:
        conn = sqlite3.connect(_db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        setattr(_local, key, conn)
    return getattr(_local, key)


# ── Models ─────────────────────────────────────────────────────────

class LeadRequest(BaseModel):
    email: str
    name: str = ""
    company: str = ""
    plan: str = ""
    message: str = ""
    user_email: str = ""


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("")
async def create_lead(body: LeadRequest):
    """Collect a sales/contact inquiry. Public — no auth required."""
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO leads (email, name, company, plan, message, user_email, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (body.email, body.name, body.company, body.plan, body.message, body.user_email, now),
    )
    conn.commit()
    return {"status": "ok", "message": "Thank you! Our team will be in touch soon."}


@router.get("", dependencies=[Depends(require_tier("enterprise"))])
async def list_leads():
    """List all collected leads. Enterprise/admin only."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    return {"leads": [dict(r) for r in rows], "total": len(rows)}


@router.get("/admin/stats", dependencies=[Depends(require_tier("enterprise"))])
async def admin_stats():
    """Admin dashboard stats — user counts, tier distribution, lead count."""
    conn = _get_conn()

    # User stats
    user_rows = conn.execute(
        "SELECT tier, COUNT(*) as count FROM users GROUP BY tier"
    ).fetchall()
    tier_counts = {row["tier"]: row["count"] for row in user_rows}
    total_users = sum(tier_counts.values())

    # Recent users
    recent = conn.execute(
        "SELECT id, email, tier, created_at, last_login FROM users ORDER BY created_at DESC LIMIT 10"
    ).fetchall()

    # Lead stats
    lead_count = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()["c"]

    return {
        "total_users": total_users,
        "tier_distribution": tier_counts,
        "total_leads": lead_count,
        "recent_users": [dict(r) for r in recent],
    }
