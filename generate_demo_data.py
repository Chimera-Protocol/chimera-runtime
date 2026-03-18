#!/usr/bin/env python3
"""
Generate realistic demo audit records for the Chimera Runtime Dashboard.

Usage:
    python3 generate_demo_data.py

Creates ~15 diverse decisions in audit_logs/ using the real
ChimeraAgent pipeline with a MockLLM.
"""

import json
import os
import sys
import random
from datetime import datetime, timezone, timedelta

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from chimera_runtime.llm.base import BaseLLMProvider
from chimera_runtime.policy import PolicyManager
from chimera_runtime.agent import ChimeraAgent
from chimera_runtime.oversight import HumanOversight


# ============================================================================
# MOCK LLM — returns canned responses per scenario
# ============================================================================

class DemoLLM(BaseLLMProvider):
    """Mock LLM that returns pre-built candidate responses."""

    def __init__(self, responses: list):
        super().__init__(model="gpt-4o-demo", api_key="demo")
        self._responses = responses
        self._idx = 0

    @property
    def provider_name(self) -> str:
        return "demo"

    def _call_llm(self, prompt: str) -> str:
        if self._idx < len(self._responses):
            resp = self._responses[self._idx]
            self._idx += 1
            return resp
        return self._responses[-1]


def make_response(candidates: list) -> str:
    """Build a JSON response string from candidate parameter dicts."""
    items = []
    for i, params in enumerate(candidates):
        items.append({
            "strategy": params.pop("_strategy", f"Strategy {i+1}"),
            "reasoning": params.pop("_reasoning", "Based on risk assessment and policy analysis."),
            "confidence": params.pop("_confidence", round(random.uniform(0.7, 0.95), 2)),
            "parameters": params,
        })
    return json.dumps(items)


# ============================================================================
# SCENARIOS
# ============================================================================

