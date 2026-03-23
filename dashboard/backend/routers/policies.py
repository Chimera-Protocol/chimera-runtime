"""
Policies API Router — /api/v1/policies/*

Hybrid policy model:
  - Global policies: shared read-only templates
  - User policies: per-user custom policies

Users see both. Create/edit only affects user's own policies.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Body, Depends, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..middleware.auth import get_current_user, get_optional_user
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
async def list_policies(user: Optional[dict] = Depends(get_optional_user)):
    """List all policy files: global templates + user's custom policies."""
    svc = get_service()
    user_id = user["id"] if user else None
    return {"policies": svc.list_policies(user_id=user_id)}


@router.get("/{filename}")
async def get_policy(filename: str, user: Optional[dict] = Depends(get_optional_user)):
    """Get detailed policy information: constraints, variables, domains."""
    svc = get_service()
    user_id = user["id"] if user else None
    try:
        return svc.get_policy(filename, user_id=user_id)
    except Exception as e:
        raise HTTPException(404, f"Policy not found: {filename}")


@router.post("/{filename}/verify")
async def verify_policy(filename: str, user: Optional[dict] = Depends(get_optional_user)):
    """Run Z3 formal verification (CSL) or syntax validation (YAML)."""
    svc = get_service()
    user_id = user["id"] if user else None
    try:
        return svc.verify_policy(filename, user_id=user_id)
    except Exception as e:
        raise HTTPException(400, f"Verification failed: {e}")


@router.post("/{filename}/simulate")
async def simulate_policy(
    filename: str,
    parameters: Dict[str, Any] = Body(..., description="Parameters to evaluate"),
    user: Optional[dict] = Depends(get_optional_user),
):
    """Simulate policy evaluation against given parameters."""
    svc = get_service()
    user_id = user["id"] if user else None
    try:
        return svc.simulate_policy(filename, parameters, user_id=user_id)
    except Exception as e:
        raise HTTPException(400, f"Simulation failed: {e}")


@router.get("/{filename}/content")
async def get_policy_content(filename: str, user: Optional[dict] = Depends(get_optional_user)):
    """Get raw policy file source content for the editor."""
    svc = get_service()
    user_id = user["id"] if user else None
    try:
        return svc.get_policy_content(filename, user_id=user_id)
    except Exception as e:
        raise HTTPException(404, str(e))


class CreatePolicyRequest(BaseModel):
    filename: str
    content: str


@router.post("")
async def create_policy(body: CreatePolicyRequest, user: dict = Depends(get_current_user)):
    """Create a new policy file in user's workspace."""
    svc = get_service()
    try:
        return svc.create_policy(body.filename, body.content, user_id=user["id"])
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/{filename}/fork")
async def fork_policy(filename: str, user: dict = Depends(get_current_user)):
    """Copy a global policy to your workspace for customization."""
    svc = get_service()
    try:
        return svc.copy_global_to_user(filename, user["id"])
    except Exception as e:
        raise HTTPException(400, str(e))


@router.delete("/{filename}")
async def delete_policy(filename: str, user: dict = Depends(get_current_user)):
    """Delete a custom policy from your workspace. Cannot delete global policies."""
    svc = get_service()
    try:
        return svc.delete_user_policy(filename, user["id"])
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
