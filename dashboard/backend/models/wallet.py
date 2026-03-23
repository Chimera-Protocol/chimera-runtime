"""
Wallet — Dollar-based usage metering for Chimera Runtime.

Each user gets a USD spending allowance. Every operation costs real money
from the platform's pocket. Balances stored as CENTS (integer) for precision.

User-facing: CREDITS (abstract units)
Internal math: DOLLARS (hidden from user)

Tier budgets:
  - free:       1,000 credits   (internal: $1.00)
  - pro:        3,000 credits   (internal: $3.00)
  - enterprise: 5,000 credits   (internal: $5.00, not active yet)

Per-operation costs:
  - ingest:     1 credit   (internal: $0.001)
  - export:     5 credits  (internal: $0.005)
  - policy_pull: 0 credits (free)

When credits hit 0 → 402 "Contact research@chimera-protocol.com"
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

from .user import _get_conn


# ── Tier Budget (in CENTS) ───────────────────────────────────────

TIER_BUDGET_CENTS = {
    "free": 100,         # $1.00
    "pro": 300,          # $3.00
    "enterprise": 500,   # $5.00
}

# Operation costs (in CENTS — use floats for sub-cent precision)
# Stored as float cents: 0.1 = $0.001
OPERATION_COST_CENTS = {
    "ingest": 0.1,         # $0.001 per audit record
    "ingest_batch": 0.1,   # $0.001 per record in batch
    "export": 0.5,         # $0.005 per export
    "policy_pull": 0.0,    # Free
}

# ── User-Facing: Credits ─────────────────────────────────────────
# 1 credit = 1 ingest = $0.001

TIER_CREDITS = {
    "free": 1_000,        # $1.00 ÷ $0.001
    "pro": 3_000,         # $3.00 ÷ $0.001
    "enterprise": 5_000,  # $5.00 ÷ $0.001
}

CREDIT_COSTS = {
    "ingest": 1,           # 1 credit per audit record
    "ingest_batch": 1,     # 1 credit per record
    "export": 5,           # 5 credits per export
    "policy_pull": 0,      # Free
}


def _cents_to_dollars(cents: float) -> str:
    """Format cents as dollar string."""
    return f"${cents / 100:.2f}"


def _cost_display(operation: str) -> str:
    """Human-readable cost for an operation."""
    cost = OPERATION_COST_CENTS.get(operation, 0)
    if cost == 0:
        return "free"
    return f"${cost / 100:.4f}"


# ── Data Models ──────────────────────────────────────────────────

@dataclass
class Wallet:
    id: int
    user_id: int
    balance_cents: int       # Current balance in cents (×100 for sub-cent: stored as cents×100)
    total_loaded_cents: int  # Lifetime dollars loaded
    total_spent_cents: int   # Lifetime dollars spent
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        budget = self.total_loaded_cents
        # Convert internal units to user-facing credits
        # 1 credit = 1 ingest = $0.001 = 0.1 cents = 10 internal units
        units_per_credit = _to_units(OPERATION_COST_CENTS["ingest"]) if OPERATION_COST_CENTS["ingest"] > 0 else 1
        balance_credits = int(self.balance_cents / units_per_credit) if units_per_credit > 0 else 0
        total_credits = int(self.total_loaded_cents / units_per_credit) if units_per_credit > 0 else 0
        spent_credits = int(self.total_spent_cents / units_per_credit) if units_per_credit > 0 else 0

        return {
            "credits": balance_credits,
            "total_credits": total_credits,
            "spent_credits": spent_credits,
            "usage_percent": round(
                (self.total_spent_cents / budget * 100) if budget > 0 else 0, 1
            ),
            "remaining_ingests": balance_credits,  # 1 credit = 1 ingest
        }


# ── SQL ──────────────────────────────────────────────────────────
# balance_cents stores cents × 100 for sub-cent precision (1 unit = 0.01 cent)
# So $1.00 = 10000 units, $0.001 = 10 units

_PRECISION = 100  # Internal units per cent (so 1 cent = 100 units)

_CREATE_WALLETS_SQL = """
CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    balance_cents INTEGER NOT NULL DEFAULT 0,
    total_loaded_cents INTEGER NOT NULL DEFAULT 0,
    total_spent_cents INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

_CREATE_TRANSACTIONS_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL,
    operation TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    decision_id TEXT,
    balance_after_cents INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def create_wallet_tables(db_path: str) -> None:
    """Create wallets and transactions tables."""
    conn = _get_conn(db_path)
    conn.execute(_CREATE_WALLETS_SQL)
    conn.execute(_CREATE_TRANSACTIONS_SQL)
    conn.commit()


# ── Wallet Operations ────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_units(cents: float) -> int:
    """Convert cents (float) to internal precision units."""
    return int(cents * _PRECISION)


def _units_to_cents(units: int) -> float:
    """Convert internal units back to cents."""
    return units / _PRECISION


