"""
Audit API Router — /api/v1/audit/*

Wraps chimera_runtime's AuditQuery for the dashboard.
Tier limits are applied at the service layer (cloud dashboard only).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])

# Service instance — initialized in main.py lifespan
_service: Optional[AuditService] = None


def init_service(audit_dir: str) -> None:
    global _service
    _service = AuditService(audit_dir)


def get_service() -> AuditService:
    if _service is None:
        raise HTTPException(500, "Audit service not initialized")
    return _service


# ========================================================================
# ENDPOINTS
# ========================================================================


@router.get("/agents")
async def list_agents(tier: str = Query("free")):
    """Get list of unique agents and their statistics."""
    svc = get_service()
    svc.refresh()
    return {"agents": svc.get_agent_stats(tier=tier)}


@router.get("/decisions")
async def list_decisions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    result: Optional[str] = Query(None, description="Filter: ALLOWED, BLOCKED, etc."),
    after: Optional[str] = Query(None, description="ISO datetime lower bound"),
    before: Optional[str] = Query(None, description="ISO datetime upper bound"),
    action: Optional[str] = Query(None, description="Filter by action (substring)"),
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    tier: str = Query("free", description="User tier: free, pro, enterprise"),
):
    """Get paginated decision list."""
    svc = get_service()
    svc.refresh()  # Reload from disk to see latest
    return svc.get_decisions(
        page=page, limit=limit, result=result,
        after=after, before=before, action=action, agent=agent, tier=tier,
    )


@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id: str,
    tier: str = Query("free"),
):
    """Get a single decision. Free: summary. Pro+: full detail with reasoning trace."""
    svc = get_service()
    try:
        return svc.get_decision(decision_id, tier=tier)
    except Exception as e:
        raise HTTPException(404, f"Decision not found: {decision_id}")


@router.get("/stats")
async def get_stats(
    tier: str = Query("free"),
    last_days: Optional[int] = Query(None, ge=1),
):
    """Get aggregate audit statistics."""
    svc = get_service()
    svc.refresh()
    return svc.get_stats(tier=tier, last_days=last_days)


@router.get("/violations")
async def get_violations(
    n: int = Query(10, ge=1, le=50),
    tier: str = Query("free"),
):
    """Get top N most frequently triggered constraint violations."""
    svc = get_service()
    svc.refresh()
    return svc.get_violations(n=n, tier=tier)


@router.get("/export")
async def export_decisions(
    format: str = Query("json", description="json, compact, or stats"),
    last_days: Optional[int] = Query(None, ge=1),
    result: Optional[str] = Query(None),
    tier: str = Query("free"),
):
    """Export audit decisions as downloadable JSON."""
    from fastapi.responses import JSONResponse
    svc = get_service()
    svc.refresh()
    data = svc.export_records(format=format, tier=tier, last_days=last_days, result=result)
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename=chimera-audit-{format}.json"},
    )


@router.get("/decisions/{decision_id}/explanation", response_class=HTMLResponse)
async def get_explanation(decision_id: str):
    """Generate Art. 86 HTML explanation report for a single decision."""
    svc = get_service()
    try:
        html = svc.get_explanation_html(decision_id)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(404, f"Decision not found: {decision_id}")
