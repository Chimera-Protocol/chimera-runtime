"""Auth middleware — FastAPI dependencies for authentication and tier gating."""

from __future__ import annotations

from typing import Optional

from fastapi import Request, HTTPException


# Module-level service reference (initialized by main.py lifespan)
_auth_service = None


def init_auth_middleware(auth_service):
    """Initialize with auth service instance."""
    global _auth_service
    _auth_service = auth_service


async def get_optional_user(request: Request) -> Optional[dict]:
    """Extract user from Bearer token if present. Returns None if no token.

    This is a non-blocking dependency — endpoints still work without auth
    but can use user info if available.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    if not _auth_service:
        return None

    try:
        return _auth_service.get_current_user(token)
    except Exception:
        return None


async def get_current_user(request: Request) -> dict:
    """Require authenticated user. Raises 401 if no valid token."""
    user = await get_optional_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def get_tier(request: Request, user: Optional[dict] = None) -> str:
    """Get tier from auth user or fallback to query parameter.

    Priority: authenticated user tier > query param > "free"
    """
    if user and "tier" in user:
        return user["tier"]

    # Fallback to query parameter for backward compatibility
    return request.query_params.get("tier", "free")


def require_tier(min_tier: str):
    """Factory for tier-gating dependencies.

    Usage:
        @router.get("/analytics/trend", dependencies=[Depends(require_tier("pro"))])
    """
    TIER_LEVELS = {"free": 0, "pro": 1, "enterprise": 2}
    min_level = TIER_LEVELS.get(min_tier, 0)

    async def _check_tier(request: Request):
        user = await get_optional_user(request)
        tier = get_tier(request, user)
        user_level = TIER_LEVELS.get(tier, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=403,
                detail=f"This feature requires {min_tier} tier or above. Current tier: {tier}",
            )

    return _check_tier
