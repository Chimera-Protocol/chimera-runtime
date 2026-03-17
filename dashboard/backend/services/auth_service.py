"""Authentication service — JWT token management + user operations."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt

from ..models.user import (
    UserDB,
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    update_password,
    verify_password,
)


class AuthError(Exception):
    """Authentication error."""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    """JWT-based authentication service."""

    def __init__(self, db_path: str, secret_key: str, token_expiry_minutes: int = 1440):
        self.db_path = db_path
        self.secret_key = secret_key
        self.token_expiry_minutes = token_expiry_minutes

    def register(self, email: str, password: str, tier: str = "free") -> dict:
        """Register a new user and return access token + user."""
        if not email or not password:
            raise AuthError("Email and password are required", 400)
        if len(password) < 6:
            raise AuthError("Password must be at least 6 characters", 400)
        if tier not in ("free", "pro", "enterprise"):
            raise AuthError("Invalid tier", 400)

        try:
            user = create_user(self.db_path, email, password, tier)
        except ValueError as e:
            raise AuthError(str(e), 409)

        token = self._create_token(user)
        return {"access_token": token, "token_type": "bearer", "user": user.to_public()}

    def login(self, email: str, password: str) -> dict:
        """Authenticate user and return access token."""
        if not email or not password:
            raise AuthError("Email and password are required", 400)

        user = get_user_by_email(self.db_path, email)
        if user is None:
            raise AuthError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")

        update_last_login(self.db_path, user.id)
        token = self._create_token(user)
        return {"access_token": token, "token_type": "bearer", "user": user.to_public()}

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        """Change user's password after verifying current password."""
        if not current_password or not new_password:
            raise AuthError("Current and new passwords are required", 400)
        if len(new_password) < 6:
            raise AuthError("New password must be at least 6 characters", 400)

        user = get_user_by_id(self.db_path, user_id)
        if user is None:
            raise AuthError("User not found")

        if not verify_password(current_password, user.password_hash):
            raise AuthError("Current password is incorrect")

        update_password(self.db_path, user_id, new_password)

    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token")

    def get_current_user(self, token: str) -> dict:
        """Get user from token. Returns public user dict."""
        payload = self.verify_token(token)
        user = get_user_by_id(self.db_path, payload["user_id"])
        if user is None:
            raise AuthError("User not found")
        return user.to_public()

    def _create_token(self, user: UserDB) -> str:
        """Create JWT token for user."""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "tier": user.tier,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.token_expiry_minutes),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
