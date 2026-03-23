"""
Wallet API Router — /api/v1/wallet

Dollar-based balance, transaction history, and usage stats.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..middleware.auth import get_current_user
from ..models.wallet import (
    get_or_create_wallet,
    get_transactions,
    add_funds,
    TIER_BUDGET_CENTS,
    OPERATION_COST_CENTS,
    CREDIT_COSTS,
    TIER_CREDITS,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])

_db_path: Optional[str] = None


def init_service(db_path: str) -> None:
    global _db_path
    _db_path = db_path


# ========================================================================
# ENDPOINTS
# ========================================================================


@router.get("")
async def get_wallet(user: dict = Depends(get_current_user)):
    """Get current balance and usage stats."""
    if _db_path is None:
        raise HTTPException(500, "Wallet service not initialized")

    wallet = get_or_create_wallet(_db_path, user["id"], user.get("tier", "free"))
    tier = user.get("tier", "free")

    return {
        **wallet.to_dict(),
        "tier": tier,
        "tier_allocation": TIER_CREDITS.get(tier, 1000),
        "costs": CREDIT_COSTS,
        "need_more": "Contact research@chimera-protocol.com for additional credits.",
    }


@router.get("/transactions")
async def get_transaction_history(
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """Get recent transactions."""
    if _db_path is None:
        raise HTTPException(500, "Wallet service not initialized")

    txns = get_transactions(_db_path, user["id"], limit=limit)
    return {"transactions": txns, "total": len(txns)}


@router.post("/topup")
async def admin_topup(
    target_user_id: int,
    amount: float,
    reason: str = "manual_topup",
    user: dict = Depends(get_current_user),
):
    """Admin-only: Add funds to a user's wallet. Amount in USD."""
    if _db_path is None:
        raise HTTPException(500, "Wallet service not initialized")

    # Only enterprise tier can top up others
    if user.get("tier") != "enterprise" and user["id"] != target_user_id:
        raise HTTPException(403, "Only enterprise admins can top up other users")

    if amount <= 0 or amount > 100:
        raise HTTPException(422, "Amount must be between $0.01 and $100.00")

    try:
        new_balance = add_funds(_db_path, target_user_id, amount, reason=reason)
        return {
            "status": "ok",
            "user_id": target_user_id,
            "added": f"${amount:.2f}",
            "new_balance": f"${new_balance:.4f}",
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
