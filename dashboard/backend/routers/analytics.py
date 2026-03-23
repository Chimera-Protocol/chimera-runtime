"""
Analytics API Router — /api/v1/analytics/*

Time-series aggregation, heatmaps, and performance distributions.
User-isolated: each user sees only their own data.
[Pro+ tier]
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..middleware.auth import get_optional_user
from ..services.analytics_service import AnalyticsService
from ..services.storage_service import StorageBackend

router = APIRouter(prefix="/analytics", tags=["analytics"])

_service: Optional[AnalyticsService] = None


def init_service(audit_dir: str, storage: Optional[StorageBackend] = None) -> None:
    global _service
    _service = AnalyticsService(audit_dir, storage)


def get_service() -> AnalyticsService:
    if _service is None:
        from fastapi import HTTPException
        raise HTTPException(500, "Analytics service not initialized")
    return _service


# ========================================================================
# ENDPOINTS
# ========================================================================


@router.get("/trend")
async def get_trend(
    granularity: str = Query("daily", description="hourly, daily, or weekly"),
    last_days: int = Query(30, ge=1, le=365),
    user: Optional[dict] = Depends(get_optional_user),
):
    """Decision trend over time: counts grouped by result type."""
    svc = get_service()
    user_id = user["id"] if user else None
    return svc.get_trend(granularity=granularity, last_days=last_days, user_id=user_id)


@router.get("/heatmap")
async def get_heatmap(
    last_days: int = Query(30, ge=1, le=365),
    user: Optional[dict] = Depends(get_optional_user),
):
    """Block rate heatmap: hour-of-day vs day-of-week matrix."""
    svc = get_service()
    user_id = user["id"] if user else None
    return svc.get_heatmap(last_days=last_days, user_id=user_id)


@router.get("/violations")
async def get_violation_trend(
    last_days: int = Query(30, ge=1, le=365),
    user: Optional[dict] = Depends(get_optional_user),
):
    """Violation frequency trend over time."""
    svc = get_service()
    user_id = user["id"] if user else None
    return svc.get_violation_trend(last_days=last_days, user_id=user_id)


@router.get("/performance")
async def get_performance(
    last_days: int = Query(30, ge=1, le=365),
    user: Optional[dict] = Depends(get_optional_user),
):
    """Performance distribution: latency histograms for total, LLM, policy eval."""
    svc = get_service()
    user_id = user["id"] if user else None
    return svc.get_performance(last_days=last_days, user_id=user_id)


@router.get("/cost-estimate")
async def get_cost_estimate(
    last_days: int = Query(30, ge=1, le=365),
    user: Optional[dict] = Depends(get_optional_user),
):
    """LLM cost estimate based on model inference duration."""
    svc = get_service()
    user_id = user["id"] if user else None
    return svc.get_cost_estimate(last_days=last_days, user_id=user_id)
