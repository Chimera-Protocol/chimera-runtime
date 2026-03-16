"""Settings router — API key management (Pro+)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..middleware.auth import get_current_user, require_tier
from ..models.api_key import (
    generate_api_key,
    list_api_keys,
    revoke_api_key,
)

router = APIRouter(prefix="/settings", tags=["settings"])

# ── Service state ─────────────────────────────────────────────────
_db_path: str | None = None


def init_service(db_path: str):
    global _db_path
    _db_path = db_path


def _get_db() -> str:
    if _db_path is None:
        raise RuntimeError("Settings service not initialized")
    return _db_path


# ── Request models ────────────────────────────────────────────────

class CreateApiKeyRequest(BaseModel):
    name: str = "Default"


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/api-keys", dependencies=[Depends(require_tier("pro"))])
async def list_keys(user: dict = Depends(get_current_user)):
    """List all API keys for the current user."""
    keys = list_api_keys(_get_db(), user["id"])
    return {"keys": [k.to_public() for k in keys]}


@router.post("/api-keys", dependencies=[Depends(require_tier("pro"))])
async def create_key(body: CreateApiKeyRequest, user: dict = Depends(get_current_user)):
    """Create a new API key. The raw key is only shown once."""
    # Limit to 5 active keys
    existing = list_api_keys(_get_db(), user["id"])
    active = [k for k in existing if not k.revoked]
    if len(active) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 active API keys allowed")

    record, raw_key = generate_api_key(_get_db(), user["id"], body.name)
    return {
        "key": raw_key,
        "key_prefix": record.key_prefix,
        "name": record.name,
        "id": record.id,
        "created_at": record.created_at,
        "message": "Save this key — it won't be shown again.",
    }


@router.delete("/api-keys/{key_id}", dependencies=[Depends(require_tier("pro"))])
async def revoke_key(key_id: int, user: dict = Depends(get_current_user)):
    """Revoke an API key."""
    success = revoke_api_key(_get_db(), key_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked", "id": key_id}
