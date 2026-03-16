"""
Analytics API Router — /api/v1/analytics/*

Time-series aggregation, heatmaps, and performance distributions.
[Pro+ tier]
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from ..services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

_service: Optional[AnalyticsService] = None


def init_service(audit_dir: str) -> None:
    global _service
    _service = AnalyticsService(audit_dir)


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
):
    """Decision trend over time: counts grouped by result type."""
    svc = get_service()
    return svc.get_trend(granularity=granularity, last_days=last_days)


@router.get("/heatmap")
async def get_heatmap(
    last_days: int = Query(30, ge=1, le=365),
):
    """Block rate heatmap: hour-of-day vs day-of-week matrix."""
    svc = get_service()
    return svc.get_heatmap(last_days=last_days)


@router.get("/violations")
async def get_violation_trend(
    last_days: int = Query(30, ge=1, le=365),
):
    """Violation frequency trend over time."""
    svc = get_service()
    return svc.get_violation_trend(last_days=last_days)


@router.get("/performance")
async def get_performance(
    last_days: int = Query(30, ge=1, le=365),
):
    """Performance distribution: latency histograms for total, LLM, policy eval."""
    svc = get_service()
    return svc.get_performance(last_days=last_days)


@router.get("/cost-estimate")
async def get_cost_estimate(
    last_days: int = Query(30, ge=1, le=365),
):
    """LLM cost estimate based on model inference duration."""
    svc = get_service()
    return svc.get_cost_estimate(last_days=last_days)
