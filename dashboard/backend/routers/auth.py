"""Auth router — register, login, me endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from ..services.auth_service import AuthService, AuthError
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Service singleton ──────────────────────────────────────────────
_service: AuthService | None = None


def init_service(db_path: str, secret_key: str, token_expiry: int = 1440):
    global _service
    _service = AuthService(db_path, secret_key, token_expiry)


def get_service() -> AuthService:
    if _service is None:
        raise RuntimeError("AuthService not initialized")
    return _service


# ── Request/Response models ────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    tier: str = "pro"  # Open beta: all new users get Pro


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/register")
async def register(body: RegisterRequest):
    """Register a new user account. Open beta: defaults to Pro tier."""
    svc = get_service()
    try:
        # Force pro tier during open beta regardless of what client sends
        result = svc.register(body.email, body.password, "pro")
        return result
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/login")
async def login(body: LoginRequest):
    """Login and receive JWT token."""
    svc = get_service()
    try:
        result = svc.login(body.email, body.password)
        return result
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """Change password for authenticated user."""
    svc = get_service()
    try:
        svc.change_password(user["id"], body.current_password, body.new_password)
        return {"status": "ok", "message": "Password changed successfully"}
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return {"user": user}
