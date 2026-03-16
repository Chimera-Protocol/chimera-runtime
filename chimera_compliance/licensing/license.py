"""
chimera-compliance -- License Manager

Validates signed JWT license keys for tier-gated features.
Keys are issued by the Chimera dashboard (compliance.chimera-protocol.com).

License resolution order:
  1. Programmatic: chimera_compliance.activate_license("chm_lic_...")
  2. Environment:  CHIMERA_LICENSE_KEY=chm_lic_...
  3. Config file:  .chimera/license.key
  4. Global file:  ~/.chimera/license.key
  5. Default:      FREE tier (no key needed)

The package ships with the Ed25519 public key for offline verification.
The private key never leaves the dashboard server.
"""

from __future__ import annotations

import functools
import os
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .keys import CHIMERA_PUBLIC_KEY


# ---------------------------------------------------------------------------
# Tier enum
# ---------------------------------------------------------------------------

class LicenseTier(IntEnum):
    """Tier levels as integers for easy comparison."""
    FREE = 0
    PRO = 1
    ENTERPRISE = 2

    @classmethod
    def from_str(cls, s: str) -> "LicenseTier":
        return cls[s.upper()]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LicenseError(Exception):
    """Raised when a license key is invalid, expired, or missing crypto deps."""
    pass


class TierUpgradeRequired(LicenseError):
    """Raised when a feature requires a higher tier than the active license."""

    def __init__(self, feature: str, required_tier: str, current_tier: str):
        self.feature = feature
        self.required_tier = required_tier
        self.current_tier = current_tier
        super().__init__(
            f"Feature '{feature}' requires {required_tier.upper()} tier "
            f"(current: {current_tier}). "
            f"Upgrade at https://compliance.chimera-protocol.com/settings"
        )


# ---------------------------------------------------------------------------
# License dataclass
# ---------------------------------------------------------------------------

@dataclass
class ChimeraLicense:
    """Validated license state."""
    tier: LicenseTier = LicenseTier.FREE
    email: str = ""
    org: str = ""
    features: List[str] = field(default_factory=list)
    expires_at: float = 0.0   # Unix timestamp; 0 = never (free)
    raw_token: str = ""

    @property
    def is_expired(self) -> bool:
        if self.tier == LicenseTier.FREE:
            return False
        return time.time() > self.expires_at

    @property
    def is_pro_or_above(self) -> bool:
        return self.tier >= LicenseTier.PRO and not self.is_expired

    @property
    def is_enterprise(self) -> bool:
        return self.tier >= LicenseTier.ENTERPRISE and not self.is_expired

    def has_feature(self, feature: str) -> bool:
        """Check if a specific feature flag is granted."""
        if self.is_expired:
            return False
        return "all" in self.features or feature in self.features

    @property
    def tier_name(self) -> str:
        return self.tier.name.lower()


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_license_lock = threading.Lock()
_active_license: Optional[ChimeraLicense] = None


def get_license() -> ChimeraLicense:
    """Get the active license, resolving lazily on first call."""
    global _active_license
    if _active_license is None:
        with _license_lock:
            if _active_license is None:
                _active_license = _resolve_license()
    return _active_license


def activate_license(key: str) -> ChimeraLicense:
    """Programmatically activate a license key.

    Usage::

        import chimera_compliance
        chimera_compliance.activate_license("chm_lic_eyJ...")
    """
    global _active_license
    with _license_lock:
        _active_license = _validate_key(key)
    return _active_license


def reset_license() -> None:
    """Reset the cached license (useful for testing)."""
    global _active_license
    with _license_lock:
        _active_license = None


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def _resolve_license() -> ChimeraLicense:
    """Resolve license from env / file / default."""

    # 0. Testing / development override (no JWT validation)
    #    Set CHIMERA_LICENSE_TIER=enterprise to bypass key validation in tests.
    tier_override = os.environ.get("CHIMERA_LICENSE_TIER", "").strip().lower()
    if tier_override in ("pro", "enterprise"):
        return ChimeraLicense(
            tier=LicenseTier.from_str(tier_override),
            email="dev@chimera.local",
            features=["all"],
            expires_at=time.time() + 365 * 86400,  # 1 year from now
        )

    # 1. Environment variable
    env_key = os.environ.get("CHIMERA_LICENSE_KEY", "").strip()
    if env_key:
        try:
            return _validate_key(env_key)
        except LicenseError:
            pass

    # 2. Local config file
    for path in [
        Path(".chimera") / "license.key",
        Path.home() / ".chimera" / "license.key",
    ]:
        if path.exists():
            try:
                key = path.read_text(encoding="utf-8").strip()
                if key:
                    return _validate_key(key)
            except (OSError, LicenseError):
                pass

    # 3. Default: FREE
    return ChimeraLicense()


# ---------------------------------------------------------------------------
# JWT validation
# ---------------------------------------------------------------------------

def _validate_key(raw_key: str) -> ChimeraLicense:
    """Validate a license key (Ed25519-signed JWT) using the embedded public key."""
    try:
        import jwt  # PyJWT
    except ImportError:
        raise LicenseError(
            "PyJWT with Ed25519 support is required for license validation. "
            "Install with: pip install 'chimera-compliance[pro]'"
        )

    try:
        payload: Dict[str, Any] = jwt.decode(
            raw_key,
            CHIMERA_PUBLIC_KEY,
            algorithms=["EdDSA"],
            audience="chimera-sdk",
            issuer="chimera-compliance",
        )
    except jwt.ExpiredSignatureError:
        raise LicenseError(
            "License key has expired. "
            "Renew at https://compliance.chimera-protocol.com/settings"
        )
    except jwt.InvalidTokenError as exc:
        raise LicenseError(f"Invalid license key: {exc}")

    tier_str = payload.get("tier", "free")
    return ChimeraLicense(
        tier=LicenseTier.from_str(tier_str),
        email=payload.get("email", ""),
        org=payload.get("org", ""),
        features=payload.get("features", []),
        expires_at=float(payload.get("exp", 0)),
        raw_token=raw_key,
    )


# ---------------------------------------------------------------------------
# Decorator / guard API
# ---------------------------------------------------------------------------

def require_tier(min_tier: str, feature_name: str = ""):
    """Decorator that gates a function behind a minimum tier.

    Usage::

        @require_tier("pro", feature_name="halt/resume")
        def halt(self):
            ...

        @require_tier("enterprise", feature_name="Annex IV generation")
        def generate(self):
            ...
    """
    min_level = LicenseTier.from_str(min_tier)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            lic = get_license()
            if lic.is_expired:
                raise TierUpgradeRequired(
                    feature=feature_name or func.__name__,
                    required_tier=min_tier,
                    current_tier="expired",
                )
            if lic.tier < min_level:
                raise TierUpgradeRequired(
                    feature=feature_name or func.__name__,
                    required_tier=min_tier,
                    current_tier=lic.tier_name,
                )
            return func(*args, **kwargs)

        # Metadata for introspection
        wrapper._chimera_min_tier = min_tier  # type: ignore[attr-defined]
        wrapper._chimera_feature = feature_name  # type: ignore[attr-defined]
        return wrapper

    return decorator


def check_tier(min_tier: str) -> bool:
    """Non-throwing tier check. Returns True if current license meets minimum."""
    lic = get_license()
    if lic.is_expired:
        return False
    return lic.tier >= LicenseTier.from_str(min_tier)