SCENARIOS = [
    # --- ALLOWED ---
    {
        "request": "Process payroll transfer of $45,000 for Q1 bonuses",
        "context": {"user_id": "usr_sarah_chen", "role": "MANAGER", "department": "HR", "session": "sess_001"},
        "response": make_response([
            {"_strategy": "Standard payroll transfer via ACH", "_reasoning": "Regular quarterly bonus disbursement within manager limits", "_confidence": 0.92,
             "amount": 45000, "role": "MANAGER", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
            {"_strategy": "Batch payroll with compliance check", "_confidence": 0.88,
             "amount": 45000, "role": "MANAGER", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
            {"_strategy": "Split into departmental sub-transfers", "_confidence": 0.75,
             "amount": 45000, "role": "MANAGER", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
        ]),
    },
    {
        "request": "View transaction history for account audit",
        "context": {"user_id": "usr_james_park", "role": "ANALYST", "department": "Compliance", "session": "sess_002"},
        "response": make_response([
            {"_strategy": "Read-only audit report generation", "_reasoning": "Analyst requesting standard view operation", "_confidence": 0.97,
             "amount": 0, "role": "ANALYST", "transaction_type": "VIEW", "is_weekend": "NO", "risk_level": "LOW", "destination": "INTERNAL"},
        ]),
    },
    {
        "request": "Approve vendor payment of $180,000 for cloud infrastructure",
        "context": {"user_id": "usr_michael_ross", "role": "DIRECTOR", "department": "Engineering", "session": "sess_003"},
        "response": make_response([
            {"_strategy": "Direct vendor payment via wire transfer", "_reasoning": "Director-level approval for infrastructure expense", "_confidence": 0.91,
             "amount": 180000, "role": "DIRECTOR", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "MEDIUM", "destination": "DOMESTIC"},
            {"_strategy": "PO-backed vendor payment", "_confidence": 0.85,
             "amount": 180000, "role": "DIRECTOR", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
        ]),
    },
    {
        "request": "Execute international wire of $620,000 to Singapore subsidiary",
        "context": {"user_id": "usr_elena_volkov", "role": "CFO", "department": "Finance", "session": "sess_004"},
        "response": make_response([
            {"_strategy": "SWIFT international wire transfer", "_reasoning": "CFO-authorized cross-border transfer to subsidiary", "_confidence": 0.93,
             "amount": 620000, "role": "CFO", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "HIGH", "destination": "INTERNATIONAL"},
            {"_strategy": "Multi-currency treasury transfer", "_confidence": 0.87,
             "amount": 620000, "role": "CFO", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "MEDIUM", "destination": "INTERNATIONAL"},
        ]),
    },
    {
        "request": "Process client refund of $12,500 for service disruption",
        "context": {"user_id": "usr_sarah_chen", "role": "MANAGER", "department": "Customer Success", "session": "sess_005"},
        "response": make_response([
            {"_strategy": "Standard refund via original payment method", "_reasoning": "Customer compensation within manager authority", "_confidence": 0.94,
             "amount": 12500, "role": "MANAGER", "transaction_type": "REFUND", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
        ]),
    },

    # --- BLOCKED ---
    {
        "request": "Transfer $350,000 to new supplier account urgently",
        "context": {"user_id": "usr_david_kim", "role": "MANAGER", "department": "Procurement", "session": "sess_006"},
        "response": make_response([
            {"_strategy": "Urgent wire transfer to new supplier", "_reasoning": "Time-sensitive supplier payment", "_confidence": 0.82,
             "amount": 350000, "role": "MANAGER", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "HIGH", "destination": "DOMESTIC"},
            {"_strategy": "Expedited ACH transfer", "_confidence": 0.78,
             "amount": 350000, "role": "MANAGER", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "HIGH", "destination": "DOMESTIC"},
            {"_strategy": "Split payment with interim approval", "_confidence": 0.65,
             "amount": 350000, "role": "MANAGER", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "MEDIUM", "destination": "DOMESTIC"},
        ]),
    },
    {
        "request": "Analyst requesting direct fund transfer for expense reimbursement",
        "context": {"user_id": "usr_lisa_wong", "role": "ANALYST", "department": "Operations", "session": "sess_007"},
        "response": make_response([
            {"_strategy": "Direct expense reimbursement transfer", "_reasoning": "Analyst attempting transfer operation", "_confidence": 0.72,
             "amount": 5000, "role": "ANALYST", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
            {"_strategy": "Petty cash disbursement", "_confidence": 0.68,
             "amount": 5000, "role": "ANALYST", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
        ]),
    },
    {
        "request": "Process weekend emergency payout of $75,000",
        "context": {"user_id": "usr_michael_ross", "role": "DIRECTOR", "department": "Operations", "session": "sess_008"},
        "response": make_response([
            {"_strategy": "Emergency weekend wire transfer", "_reasoning": "Operational emergency requiring immediate funds", "_confidence": 0.80,
             "amount": 75000, "role": "DIRECTOR", "transaction_type": "PAYOUT", "is_weekend": "YES", "risk_level": "MEDIUM", "destination": "DOMESTIC"},
            {"_strategy": "After-hours emergency disbursement", "_confidence": 0.73,
             "amount": 75000, "role": "DIRECTOR", "transaction_type": "PAYOUT", "is_weekend": "YES", "risk_level": "HIGH", "destination": "DOMESTIC"},
        ]),
    },
    {
        "request": "Authorize $2,500,000 acquisition payment",
        "context": {"user_id": "usr_elena_volkov", "role": "CFO", "department": "M&A", "session": "sess_009"},
        "response": make_response([
            {"_strategy": "Large-scale acquisition wire", "_reasoning": "M&A transaction exceeding policy ceiling", "_confidence": 0.88,
             "amount": 2500000, "role": "CFO", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "CRITICAL", "destination": "INTERNATIONAL"},
        ]),
    },
    {
        "request": "Transfer $150,000 to offshore account for tax optimization",
        "context": {"user_id": "usr_unknown", "role": "MANAGER", "department": "Finance", "session": "sess_010"},
        "response": make_response([
            {"_strategy": "International tax optimization transfer", "_reasoning": "Cross-border transfer to optimize tax structure", "_confidence": 0.65,
             "amount": 150000, "role": "MANAGER", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "HIGH", "destination": "INTERNATIONAL"},
        ]),
    },

    # --- MORE ALLOWED ---
    {
        "request": "Internal budget reallocation of $90,000 between departments",
        "context": {"user_id": "usr_michael_ross", "role": "DIRECTOR", "department": "Finance", "session": "sess_011"},
        "response": make_response([
            {"_strategy": "Inter-departmental budget transfer", "_reasoning": "Routine Q2 budget reallocation", "_confidence": 0.96,
             "amount": 90000, "role": "DIRECTOR", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "LOW", "destination": "INTERNAL"},
        ]),
    },
    {
        "request": "Generate compliance report for board meeting",
        "context": {"user_id": "usr_james_park", "role": "ANALYST", "department": "Compliance", "session": "sess_012"},
        "response": make_response([
            {"_strategy": "Board compliance report generation", "_reasoning": "Standard quarterly compliance reporting", "_confidence": 0.98,
             "amount": 0, "role": "ANALYST", "transaction_type": "VIEW", "is_weekend": "NO", "risk_level": "LOW", "destination": "INTERNAL"},
        ]),
    },
    {
        "request": "Approve $500,000 capital expenditure for new data center",
        "context": {"user_id": "usr_elena_volkov", "role": "CFO", "department": "IT", "session": "sess_013"},
        "response": make_response([
            {"_strategy": "Capital expenditure approval and wire", "_reasoning": "Strategic infrastructure investment within CFO authority", "_confidence": 0.94,
             "amount": 500000, "role": "CFO", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "MEDIUM", "destination": "DOMESTIC"},
        ]),
    },
    {
        "request": "Process quarterly dividend payout of $200,000",
        "context": {"user_id": "usr_michael_ross", "role": "DIRECTOR", "department": "Finance", "session": "sess_014"},
        "response": make_response([
            {"_strategy": "Scheduled dividend disbursement", "_reasoning": "Board-approved quarterly dividend to shareholders", "_confidence": 0.93,
             "amount": 200000, "role": "DIRECTOR", "transaction_type": "PAYOUT", "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"},
        ]),
    },
    {
        "request": "Emergency: Transfer $800,000 for regulatory fine payment",
        "context": {"user_id": "usr_elena_volkov", "role": "CFO", "department": "Legal", "session": "sess_015"},
        "response": make_response([
            {"_strategy": "Regulatory fine payment via certified wire", "_reasoning": "Urgent compliance-mandated payment to regulator", "_confidence": 0.91,
             "amount": 800000, "role": "CFO", "transaction_type": "TRANSFER", "is_weekend": "NO", "risk_level": "CRITICAL", "destination": "DOMESTIC"},
        ]),
    },
]


def main():
    policy_path = "./policies/governance.csl"
    audit_dir = "./audit_logs"

    if not os.path.exists(policy_path):
        print(f"Policy file not found: {policy_path}")
        sys.exit(1)

    print(f"\n  Chimera Runtime — Demo Data Generator")
    print(f"  Policy: {policy_path}")
    print(f"  Audit dir: {audit_dir}")
    print(f"  Scenarios: {len(SCENARIOS)}")
    print()

    # Spread timestamps across the last 7 days
    now = datetime.now(timezone.utc)

    for i, scenario in enumerate(SCENARIOS):
        # Create a unique LLM per scenario
        llm = DemoLLM(responses=[scenario["response"]])

        agent = ChimeraAgent(
            model="gpt-4o-demo",
            api_key="demo",
            policy=policy_path,
            llm_provider=llm,
            agent_name="chimera-runtime-guard",
            audit_dir=audit_dir,
            max_retries=1,
            candidates_per_attempt=3,
        )

        try:
            result = agent.decide(
                request=scenario["request"],
                context=scenario["context"],
            )

            status = "ALLOWED" if result.allowed else "BLOCKED"
            color = "\033[92m" if result.allowed else "\033[91m"
            reset = "\033[0m"

            violations = ""
            if result.audit and result.audit.reasoning:
                for attempt in result.audit.reasoning.attempts:
                    for c in attempt.candidates:
                        if c.policy_evaluation and c.policy_evaluation.violations:
                            vnames = [v.constraint for v in c.policy_evaluation.violations]
                            violations = f" [{', '.join(set(vnames))}]"

            print(f"  {i+1:2d}. {color}{status:8s}{reset}  {scenario['request'][:60]}{violations}")

        except Exception as e:
            print(f"  {i+1:2d}. \033[93mERROR\033[0m    {scenario['request'][:50]}  ({e})")

    # Count results
    from chimera_runtime.audit.query import AuditQuery
    query = AuditQuery(audit_dir)
    query.refresh()
    stats = query.stats()

    print(f"\n  Results:")
    print(f"    Total: {stats.total_decisions}")
    print(f"    Allowed: {stats.allowed_count}")
    print(f"    Blocked: {stats.blocked_count}")
    print(f"    Block rate: {stats.block_rate*100:.1f}%")
    print(f"    Violations: {stats.total_violations}")
    print()
    print(f"  Dashboard'u yenile: http://localhost:3000/dashboard")
    print()


if __name__ == "__main__":
    main()
