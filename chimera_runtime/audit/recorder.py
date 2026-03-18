"""
chimera-runtime — Audit Recorder

Builds a complete DecisionAuditRecord from agent state.
Standalone builder for external callers and for reconstructing
records from stored components.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import (
    AgentInfo,
    Attempt,
    ComplianceInfo,
    DecisionAuditRecord,
    DecisionInfo,
    HumanOversightRecord,
    InputInfo,
    PerformanceInfo,
    ReasoningTrace,
    generate_decision_id,
    utc_now_iso,
    SCHEMA_VERSION,
)


def build_audit_record(
    *,
    agent_info: AgentInfo,
    input_info: InputInfo,
    attempts: List[Attempt],
    action_taken: str,
    result: str,
    final_parameters: Dict[str, Any],
    policy_file: str,
    policy_hash: str,
    selected_candidate_id: Optional[str] = None,
    selection_reasoning: str = "",
    total_duration_ms: float = 0.0,
    llm_duration_ms: float = 0.0,
    policy_evaluation_ms: float = 0.0,
    audit_generation_ms: float = 0.0,
    human_oversight_record: Optional[HumanOversightRecord] = None,
    decision_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> DecisionAuditRecord:
    """
    Build a complete DecisionAuditRecord from individual components.

    All fields map 1:1 to spec §2.1.

    Returns:
        Complete, immutable DecisionAuditRecord ready for storage.
    """
    total_candidates = sum(len(a.candidates) for a in attempts)

    reasoning = ReasoningTrace(
        total_candidates=total_candidates,
        total_attempts=len(attempts),
        attempts=attempts,
        selected_candidate=selected_candidate_id,
        selection_reasoning=selection_reasoning,
    )

    decision = DecisionInfo(
        action_taken=action_taken,
        result=result,
        final_parameters=final_parameters,
        policy_file=policy_file,
        policy_hash=policy_hash,
    )

    performance = PerformanceInfo(
        total_duration_ms=round(total_duration_ms, 3),
        llm_duration_ms=round(llm_duration_ms, 3),
        policy_evaluation_ms=round(policy_evaluation_ms, 3),
        audit_generation_ms=round(audit_generation_ms, 3),
    )

    return DecisionAuditRecord(
        schema_version=SCHEMA_VERSION,
        decision_id=decision_id or generate_decision_id(),
        timestamp=timestamp or utc_now_iso(),
        agent=agent_info,
        input=input_info,
        reasoning=reasoning,
        decision=decision,
        compliance=ComplianceInfo(),
        performance=performance,
        human_oversight_record=human_oversight_record,
    )
