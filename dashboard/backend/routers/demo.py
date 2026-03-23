"""
Demo Data API Router — /api/v1/demo

Generates realistic demo audit records and policies for new users
so the dashboard has meaningful data to display immediately.
"""

from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..middleware.auth import get_current_user
from ..services.storage_service import StorageBackend

router = APIRouter(prefix="/demo", tags=["demo"])

# Module-level service references — initialized in main.py lifespan
_storage: Optional[StorageBackend] = None
_db_path: Optional[str] = None
_policies_dir: Optional[str] = None


def init_service(storage: StorageBackend, db_path: str, policies_dir: str) -> None:
    global _storage, _db_path, _policies_dir
    _storage = storage
    _db_path = db_path
    _policies_dir = policies_dir


# ========================================================================
# DEMO DATA DEFINITIONS
# ========================================================================

_AGENTS = [
    {"name": "finance-bot", "version": "2.1.0", "model": "gpt-4o", "provider": "openai", "temp": 0.3},
    {"name": "hr-assistant", "version": "1.4.2", "model": "gpt-4o-mini", "provider": "openai", "temp": 0.5},
    {"name": "marketing-agent", "version": "3.0.1", "model": "claude-sonnet-4-20250514", "provider": "anthropic", "temp": 0.7},
    {"name": "ops-controller", "version": "1.8.0", "model": "gpt-4o", "provider": "openai", "temp": 0.2},
]

