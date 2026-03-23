"""
Policies API Router — /api/v1/policies/*

Wraps chimera_runtime's PolicyManager for the dashboard.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Body, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..models.api_key import verify_api_key
from ..services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["policies"])

_service: Optional[PolicyService] = None


def init_service(policies_dir: str) -> None:
    global _service
    _service = PolicyService(policies_dir)


def get_service() -> PolicyService:
    if _service is None:
        raise HTTPException(500, "Policy service not initialized")
    return _service


# ========================================================================
# ENDPOINTS
# ========================================================================


@router.get("")
async def list_policies():
    """List all policy files with summary info."""
    svc = get_service()
    return {"policies": svc.list_policies()}


@router.get("/{filename}")
async def get_policy(filename: str):
    """Get detailed policy information: constraints, variables, domains."""
    svc = get_service()
    try:
        return svc.get_policy(filename)
    except Exception as e:
        raise HTTPException(404, f"Policy not found: {filename}")


@router.post("/{filename}/verify")
async def verify_policy(filename: str):
    """Run Z3 formal verification (CSL) or syntax validation (YAML)."""
    svc = get_service()
    try:
        return svc.verify_policy(filename)
    except Exception as e:
        raise HTTPException(400, f"Verification failed: {e}")


@router.post("/{filename}/simulate")
async def simulate_policy(
    filename: str,
    parameters: Dict[str, Any] = Body(..., description="Parameters to evaluate"),
):
    """Simulate policy evaluation against given parameters. [Pro+]"""
    svc = get_service()
    try:
        return svc.simulate_policy(filename, parameters)
    except Exception as e:
        raise HTTPException(400, f"Simulation failed: {e}")


@router.get("/{filename}/content")
async def get_policy_content(filename: str):
    """Get raw policy file source content for the editor."""
    svc = get_service()
    try:
        return svc.get_policy_content(filename)
    except Exception as e:
        raise HTTPException(404, str(e))


class CreatePolicyRequest(BaseModel):
    filename: str
    content: str


@router.post("")
async def create_policy(body: CreatePolicyRequest):
    """Create a new policy file (CSL or YAML)."""
    svc = get_service()
    try:
        return svc.create_policy(body.filename, body.content)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/{filename}/download")
async def download_policy(filename: str, request: Request):
    """Download raw policy file. Supports both Bearer token and X-API-Key auth."""
    svc = get_service()
    try:
        result = svc.get_policy_content(filename)
        return PlainTextResponse(
            content=result["content"],
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/plain",
            },
        )
    except Exception:
        raise HTTPException(404, f"Policy not found: {filename}")
