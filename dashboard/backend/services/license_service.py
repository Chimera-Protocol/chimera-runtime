"""
License Key Service — Generate signed JWT license keys for the SDK.

Uses Ed25519 asymmetric signing:
  - Private key: stays on this server (CHIMERA_LICENSE_PRIVATE_KEY env var)
  - Public key: embedded in the chimera-runtime PyPI package
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import jwt


# The Ed25519 private key (PEM). Set via environment variable.
# Docker .env files store \n as literal characters, so we replace them.
_PRIVATE_KEY = os.environ.get("CHIMERA_LICENSE_PRIVATE_KEY", "").strip().replace("\\n", "\n")

# Feature lists per tier
TIER_FEATURES: Dict[str, List[str]] = {
    "free": [],
    "pro": [
        "reasoning_traces",
        "halt_resume",
        "multi_policy",
        "hot_reload",
        "audit_export",
        "html_reports",
        "alerts",
        "api_keys",
    ],
    "enterprise": [
        "reasoning_traces",
        "halt_resume",
        "multi_policy",
        "hot_reload",
        "audit_export",
        "html_reports",
        "alerts",
        "api_keys",
        "annex_iv",
        "websocket",
        "sso_saml",
        "siem",
        "unlimited_retention",
        "causal_analysis",
        "white_label",
    ],
}


def generate_license_key(
    user_id: int,
    email: str,
    tier: str,
    org: str = "",
    validity_days: int = 365,
) -> str:
    """
    Generate a signed Ed25519 JWT license key for the chimera-runtime SDK.

    Args:
        user_id: User ID from dashboard
        email: User email
        tier: "pro" or "enterprise"
        org: Organization name (enterprise only)
        validity_days: Key validity in days (default: 1 year)

    Returns:
        Signed JWT string

    Raises:
        ValueError: If private key is not configured or tier is invalid
    """
    if not _PRIVATE_KEY:
        raise ValueError(
            "CHIMERA_LICENSE_PRIVATE_KEY not set. "
            "Generate with: openssl genpkey -algorithm Ed25519"
        )

    if tier not in ("pro", "enterprise"):
        raise ValueError(f"Cannot generate license for tier: {tier}")

    now = int(time.time())
    payload: Dict[str, Any] = {
        "sub": f"user_{user_id}",
        "email": email,
        "tier": tier,
        "org": org,
        "features": TIER_FEATURES.get(tier, []),
        "iat": now,
        "exp": now + (validity_days * 86400),
        "iss": "chimera-runtime",
        "aud": "chimera-sdk",
    }

    return jwt.encode(payload, _PRIVATE_KEY, algorithm="EdDSA")
