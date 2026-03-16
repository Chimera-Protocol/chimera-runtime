"""
License Key Router — Issue signed JWT license keys for the SDK.

Pro and Enterprise users can generate license keys for the
chimera-compliance Python package. The key unlocks tier-gated features.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..middleware.auth import get_current_user, require_tier

router = APIRouter(prefix="/api/v1/license", tags=["license"])


class LicenseKeyResponse(BaseModel):
    key: str
    tier: str
    email: str
    message: str


@router.post(
    "/generate-sdk-key",
    response_model=LicenseKeyResponse,
    dependencies=[Depends(require_tier("pro"))],
)
async def generate_sdk_key(
    user: dict = Depends(get_current_user),
):
    """Generate a signed JWT license key for the chimera-compliance SDK.

    The key is valid for 1 year and can be used with:
      - Environment variable: CHIMERA_LICENSE_KEY=<key>
      - CLI: chimera-compliance license activate <key>
      - Python: chimera_compliance.activate_license("<key>")
    """
    from ..services.license_service import generate_license_key

    try:
        key = generate_license_key(
            user_id=user["id"],
            email=user["email"],
            tier=user["tier"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return LicenseKeyResponse(
        key=key,
        tier=user["tier"],
        email=user["email"],
        message=(
            f"License key generated for {user['tier'].upper()} tier. "
            f"Activate with: chimera-compliance license activate <key>"
        ),
    )
