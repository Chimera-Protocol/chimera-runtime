"""
chimera-compliance — Data Models

Every dataclass here maps 1:1 to the technical specification.
DecisionAuditRecord is the atomic unit of the Decision Audit Pipeline (spec §2.1).
DecisionResult is the public return type from ChimeraAgent.decide().

Design principles:
  - Zero external dependencies (stdlib only)
  - Full serialization: to_dict() / from_dict() on every model
  - Immutable after construction where possible
  - Type-safe: every field has an explicit type
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class DecisionResultType(str, Enum):
    """Possible outcomes of a decision."""
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    HUMAN_OVERRIDE = "HUMAN_OVERRIDE"
    INTERRUPTED = "INTERRUPTED"


class AttemptOutcome(str, Enum):
    """Outcome of a single attempt round."""
    ALL_PASSED = "ALL_PASSED"
    PARTIAL = "PARTIAL"
    ALL_BLOCKED = "ALL_BLOCKED"


class EnforcementType(str, Enum):
    """Enforcement mode for the audit record."""
    ACTIVE = "ACTIVE"
    DRY_RUN = "DRY_RUN"


# ============================================================================
# CONFIG MODELS
# ============================================================================

@dataclass
class LLMConfig:
    """LLM provider configuration (spec §3.2 — llm section)."""
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_retries: int = 3
    candidates_per_attempt: int = 3
    api_key: Optional[str] = None  # Can also come from env var

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_retries": self.max_retries,
            "candidates_per_attempt": self.candidates_per_attempt,
        }
        # Never serialize api_key to disk
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> LLMConfig:
        return cls(
            provider=d.get("provider", "openai"),
            model=d.get("model", "gpt-4o"),
            temperature=float(d.get("temperature", 0.7)),
            max_retries=int(d.get("max_retries", 3)),
            candidates_per_attempt=int(d.get("candidates_per_attempt", 3)),
            api_key=d.get("api_key"),
        )


@dataclass
class PolicyConfig:
    """Policy configuration (spec §3.2 — policy section)."""
    file: str = "./policies/governance.csl"
    auto_verify: bool = True  # Z3 verification on startup

    def to_dict(self) -> Dict[str, Any]:
        return {"file": self.file, "auto_verify": self.auto_verify}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PolicyConfig:
        return cls(
            file=d.get("file", "./policies/governance.csl"),
            auto_verify=d.get("auto_verify", True),
        )


@dataclass
class AuditConfig:
    """Audit pipeline configuration (spec §3.2 — audit section)."""
    enabled: bool = True
    output_dir: str = "./audit_logs"
    format: str = "json"  # json | compact | both
    html_reports: bool = True
    retention_days: int = 180  # EU AI Act Art.19 minimum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "output_dir": self.output_dir,
            "format": self.format,
            "html_reports": self.html_reports,
            "retention_days": self.retention_days,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AuditConfig:
        return cls(
            enabled=d.get("enabled", True),
            output_dir=d.get("output_dir", "./audit_logs"),
            format=d.get("format", "json"),
            html_reports=d.get("html_reports", True),
            retention_days=int(d.get("retention_days", 180)),
        )


@dataclass
class OversightConfig:
    """Human oversight configuration (spec §3.2 — oversight section, Art. 14)."""
    require_confirmation: bool = False
    allow_override: bool = True
    policy_hot_reload: bool = True
    stop_on_consecutive_blocks: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "require_confirmation": self.require_confirmation,
            "allow_override": self.allow_override,
            "policy_hot_reload": self.policy_hot_reload,
            "stop_on_consecutive_blocks": self.stop_on_consecutive_blocks,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> OversightConfig:
        return cls(
            require_confirmation=d.get("require_confirmation", False),
            allow_override=d.get("allow_override", True),
            policy_hot_reload=d.get("policy_hot_reload", True),
            stop_on_consecutive_blocks=int(d.get("stop_on_consecutive_blocks", 5)),
        )


@dataclass
class CausalConfig:
    """Causal engine configuration (spec §3.2 — causal section, Tier 2 optional)."""
    enabled: bool = False
    model_path: Optional[str] = None
    training_data: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"enabled": self.enabled}
        if self.model_path:
            d["model_path"] = self.model_path
        if self.training_data:
            d["training_data"] = self.training_data
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CausalConfig:
        return cls(
            enabled=d.get("enabled", False),
            model_path=d.get("model_path"),
            training_data=d.get("training_data"),
        )


@dataclass
class AgentMetaConfig:
    """Top-level agent identity (spec §3.2 — agent section)."""
    name: str = "chimera-compliance"
    version: str = "0.1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "version": self.version}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AgentMetaConfig:
        return cls(
            name=d.get("name", "chimera-compliance"),
            version=d.get("version", "0.1.0"),
        )


@dataclass
class AgentConfig:
    """
    Complete agent configuration — maps to .chimera/config.yaml (spec §3.2).
    This is the single source of truth for all agent settings.
    """
    agent: AgentMetaConfig = field(default_factory=AgentMetaConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    oversight: OversightConfig = field(default_factory=OversightConfig)
    causal: CausalConfig = field(default_factory=CausalConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent.to_dict(),
            "llm": self.llm.to_dict(),
            "policy": self.policy.to_dict(),
            "audit": self.audit.to_dict(),
            "oversight": self.oversight.to_dict(),
            "causal": self.causal.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AgentConfig:
        return cls(
            agent=AgentMetaConfig.from_dict(d.get("agent", {})),
            llm=LLMConfig.from_dict(d.get("llm", {})),
            policy=PolicyConfig.from_dict(d.get("policy", {})),
            audit=AuditConfig.from_dict(d.get("audit", {})),
            oversight=OversightConfig.from_dict(d.get("oversight", {})),
            causal=CausalConfig.from_dict(d.get("causal", {})),
        )


# ============================================================================
# DECISION PIPELINE MODELS — spec §2.1
# ============================================================================

@dataclass
class Violation:
    """
    A single policy violation (spec §2.1 — policy_evaluation.violations[]).
    Maps to the violation object inside each candidate's evaluation.
    """
    constraint: str                    # Constraint name from .csl
    rule: str                          # Human-readable rule text
    trigger_values: Dict[str, Any]     # Variable values that triggered the violation
    explanation: str                   # Plain-language explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint": self.constraint,
            "rule": self.rule,
            "trigger_values": self.trigger_values,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Violation:
        return cls(
            constraint=d["constraint"],
            rule=d.get("rule", ""),
            trigger_values=d.get("trigger_values", {}),
            explanation=d.get("explanation", ""),
        )


@dataclass
class PolicyEvaluation:
    """
    Result of evaluating a single candidate against CSL policy (spec §2.1).
    Wraps csl-core's GuardResult with additional metadata.
    """
    policy_file: str                            # Path to .csl file used
    policy_hash: str                            # SHA256 of policy file content
    result: str                                 # "ALLOWED" or "BLOCKED"
    duration_ms: float                          # Policy evaluation time
    violations: List[Violation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_file": self.policy_file,
            "policy_hash": self.policy_hash,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "violations": [v.to_dict() for v in self.violations],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PolicyEvaluation:
        return cls(
            policy_file=d["policy_file"],
            policy_hash=d["policy_hash"],
            result=d["result"],
            duration_ms=float(d["duration_ms"]),
            violations=[Violation.from_dict(v) for v in d.get("violations", [])],
        )


@dataclass
class Candidate:
    """
    A single strategy candidate generated by the LLM (spec §2.1 — reasoning.attempts[].candidates[]).
    """
    candidate_id: str                                    # "cand_001", "cand_002", ...
    strategy: str                                        # Human-readable strategy description
    llm_reasoning: str                                   # LLM's reasoning for this candidate
    llm_confidence: float                                # LLM's self-reported confidence [0, 1]
    parameters: Dict[str, Any]                           # Structured parameters for policy eval
    policy_evaluation: Optional[PolicyEvaluation] = None # Filled after CSL evaluation

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "strategy": self.strategy,
            "llm_reasoning": self.llm_reasoning,
            "llm_confidence": self.llm_confidence,
            "parameters": self.parameters,
        }
        if self.policy_evaluation is not None:
            d["policy_evaluation"] = self.policy_evaluation.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Candidate:
        pe = d.get("policy_evaluation")
        return cls(
            candidate_id=d["candidate_id"],
            strategy=d["strategy"],
            llm_reasoning=d.get("llm_reasoning", ""),
            llm_confidence=float(d.get("llm_confidence", 0.0)),
            parameters=d.get("parameters", {}),
            policy_evaluation=PolicyEvaluation.from_dict(pe) if pe else None,
        )


@dataclass
class Attempt:
    """
    A single attempt round in the retry loop (spec §2.1 — reasoning.attempts[]).
    Contains all candidates generated in this round and the round outcome.
    """
    attempt_number: int
    candidates: List[Candidate]
    outcome: str                  # "ALL_PASSED", "PARTIAL", "ALL_BLOCKED"
    note: str = ""                # Optional explanation of round outcome

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "candidates": [c.to_dict() for c in self.candidates],
            "outcome": self.outcome,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Attempt:
        return cls(
            attempt_number=int(d["attempt_number"]),
            candidates=[Candidate.from_dict(c) for c in d.get("candidates", [])],
            outcome=d["outcome"],
            note=d.get("note", ""),
        )


@dataclass
class AgentInfo:
    """
    Agent identity and configuration snapshot at decision time (spec §2.1 — agent).
    Captured per-decision so audit records are self-contained.
    """
    name: str
    version: str
    csl_core_version: str
    model: str
    model_provider: str
    temperature: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "csl_core_version": self.csl_core_version,
            "model": self.model,
            "model_provider": self.model_provider,
            "temperature": self.temperature,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AgentInfo:
        return cls(
            name=d["name"],
            version=d["version"],
            csl_core_version=d.get("csl_core_version", "unknown"),
            model=d["model"],
            model_provider=d["model_provider"],
            temperature=float(d.get("temperature", 0.0)),
        )


@dataclass
class InputInfo:
    """
    Captured input for a decision (spec §2.1 — input).
    """
    raw_request: str                              # Original natural language request
    structured_params: Dict[str, Any] = field(default_factory=dict)  # Parsed parameters
    context: Dict[str, Any] = field(default_factory=dict)            # Session/env context

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_request": self.raw_request,
            "structured_params": self.structured_params,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> InputInfo:
        return cls(
            raw_request=d["raw_request"],
            structured_params=d.get("structured_params", {}),
            context=d.get("context", {}),
        )


@dataclass
class ReasoningTrace:
    """
    Complete reasoning trace across all attempts (spec §2.1 — reasoning).
    """
    total_candidates: int
    total_attempts: int
    attempts: List[Attempt]
    selected_candidate: Optional[str] = None   # candidate_id of the selected candidate
    selection_reasoning: str = ""               # Why this candidate was chosen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_candidates": self.total_candidates,
            "total_attempts": self.total_attempts,
            "attempts": [a.to_dict() for a in self.attempts],
            "selected_candidate": self.selected_candidate,
            "selection_reasoning": self.selection_reasoning,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ReasoningTrace:
        return cls(
            total_candidates=int(d["total_candidates"]),
            total_attempts=int(d["total_attempts"]),
            attempts=[Attempt.from_dict(a) for a in d.get("attempts", [])],
            selected_candidate=d.get("selected_candidate"),
            selection_reasoning=d.get("selection_reasoning", ""),
        )


@dataclass
class DecisionInfo:
    """
    The final decision taken (spec §2.1 — decision).
    """
    action_taken: str                           # e.g. "INCREASE_BUDGET"
    result: str                                 # "ALLOWED", "BLOCKED", "HUMAN_OVERRIDE", "INTERRUPTED"
    final_parameters: Dict[str, Any]            # Parameters of the executed action
    policy_file: str                            # Policy that governed this decision
    policy_hash: str                            # Hash at decision time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_taken": self.action_taken,
            "result": self.result,
            "final_parameters": self.final_parameters,
            "policy_file": self.policy_file,
            "policy_hash": self.policy_hash,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DecisionInfo:
        return cls(
            action_taken=d["action_taken"],
            result=d["result"],
            final_parameters=d.get("final_parameters", {}),
            policy_file=d["policy_file"],
            policy_hash=d["policy_hash"],
        )


@dataclass
class ComplianceInfo:
    """
    EU AI Act compliance metadata per decision (spec §2.1 — compliance).
    """
    eu_ai_act: Dict[str, bool] = field(default_factory=lambda: {
        "article_12_record_keeping": True,
        "article_13_transparency": True,
        "article_14_human_oversight": True,
        "article_15_adversarial_resilience": True,
        "article_19_auto_logs": True,
        "article_86_right_to_explanation": True,
    })
    formal_verification: Dict[str, Any] = field(default_factory=lambda: {
        "policy_verified": True,
        "verification_engine": "Z3",
        "verification_result": "SAT",
    })
    human_oversight: Dict[str, bool] = field(default_factory=lambda: {
        "override_available": True,
        "stop_mechanism": True,
        "policy_human_editable": True,
    })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eu_ai_act": self.eu_ai_act,
            "formal_verification": self.formal_verification,
            "human_oversight": self.human_oversight,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ComplianceInfo:
        return cls(
            eu_ai_act=d.get("eu_ai_act", {}),
            formal_verification=d.get("formal_verification", {}),
            human_oversight=d.get("human_oversight", {}),
        )


@dataclass
class PerformanceInfo:
    """
    Performance metrics for a single decision (spec §2.1 — performance).
    """
    total_duration_ms: float = 0.0
    llm_duration_ms: float = 0.0
    policy_evaluation_ms: float = 0.0
    audit_generation_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_duration_ms": self.total_duration_ms,
            "llm_duration_ms": self.llm_duration_ms,
            "policy_evaluation_ms": self.policy_evaluation_ms,
            "audit_generation_ms": self.audit_generation_ms,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PerformanceInfo:
        return cls(
            total_duration_ms=float(d.get("total_duration_ms", 0.0)),
            llm_duration_ms=float(d.get("llm_duration_ms", 0.0)),
            policy_evaluation_ms=float(d.get("policy_evaluation_ms", 0.0)),
            audit_generation_ms=float(d.get("audit_generation_ms", 0.0)),
        )


@dataclass
class HumanOversightRecord:
    """
    Record of a human oversight action (override, confirmation, stop).
    Attached to DecisionAuditRecord when human intervenes.
    """
    action: str                     # "CONFIRM", "OVERRIDE", "STOP"
    reason: str = ""                # Human's stated reason
    override_decision: str = ""     # If override: what the human decided (e.g. "BLOCK")
    timestamp: str = ""             # When the human acted

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = _utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "action": self.action,
            "timestamp": self.timestamp,
        }
        if self.reason:
            d["reason"] = self.reason
        if self.override_decision:
            d["override_decision"] = self.override_decision
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> HumanOversightRecord:
        return cls(
            action=d["action"],
            reason=d.get("reason", ""),
            override_decision=d.get("override_decision", ""),
            timestamp=d.get("timestamp", _utc_now_iso()),
        )


# ============================================================================
# DECISION AUDIT RECORD — The Atomic Unit (spec §2.1)
# ============================================================================

SCHEMA_VERSION = "1.0.0"


@dataclass
class DecisionAuditRecord:
    """
    The complete, immutable audit record for a single agent decision.
    This is the atomic unit of the Decision Audit Pipeline.

    Maps 1:1 to spec §2.1 Full Schema. Every field name matches the spec JSON.
    Once written to disk, this record is never modified.

    Compliance:
      - Art. 12(1): Automatic recording of events
      - Art. 12(2a): Risk identification via violations
      - Art. 13(1): Transparency via reasoning trace
      - Art. 19(1): Log retention (handled by storage layer)
      - Art. 86(1): Right to explanation via reasoning + decision
    """
    # Identity
    schema_version: str
    decision_id: str
    timestamp: str

    # Sections (spec §2.1)
    agent: AgentInfo
    input: InputInfo
    reasoning: ReasoningTrace
    decision: DecisionInfo
    compliance: ComplianceInfo
    performance: PerformanceInfo

    # Optional: human oversight record (only if human intervened)
    human_oversight_record: Optional[HumanOversightRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to spec-compliant JSON-ready dict."""
        d: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "agent": self.agent.to_dict(),
            "input": self.input.to_dict(),
            "reasoning": self.reasoning.to_dict(),
            "decision": self.decision.to_dict(),
            "compliance": self.compliance.to_dict(),
            "performance": self.performance.to_dict(),
        }
        if self.human_oversight_record is not None:
            d["human_oversight_record"] = self.human_oversight_record.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to formatted JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_compact(self) -> Dict[str, Any]:
        """
        Compact format for high-throughput systems (spec §2.3).
        Drops reasoning chain, keeps essentials.
        """
        total_candidates = self.reasoning.total_candidates
        candidates_passed = sum(
            1 for attempt in self.reasoning.attempts
            for c in attempt.candidates
            if c.policy_evaluation and c.policy_evaluation.result == "ALLOWED"
        )
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "result": self.decision.result,
            "action": self.decision.action_taken,
            "policy": self.decision.policy_file,
            "policy_hash": self.decision.policy_hash,
            "violations": [
                v.to_dict()
                for attempt in self.reasoning.attempts
                for c in attempt.candidates
                if c.policy_evaluation
                for v in c.policy_evaluation.violations
            ] if self.decision.result == "BLOCKED" else [],
            "attempts": self.reasoning.total_attempts,
            "candidates_total": total_candidates,
            "candidates_passed": candidates_passed,
            "selected": self.reasoning.selected_candidate,
            "duration_ms": self.performance.total_duration_ms,
        }

    def to_compact_json(self) -> str:
        """Compact format as JSON string (single line, no indent)."""
        return json.dumps(self.to_compact(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DecisionAuditRecord:
        """Deserialize from JSON-ready dict."""
        hor = d.get("human_oversight_record")
        return cls(
            schema_version=d["schema_version"],
            decision_id=d["decision_id"],
            timestamp=d["timestamp"],
            agent=AgentInfo.from_dict(d["agent"]),
            input=InputInfo.from_dict(d["input"]),
            reasoning=ReasoningTrace.from_dict(d["reasoning"]),
            decision=DecisionInfo.from_dict(d["decision"]),
            compliance=ComplianceInfo.from_dict(d["compliance"]),
            performance=PerformanceInfo.from_dict(d["performance"]),
            human_oversight_record=HumanOversightRecord.from_dict(hor) if hor else None,
        )

    @classmethod
    def from_json(cls, json_str: str) -> DecisionAuditRecord:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


# ============================================================================
# DECISION RESULT — Public Return Type
# ============================================================================

@dataclass
class DecisionResult:
    """
    Public return type from ChimeraAgent.decide().
    Provides clean access to the decision outcome while carrying
    the full audit record for inspection or persistence.

    Usage:
        result = agent.decide("Increase marketing spend by 40%")
        result.result       # "ALLOWED"
        result.action       # "INCREASE_BUDGET"
        result.explanation  # Human-readable explanation
        result.parameters   # Final action parameters
        result.audit        # Full DecisionAuditRecord
    """
    result: str                                # "ALLOWED", "BLOCKED", "HUMAN_OVERRIDE", "INTERRUPTED"
    action: str                                # Action taken (e.g. "INCREASE_BUDGET")
    explanation: str                           # Human-readable selection reasoning
    parameters: Dict[str, Any]                 # Final parameters of the action
    audit: DecisionAuditRecord                 # Full audit record

    @property
    def allowed(self) -> bool:
        """Convenience: was the action allowed?"""
        return self.result == DecisionResultType.ALLOWED.value

    @property
    def blocked(self) -> bool:
        """Convenience: was the action blocked?"""
        return self.result == DecisionResultType.BLOCKED.value

    @property
    def decision_id(self) -> str:
        """Convenience: get the decision ID from the audit record."""
        return self.audit.decision_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result,
            "action": self.action,
            "explanation": self.explanation,
            "parameters": self.parameters,
            "audit": self.audit.to_dict(),
        }


# ============================================================================
# HELPERS
# ============================================================================

def _utc_now_iso() -> str:
    """Generate ISO 8601 UTC timestamp with millisecond precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def generate_decision_id() -> str:
    """Generate a unique decision ID in spec format: dec_<uuid>."""
    return f"dec_{uuid.uuid4().hex[:20]}"


def generate_candidate_id(index: int) -> str:
    """Generate a candidate ID: cand_001, cand_002, ..."""
    return f"cand_{index:03d}"


def utc_now_iso() -> str:
    """Public timestamp helper — ISO 8601 UTC with millisecond precision."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
