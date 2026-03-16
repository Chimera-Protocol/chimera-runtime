"""Agent management router — Halt/Resume (Art. 14 Human Oversight)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..middleware.auth import require_tier
from ..services.audit_service import AuditService

router = APIRouter(prefix="/agents", tags=["agents"])

# ── Service state ─────────────────────────────────────────────────
_audit_service: Optional[AuditService] = None

# In-memory agent status (reset on restart)
# Format: { agent_name: { "halted": bool, "halted_at": str, "reason": str } }
_agent_status: dict[str, dict] = {}


def init_service(audit_service: AuditService):
    global _audit_service
    _audit_service = audit_service


def _get_svc() -> AuditService:
    if _audit_service is None:
        raise RuntimeError("Agent service not initialized")
    return _audit_service


# ── Request models ────────────────────────────────────────────────

class HaltRequest(BaseModel):
    reason: str = "Manual halt via dashboard"


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("")
async def list_agents(tier: str = Query("free")):
    """Get all agents with stats and halt status."""
    svc = _get_svc()
    svc.refresh()
    agents = svc.get_agent_stats(tier=tier)

    # Enrich with halt status
    for agent in agents:
        status = _agent_status.get(agent["name"], {})
        agent["halted"] = status.get("halted", False)
        agent["halted_at"] = status.get("halted_at")
        agent["halt_reason"] = status.get("reason")

    return {"agents": agents}


@router.post("/{agent_name}/halt", dependencies=[Depends(require_tier("pro"))])
async def halt_agent(agent_name: str, body: HaltRequest):
    """Halt an agent (Art. 14 Human Oversight — stop mechanism)."""
    _agent_status[agent_name] = {
        "halted": True,
        "halted_at": datetime.now(timezone.utc).isoformat(),
        "reason": body.reason,
    }
    return {
        "status": "halted",
        "agent": agent_name,
        "reason": body.reason,
        "halted_at": _agent_status[agent_name]["halted_at"],
    }


@router.post("/{agent_name}/resume", dependencies=[Depends(require_tier("pro"))])
async def resume_agent(agent_name: str):
    """Resume a halted agent."""
    if agent_name in _agent_status:
        _agent_status[agent_name] = {"halted": False}
    return {"status": "running", "agent": agent_name}