_SCENARIOS = [
    # (action, raw_request, params, result, violations, agent_index)
    {
        "action": "APPROVE_BUDGET",
        "request": "Approve Q2 marketing budget increase of $45,000 for digital campaigns",
        "params": {"amount": 45000, "role": "MANAGER", "channel": "DIGITAL", "department": "MARKETING", "urgency": "MEDIUM", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 2,
    },
    {
        "action": "TRANSFER_FUNDS",
        "request": "Transfer $320,000 to vendor account for Q3 infrastructure upgrade",
        "params": {"amount": 320000, "role": "DIRECTOR", "channel": "ALL", "department": "ENGINEERING", "urgency": "HIGH", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 0,
    },
    {
        "action": "APPROVE_BUDGET",
        "request": "Approve $500,000 TV advertising spend for product launch",
        "params": {"amount": 500000, "role": "MANAGER", "channel": "TV", "department": "MARKETING", "urgency": "HIGH", "is_weekend": "NO"},
        "result": "BLOCKED",
        "violations": [
            {"constraint": "manager_approval_limit", "rule": "WHEN role == MANAGER THEN amount <= 250000", "trigger_values": {"role": "MANAGER", "amount": 500000}, "explanation": "Manager role cannot approve amounts exceeding $250,000. This request for $500,000 requires Director-level or above approval."},
            {"constraint": "single_channel_cap", "rule": "WHEN channel != ALL THEN amount <= 300000", "trigger_values": {"channel": "TV", "amount": 500000}, "explanation": "Single channel spend is capped at $300,000. The TV channel allocation of $500,000 exceeds this limit."},
        ],
        "agent_idx": 2,
    },
    {
        "action": "HIRE_CONTRACTOR",
        "request": "Approve hiring of senior DevOps contractor at $180/hr for 6 months",
        "params": {"amount": 187200, "role": "DIRECTOR", "channel": "ALL", "department": "ENGINEERING", "urgency": "MEDIUM", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 1,
    },
    {
        "action": "APPROVE_BUDGET",
        "request": "Weekend emergency: approve $75,000 for server migration",
        "params": {"amount": 75000, "role": "VP", "channel": "ALL", "department": "OPERATIONS", "urgency": "MEDIUM", "is_weekend": "YES"},
        "result": "BLOCKED",
        "violations": [
            {"constraint": "weekend_freeze", "rule": "WHEN is_weekend == YES THEN urgency == CRITICAL", "trigger_values": {"is_weekend": "YES", "urgency": "MEDIUM"}, "explanation": "Budget changes on weekends require CRITICAL urgency level. This request has MEDIUM urgency."},
        ],
        "agent_idx": 3,
    },
    {
        "action": "LAUNCH_CAMPAIGN",
        "request": "Launch multi-channel holiday campaign across digital and print",
        "params": {"amount": 220000, "role": "DIRECTOR", "channel": "ALL", "department": "MARKETING", "urgency": "HIGH", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 2,
    },
    {
        "action": "APPROVE_RAISE",
        "request": "Approve 15% salary increase for lead engineer retention",
        "params": {"amount": 28500, "role": "DIRECTOR", "channel": "ALL", "department": "HR", "urgency": "HIGH", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 1,
    },
    {
        "action": "TRANSFER_FUNDS",
        "request": "Transfer $850,000 to overseas subsidiary for expansion",
        "params": {"amount": 850000, "role": "VP", "channel": "ALL", "department": "FINANCE", "urgency": "HIGH", "is_weekend": "NO"},
        "result": "BLOCKED",
        "violations": [
            {"constraint": "vp_approval_limit", "rule": "WHEN role == VP THEN amount <= 750000", "trigger_values": {"role": "VP", "amount": 850000}, "explanation": "VP role is limited to approving amounts up to $750,000. This $850,000 transfer requires CEO-level authorization."},
        ],
        "agent_idx": 0,
    },
    {
        "action": "APPROVE_BUDGET",
        "request": "Approve $12,000 for team offsite event catering",
        "params": {"amount": 12000, "role": "MANAGER", "channel": "ALL", "department": "HR", "urgency": "LOW", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 1,
    },
    {
        "action": "APPROVE_BUDGET",
        "request": "Analyst requesting $5,000 for research tools subscription",
        "params": {"amount": 5000, "role": "ANALYST", "channel": "DIGITAL", "department": "ENGINEERING", "urgency": "LOW", "is_weekend": "NO"},
        "result": "BLOCKED",
        "violations": [
            {"constraint": "analyst_no_spend", "rule": "WHEN role == ANALYST THEN amount <= 0", "trigger_values": {"role": "ANALYST", "amount": 5000}, "explanation": "Analysts cannot approve any spending. This request must be escalated to a Manager or above."},
        ],
        "agent_idx": 3,
    },
    {
        "action": "LAUNCH_CAMPAIGN",
        "request": "Launch targeted radio campaign for midwest market expansion",
        "params": {"amount": 95000, "role": "MANAGER", "channel": "RADIO", "department": "MARKETING", "urgency": "MEDIUM", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 2,
    },
    {
        "action": "APPROVE_BUDGET",
        "request": "Emergency weekend infrastructure scaling - critical outage",
        "params": {"amount": 150000, "role": "VP", "channel": "ALL", "department": "OPERATIONS", "urgency": "CRITICAL", "is_weekend": "YES"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 3,
    },
    {
        "action": "TRANSFER_FUNDS",
        "request": "Process quarterly vendor payments batch - 12 vendors",
        "params": {"amount": 340000, "role": "DIRECTOR", "channel": "ALL", "department": "FINANCE", "urgency": "MEDIUM", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 0,
    },
    {
        "action": "APPROVE_BUDGET",
        "request": "Approve $380,000 print advertising for annual report distribution",
        "params": {"amount": 380000, "role": "DIRECTOR", "channel": "PRINT", "department": "MARKETING", "urgency": "MEDIUM", "is_weekend": "NO"},
        "result": "BLOCKED",
        "violations": [
            {"constraint": "single_channel_cap", "rule": "WHEN channel != ALL THEN amount <= 300000", "trigger_values": {"channel": "PRINT", "amount": 380000}, "explanation": "Single channel budget capped at $300,000. Print allocation of $380,000 exceeds the per-channel limit."},
        ],
        "agent_idx": 2,
    },
    {
        "action": "HIRE_CONTRACTOR",
        "request": "Fast-track hiring of 3 security consultants for compliance audit",
        "params": {"amount": 135000, "role": "MANAGER", "channel": "ALL", "department": "OPERATIONS", "urgency": "HIGH", "is_weekend": "NO"},
        "result": "ALLOWED",
        "violations": [],
        "agent_idx": 1,
    },
]

_DEMO_FINANCE_CSL = """\
CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN FinanceGuard {
  VARIABLES {
    amount: 0..5000000
    role: {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CFO"}
    transfer_type: {"INTERNAL", "EXTERNAL", "INTERNATIONAL"}
    requires_dual_approval: {"YES", "NO"}
    risk_level: {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
  }

  // Analysts cannot initiate any transfers
  STATE_CONSTRAINT analyst_no_transfers {
    WHEN role == "ANALYST"
    THEN amount <= 0
  }

  // Managers limited to $100,000 for external transfers
  STATE_CONSTRAINT manager_external_limit {
    WHEN role == "MANAGER" AND transfer_type == "EXTERNAL"
    THEN amount <= 100000
  }

  // International transfers require Director or above
  STATE_CONSTRAINT international_director_required {
    WHEN transfer_type == "INTERNATIONAL" AND role == "MANAGER"
    THEN amount <= 0
  }

  // High-risk transfers above $500,000 need dual approval
  STATE_CONSTRAINT high_value_dual_approval {
    WHEN amount > 500000 AND risk_level == "HIGH"
    THEN requires_dual_approval == "YES"
  }

  // Absolute ceiling per transaction
  STATE_CONSTRAINT transaction_ceiling {
    ALWAYS True
    THEN amount <= 5000000
  }
}
"""


# ========================================================================
# RECORD GENERATION
# ========================================================================

def _generate_decision_id() -> str:
    return f"dec_{uuid.uuid4().hex[:20]}"


def _generate_demo_records(count: int = 15) -> list[dict]:
    """Generate realistic DecisionAuditRecord dicts."""
    now = datetime.now(timezone.utc)
    records = []

    for i, scenario in enumerate(_SCENARIOS[:count]):
        # Spread timestamps over the last 7 days
        hours_ago = random.uniform(0.5, 168)  # 0.5h to 7 days
        ts = now - timedelta(hours=hours_ago)
        timestamp = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"

        agent_def = _AGENTS[scenario["agent_idx"]]
        decision_id = _generate_decision_id()

        # Performance metrics — realistic spread
        policy_eval_ms = round(random.uniform(8, 45), 1)
        llm_ms = round(random.uniform(120, 650), 1)
        audit_ms = round(random.uniform(2, 15), 1)
        total_ms = round(policy_eval_ms + llm_ms + audit_ms + random.uniform(5, 90), 1)

        # Build candidates
        is_blocked = scenario["result"] == "BLOCKED"
        policy_hash = uuid.uuid4().hex[:16]

        selected_id = "cand_001"
        candidates = []
        num_candidates = random.randint(2, 3)

        for c_idx in range(num_candidates):
            cand_id = f"cand_{c_idx + 1:03d}"
            cand_params = dict(scenario["params"])

            if c_idx > 0 and is_blocked:
                # Subsequent candidates try adjusted values
                cand_params = dict(scenario["params"])
                if "amount" in cand_params:
                    cand_params["amount"] = int(cand_params["amount"] * 0.6)

            cand_result = scenario["result"] if c_idx == 0 else ("ALLOWED" if c_idx > 0 and is_blocked else scenario["result"])
            cand_violations = scenario["violations"] if c_idx == 0 else []

            if c_idx > 0 and is_blocked:
                cand_result = "ALLOWED"
                cand_violations = []
                selected_id = cand_id

            candidates.append({
                "candidate_id": cand_id,
                "strategy": f"Strategy {c_idx + 1}: {scenario['action'].replace('_', ' ').title()} with {'original' if c_idx == 0 else 'adjusted'} parameters",
                "llm_reasoning": f"Evaluating {'original request' if c_idx == 0 else 'modified approach with reduced scope'} against governance policy constraints.",
                "llm_confidence": round(random.uniform(0.65, 0.95), 2),
                "parameters": cand_params,
                "policy_evaluation": {
                    "policy_file": "policies/governance.csl",
                    "policy_hash": policy_hash,
                    "result": cand_result,
                    "duration_ms": round(random.uniform(5, 25), 1),
                    "violations": cand_violations,
                },
            })

        # For allowed scenarios, first candidate is selected
        if not is_blocked:
            selected_id = "cand_001"

        record = {
            "schema_version": "1.0.0",
            "decision_id": decision_id,
            "timestamp": timestamp,
            "agent": {
                "name": agent_def["name"],
                "version": agent_def["version"],
                "csl_core_version": "0.4.0",
                "model": agent_def["model"],
                "model_provider": agent_def["provider"],
                "temperature": agent_def["temp"],
            },
            "input": {
                "raw_request": scenario["request"],
                "structured_params": scenario["params"],
                "context": {
                    "session_id": f"sess_{uuid.uuid4().hex[:12]}",
                    "source": "dashboard-demo",
                },
            },
            "reasoning": {
                "total_candidates": num_candidates,
                "total_attempts": 1 if not is_blocked else 2,
                "attempts": [
                    {
                        "attempt_number": 1,
                        "candidates": candidates[:1] if is_blocked else candidates,
                        "outcome": "ALL_BLOCKED" if is_blocked else "ALL_PASSED",
                        "note": "Initial evaluation" if not is_blocked else "First attempt blocked — policy violations detected",
                    },
                ] + ([
                    {
                        "attempt_number": 2,
                        "candidates": candidates[1:],
                        "outcome": "PARTIAL",
                        "note": "Retry with adjusted parameters — found compliant alternative",
                    },
                ] if is_blocked else []),
                "selected_candidate": selected_id,
                "selection_reasoning": f"Selected {selected_id} as the {'compliant alternative after initial block' if is_blocked else 'best strategy meeting all policy constraints'}.",
            },
            "decision": {
                "action_taken": scenario["action"],
                "result": scenario["result"],
                "final_parameters": scenario["params"] if not is_blocked else candidates[-1]["parameters"],
                "policy_file": "policies/governance.csl",
                "policy_hash": policy_hash,
            },
            "compliance": {
                "eu_ai_act": {
                    "article_12_record_keeping": True,
                    "article_13_transparency": True,
                    "article_14_human_oversight": True,
                    "article_15_adversarial_resilience": True,
                    "article_19_auto_logs": True,
                    "article_86_right_to_explanation": True,
                },
                "formal_verification": {
                    "policy_verified": True,
                    "verification_engine": "Z3",
                    "verification_result": "SAT",
                },
                "human_oversight": {
                    "override_available": True,
                    "stop_mechanism": True,
                    "policy_human_editable": True,
                },
            },
            "performance": {
                "total_duration_ms": total_ms,
                "llm_duration_ms": llm_ms,
                "policy_evaluation_ms": policy_eval_ms,
                "audit_generation_ms": audit_ms,
            },
        }

        records.append(record)

    return records


# ========================================================================
# ENDPOINTS
# ========================================================================


@router.post("/load")
async def load_demo_data(user: dict = Depends(get_current_user)):
    """Load demo data (audit records + policies) for the current user."""
    if _storage is None or _policies_dir is None:
        raise HTTPException(500, "Demo service not initialized")

    user_id = user["id"]

    # Generate and save demo audit records
    records = _generate_demo_records(15)
    for rec in records:
        _storage.save(user_id, rec)

    # Write demo finance policy to user's policy directory
    policies_created = 0
    policies_path = Path(_policies_dir)
    user_policies_path = policies_path / str(user_id)
    user_policies_path.mkdir(parents=True, exist_ok=True)

    demo_policy_path = user_policies_path / "demo_finance.csl"
    if not demo_policy_path.exists():
        demo_policy_path.write_text(_DEMO_FINANCE_CSL)
        policies_created += 1

    # Global governance.csl is always visible to all users
    if (policies_path / "governance.csl").exists():
        policies_created += 1

    return {
        "status": "ok",
        "records_created": len(records),
        "policies_created": policies_created,
    }


@router.post("/reset")
async def reset_demo_data(user: dict = Depends(get_current_user)):
    """Delete all demo data for the current user and reload fresh."""
    if _storage is None or _policies_dir is None:
        raise HTTPException(500, "Demo service not initialized")

    user_id = user["id"]

    # Count and clear existing records
    existing = _storage.list_records(user_id)
    records_cleared = len(existing)

    for rec in existing:
        decision_id = rec.get("decision_id", "")
        if decision_id:
            _storage.delete(user_id, decision_id)

    return {
        "status": "ok",
        "records_cleared": records_cleared,
        "records_created": 0,
    }


@router.get("/status")
async def demo_status(user: dict = Depends(get_current_user)):
    """Check if the current user has demo data loaded."""
    if _storage is None:
        raise HTTPException(500, "Demo service not initialized")

    user_id = user["id"]
    records = _storage.list_records(user_id)

    return {
        "has_demo_data": len(records) > 0,
        "record_count": len(records),
    }