def get_or_create_wallet(db_path: str, user_id: int, tier: str = "free") -> Wallet:
    """Get user's wallet, creating one with tier budget if it doesn't exist."""
    conn = _get_conn(db_path)
    row = conn.execute("SELECT * FROM wallets WHERE user_id = ?", (user_id,)).fetchone()

    if row is not None:
        return Wallet(**dict(row))

    # Create new wallet with tier budget
    now = _now()
    budget_cents = TIER_BUDGET_CENTS.get(tier, 100)  # Default $1
    budget_units = _to_units(budget_cents)

    cursor = conn.execute(
        """INSERT INTO wallets (user_id, balance_cents, total_loaded_cents, total_spent_cents, created_at, updated_at)
           VALUES (?, ?, ?, 0, ?, ?)""",
        (user_id, budget_units, budget_units, now, now),
    )
    conn.commit()

    # Record initial load
    _record_transaction(
        db_path, user_id, budget_units, "initial_budget",
        f"Welcome budget: {_cents_to_dollars(budget_cents)} ({tier} tier)",
        balance_after=budget_units,
    )

    return Wallet(
        id=cursor.lastrowid,
        user_id=user_id,
        balance_cents=budget_units,
        total_loaded_cents=budget_units,
        total_spent_cents=0,
        created_at=now,
        updated_at=now,
    )


def check_balance(db_path: str, user_id: int, tier: str, operation: str = "ingest") -> tuple:
    """Check if user can afford an operation. Returns (can_afford, balance_dollars, cost_dollars)."""
    wallet = get_or_create_wallet(db_path, user_id, tier)
    cost_cents = OPERATION_COST_CENTS.get(operation, 0.1)
    cost_units = _to_units(cost_cents)
    can_afford = wallet.balance_cents >= cost_units
    return can_afford, _units_to_cents(wallet.balance_cents) / 100, cost_cents / 100


def deduct(
    db_path: str,
    user_id: int,
    operation: str,
    count: int = 1,
    description: str = "",
    decision_id: Optional[str] = None,
) -> dict:
    """Deduct cost for operation(s). Returns {new_balance, cost, remaining_ingests}.

    Raises ValueError if insufficient balance.
    """
    conn = _get_conn(db_path)
    cost_cents = OPERATION_COST_CENTS.get(operation, 0.1)
    total_cost_units = _to_units(cost_cents) * count

    # Atomic check + deduct
    row = conn.execute("SELECT balance_cents FROM wallets WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        raise ValueError("Wallet not found")

    current = row["balance_cents"]
    if current < total_cost_units:
        remaining_dollars = _units_to_cents(current) / 100
        cost_dollars = (cost_cents * count) / 100
        raise ValueError(
            f"Insufficient balance: ${remaining_dollars:.4f} remaining, "
            f"${cost_dollars:.4f} required. "
            f"Contact research@chimera-protocol.com for additional budget."
        )

    new_balance = current - total_cost_units
    conn.execute(
        "UPDATE wallets SET balance_cents = ?, total_spent_cents = total_spent_cents + ?, updated_at = ? WHERE user_id = ?",
        (new_balance, total_cost_units, _now(), user_id),
    )
    conn.commit()

    total_cost_dollars = (cost_cents * count) / 100
    desc = description or f"{operation} ×{count} (${total_cost_dollars:.4f})"
    _record_transaction(
        db_path, user_id, -total_cost_units, operation, desc,
        decision_id=decision_id, balance_after=new_balance,
    )

    return {
        "new_balance": round(_units_to_cents(new_balance) / 100, 4),
        "cost": round(total_cost_dollars, 4),
        "remaining_ingests": int(new_balance / _to_units(OPERATION_COST_CENTS["ingest"])) if OPERATION_COST_CENTS["ingest"] > 0 else 999999,
    }


def add_funds(
    db_path: str,
    user_id: int,
    dollars: float,
    reason: str = "manual_topup",
) -> float:
    """Add funds to wallet (admin/manual). Returns new balance in dollars."""
    conn = _get_conn(db_path)
    row = conn.execute("SELECT balance_cents FROM wallets WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        raise ValueError("Wallet not found")

    add_units = _to_units(dollars * 100)  # dollars → cents → units
    new_balance = row["balance_cents"] + add_units
    conn.execute(
        "UPDATE wallets SET balance_cents = ?, total_loaded_cents = total_loaded_cents + ?, updated_at = ? WHERE user_id = ?",
        (new_balance, add_units, _now(), user_id),
    )
    conn.commit()

    _record_transaction(
        db_path, user_id, add_units, reason,
        f"Top-up: +${dollars:.2f}", balance_after=new_balance,
    )
    return round(_units_to_cents(new_balance) / 100, 4)


def get_transactions(db_path: str, user_id: int, limit: int = 50) -> List[dict]:
    """Get recent transactions for a user."""
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        # Convert internal units to dollars for display
        d["amount_dollars"] = round(_units_to_cents(d["amount_cents"]) / 100, 4)
        d["balance_after_dollars"] = round(_units_to_cents(d["balance_after_cents"]) / 100, 4)
        result.append(d)
    return result


# ── Internal Helpers ─────────────────────────────────────────────

def _record_transaction(
    db_path: str,
    user_id: int,
    amount_units: int,
    operation: str,
    description: str,
    decision_id: Optional[str] = None,
    balance_after: int = 0,
) -> None:
    """Record a transaction in the ledger."""
    conn = _get_conn(db_path)
    conn.execute(
        """INSERT INTO transactions (user_id, amount_cents, operation, description, decision_id, balance_after_cents, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, amount_units, operation, description, decision_id, balance_after, _now()),
    )
    conn.commit()
