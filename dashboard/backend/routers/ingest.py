"""
Ingest API Router — /api/v1/ingest

Receives audit records from CLI/SDK via API key authentication.
Pro+ tier only — free tier users get 403.
Each ingest costs 1 credit from user's wallet.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..models.api_key import verify_api_key
from ..models.user import get_user_by_id
from ..models.wallet import check_balance, deduct, get_or_create_wallet, CREDIT_COSTS
from ..services.storage_service import StorageBackend

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Module-level state
_storage: Optional[StorageBackend] = None
_db_path: Optional[str] = None

# Rate limiting: {user_id: (window_start, count)}
_rate_limits: Dict[int, tuple] = defaultdict(lambda: (0.0, 0))

# Tier rate limits (per hour)
RATE_LIMITS = {
    "pro": 10_000,
    "enterprise": 1_000_000,  # effectively unlimited
}


def init_service(storage: StorageBackend, db_path: str) -> None:
    global _storage, _db_path
    _storage = storage
    _db_path = db_path


def _get_storage() -> StorageBackend:
    if _storage is None:
        raise HTTPException(500, "Ingest service not initialized")
    return _storage


def _authenticate_api_key(request: Request) -> dict:
    """Extract and validate API key from X-API-Key header. Returns user dict."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(401, "X-API-Key header required")

    if _db_path is None:
        raise HTTPException(500, "Ingest service not initialized")

    user_id = verify_api_key(_db_path, api_key)
    if user_id is None:
        raise HTTPException(401, "Invalid or revoked API key")

    user = get_user_by_id(_db_path, user_id)
    if user is None:
        raise HTTPException(401, "User not found")

    # Free tier cannot use cloud sync
    if user.tier == "free":
        raise HTTPException(
            403,
            "Cloud sync requires Pro tier or above. Upgrade at runtime.chimera-protocol.com",
        )

    return {"id": user_id, "tier": user.tier}


def _check_balance(user_id: int, tier: str, operation: str = "ingest") -> None:
    """Check if user has enough credits. Raises 402 if insufficient."""
    if _db_path is None:
        return

    can_afford, balance_dollars, cost_dollars = check_balance(_db_path, user_id, tier, operation)
    if not can_afford:
        # Show credits to user, not dollars
        credit_cost = CREDIT_COSTS.get(operation, 1)
        raise HTTPException(
            402,
            {
                "error": "Insufficient credits",
                "message": f"You don't have enough credits for this operation ({credit_cost} credits required). "
                           f"Contact research@chimera-protocol.com for additional credits.",
            },
        )


def _check_rate_limit(user_id: int, tier: str, count: int = 1) -> None:
    """Check and enforce rate limits."""
    max_per_hour = RATE_LIMITS.get(tier, 0)
    if max_per_hour == 0:
        raise HTTPException(403, "Rate limit not configured for tier")

    now = time.time()
    window_start, current_count = _rate_limits[user_id]

    # Reset window if more than 1 hour has passed
    if now - window_start > 3600:
        _rate_limits[user_id] = (now, count)
        return

    if current_count + count > max_per_hour:
        raise HTTPException(
            429,
            f"Rate limit exceeded. {tier} tier allows {max_per_hour} ingests/hour.",
        )

    _rate_limits[user_id] = (window_start, current_count + count)


def _validate_record(record: dict) -> None:
    """Lightweight validation of audit record structure."""
    required = ["decision_id", "timestamp", "agent", "decision"]
    missing = [f for f in required if f not in record]
    if missing:
        raise HTTPException(
            422,
            f"Missing required fields: {', '.join(missing)}",
        )

    decision_id = record.get("decision_id", "")
    if not isinstance(decision_id, str) or not decision_id.startswith("dec_"):
        raise HTTPException(422, "decision_id must start with 'dec_'")

    result = record.get("decision", {}).get("result", "")
    valid_results = {"ALLOWED", "BLOCKED", "HUMAN_OVERRIDE", "INTERRUPTED"}
    if result and result not in valid_results:
        raise HTTPException(422, f"Invalid decision.result: {result}. Must be one of: {valid_results}")


# ========================================================================
# ENDPOINTS
# ========================================================================


class IngestResponse(BaseModel):
    status: str = "ok"
    decision_id: str
    storage_key: str
    credits_remaining: int = 0


class BatchIngestResponse(BaseModel):
    ingested: int
    errors: List[Dict[str, Any]]
    credits_remaining: int = 0


@router.post("/", response_model=IngestResponse, status_code=201)
async def ingest_record(request: Request):
    """Ingest a single audit record. Requires Pro+ API key. Costs $0.001."""
    user = _authenticate_api_key(request)
    _check_rate_limit(user["id"], user["tier"])
    _check_balance(user["id"], user["tier"], "ingest")

    body = await request.json()
    _validate_record(body)

    storage = _get_storage()
    storage_key = storage.save(user["id"], body)

    # Deduct cost
    result = deduct(
        _db_path, user["id"], operation="ingest", count=1,
        description=f"Audit ingest: {body['decision_id']}",
        decision_id=body.get("decision_id"),
    )

    return IngestResponse(
        decision_id=body["decision_id"],
        storage_key=storage_key,
        credits_remaining=result["remaining_ingests"],
    )


@router.post("/batch", response_model=BatchIngestResponse, status_code=201)
async def ingest_batch(request: Request):
    """Ingest multiple audit records (max 50). Requires Pro+ API key. Costs $0.001 per record."""
    user = _authenticate_api_key(request)

    body = await request.json()
    records = body.get("records", [])

    if len(records) > 50:
        raise HTTPException(422, "Maximum 50 records per batch request")

    _check_rate_limit(user["id"], user["tier"], count=len(records))
    _check_balance(user["id"], user["tier"], "ingest")

    storage = _get_storage()
    ingested = 0
    errors = []

    for i, record in enumerate(records):
        try:
            _validate_record(record)
            storage.save(user["id"], record)
            ingested += 1
        except HTTPException as e:
            errors.append({"index": i, "error": e.detail})
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    # Deduct cost for successfully ingested records
    result = {"new_balance": 0.0, "remaining_ingests": 0}
    if ingested > 0:
        result = deduct(
            _db_path, user["id"], operation="ingest_batch", count=ingested,
            description=f"Batch ingest: {ingested} records",
        )

    return BatchIngestResponse(
        ingested=ingested,
        errors=errors,
        credits_remaining=result["remaining_ingests"],
    )
