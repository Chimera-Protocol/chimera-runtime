"""
Tests for chimera_compliance.models

Validates:
  - Every dataclass has working to_dict() and from_dict()
  - Roundtrip serialization: obj → dict → obj produces identical results
  - DecisionAuditRecord matches spec §2.1 JSON schema
  - Compact format contains required fields
  - Helper functions generate correct IDs and timestamps
"""

import json
import re
from datetime import datetime, timezone

import pytest

from chimera_compliance.models import (
    # Config models
    AgentConfig,
    LLMConfig,
    PolicyConfig,
    AuditConfig,
    OversightConfig,
    CausalConfig,
    AgentMetaConfig,

    # Pipeline models
    Violation,
    PolicyEvaluation,
    Candidate,
    Attempt,
    AgentInfo,
    InputInfo,
    ReasoningTrace,
    DecisionInfo,
    ComplianceInfo,
    PerformanceInfo,
    HumanOversightRecord,
    DecisionAuditRecord,
    DecisionResult,

    # Enums
    DecisionResultType,
    AttemptOutcome,
    EnforcementType,

    # Helpers
    generate_decision_id,
    generate_candidate_id,
    utc_now_iso,
    SCHEMA_VERSION,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_violation():
    return Violation(
        constraint="manager_approval_limit",
        rule="Constraint 'manager_approval_limit' violated: amount 300000 > 250000",
        trigger_values={"amount": 300000, "role": "MANAGER"},
        explanation="Manager budget limit is $250,000. Requested: $300,000.",
    )


@pytest.fixture
def sample_policy_evaluation(sample_violation):
    return PolicyEvaluation(
        policy_file="./policies/governance.csl",
        policy_hash="sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        result="BLOCKED",
        duration_ms=0.723,
        violations=[sample_violation],
    )


@pytest.fixture
def sample_candidate_allowed():
    return Candidate(
        candidate_id="cand_001",
        strategy="Conservative budget increase within manager authority",
        llm_reasoning="Given the MANAGER role, cap at $200K to stay within limits.",
        llm_confidence=0.85,
        parameters={"amount": 200000, "role": "MANAGER", "channel": "DIGITAL"},
        policy_evaluation=PolicyEvaluation(
            policy_file="./policies/governance.csl",
            policy_hash="sha256:abc123",
            result="ALLOWED",
            duration_ms=0.42,
            violations=[],
        ),
    )


@pytest.fixture
def sample_candidate_blocked(sample_policy_evaluation):
    return Candidate(
        candidate_id="cand_002",
        strategy="Aggressive full-budget allocation",
        llm_reasoning="Maximize impact with $300K spend across all channels.",
        llm_confidence=0.72,
        parameters={"amount": 300000, "role": "MANAGER", "channel": "ALL"},
        policy_evaluation=sample_policy_evaluation,
    )


@pytest.fixture
def sample_attempt(sample_candidate_allowed, sample_candidate_blocked):
    return Attempt(
        attempt_number=1,
        candidates=[sample_candidate_allowed, sample_candidate_blocked],
        outcome="PARTIAL",
        note="1 of 2 candidates passed policy check",
    )


@pytest.fixture
def sample_audit_record(sample_attempt):
    return DecisionAuditRecord(
        schema_version=SCHEMA_VERSION,
        decision_id="dec_a1b2c3d4e5f6g7h8i9j0",
        timestamp="2026-02-25T14:32:07.841Z",
        agent=AgentInfo(
            name="chimera-compliance",
            version="0.1.0",
            csl_core_version="0.3.0",
            model="gpt-4o",
            model_provider="openai",
            temperature=0.7,
        ),
        input=InputInfo(
            raw_request="Increase marketing spend by 40% for Q3",
            structured_params={"target_increase": 0.4, "quarter": "Q3"},
            context={"session_id": "sess_001", "user_id": "usr_001", "environment": "production"},
        ),
        reasoning=ReasoningTrace(
            total_candidates=2,
            total_attempts=1,
            attempts=[sample_attempt],
            selected_candidate="cand_001",
            selection_reasoning="Selected conservative approach within MANAGER authority limits",
        ),
        decision=DecisionInfo(
            action_taken="INCREASE_BUDGET",
            result="ALLOWED",
            final_parameters={"amount": 200000, "role": "MANAGER", "channel": "DIGITAL"},
            policy_file="./policies/governance.csl",
            policy_hash="sha256:abc123",
        ),
        compliance=ComplianceInfo(),
        performance=PerformanceInfo(
            total_duration_ms=1247.3,
            llm_duration_ms=1200.0,
            policy_evaluation_ms=1.2,
            audit_generation_ms=46.1,
        ),
    )


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestHelpers:
    def test_generate_decision_id_format(self):
        did = generate_decision_id()
        assert did.startswith("dec_")
        assert len(did) == 24  # "dec_" + 20 hex chars

    def test_generate_decision_id_unique(self):
        ids = {generate_decision_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_candidate_id(self):
        assert generate_candidate_id(1) == "cand_001"
        assert generate_candidate_id(10) == "cand_010"
        assert generate_candidate_id(100) == "cand_100"

    def test_utc_now_iso_format(self):
        ts = utc_now_iso()
        # Must match: 2026-02-25T14:32:07.841Z
        pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z"
        assert re.match(pattern, ts), f"Timestamp {ts} doesn't match ISO 8601 format"

    def test_utc_now_iso_is_utc(self):
        ts = utc_now_iso()
        assert ts.endswith("Z")


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    def test_decision_result_type_values(self):
        assert DecisionResultType.ALLOWED.value == "ALLOWED"
        assert DecisionResultType.BLOCKED.value == "BLOCKED"
        assert DecisionResultType.HUMAN_OVERRIDE.value == "HUMAN_OVERRIDE"
        assert DecisionResultType.INTERRUPTED.value == "INTERRUPTED"

    def test_enum_is_string(self):
        assert DecisionResultType.ALLOWED == "ALLOWED"
        assert isinstance(DecisionResultType.ALLOWED, str)


# ============================================================================
# CONFIG MODEL TESTS
# ============================================================================

class TestConfigModels:
    def test_llm_config_defaults(self):
        cfg = LLMConfig()
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.7
        assert cfg.max_retries == 3
        assert cfg.candidates_per_attempt == 3
        assert cfg.api_key is None

    def test_llm_config_roundtrip(self):
        cfg = LLMConfig(provider="anthropic", model="claude-sonnet-4-20250514", temperature=0.5)
        d = cfg.to_dict()
        restored = LLMConfig.from_dict(d)
        assert restored.provider == "anthropic"
        assert restored.model == "claude-sonnet-4-20250514"
        assert restored.temperature == 0.5

    def test_llm_config_no_api_key_in_dict(self):
        cfg = LLMConfig(api_key="sk-secret-key")
        d = cfg.to_dict()
        assert "api_key" not in d

    def test_agent_config_full_roundtrip(self):
        cfg = AgentConfig(
            llm=LLMConfig(provider="anthropic", model="claude-sonnet-4-20250514"),
            policy=PolicyConfig(file="./my_policy.csl"),
            audit=AuditConfig(retention_days=365),
            oversight=OversightConfig(require_confirmation=True),
        )
        d = cfg.to_dict()
        restored = AgentConfig.from_dict(d)
        assert restored.llm.provider == "anthropic"
        assert restored.policy.file == "./my_policy.csl"
        assert restored.audit.retention_days == 365
        assert restored.oversight.require_confirmation is True

    def test_agent_config_defaults(self):
        cfg = AgentConfig()
        assert cfg.agent.name == "chimera-compliance"
        assert cfg.agent.version == "0.1.0"
        assert cfg.llm.provider == "openai"
        assert cfg.audit.retention_days == 180
        assert cfg.causal.enabled is False


# ============================================================================
# PIPELINE MODEL TESTS
# ============================================================================

class TestViolation:
    def test_roundtrip(self, sample_violation):
        d = sample_violation.to_dict()
        restored = Violation.from_dict(d)
        assert restored.constraint == "manager_approval_limit"
        assert restored.trigger_values["amount"] == 300000

    def test_dict_keys(self, sample_violation):
        d = sample_violation.to_dict()
        assert set(d.keys()) == {"constraint", "rule", "trigger_values", "explanation"}


class TestPolicyEvaluation:
    def test_roundtrip(self, sample_policy_evaluation):
        d = sample_policy_evaluation.to_dict()
        restored = PolicyEvaluation.from_dict(d)
        assert restored.result == "BLOCKED"
        assert restored.duration_ms == 0.723
        assert len(restored.violations) == 1
        assert restored.violations[0].constraint == "manager_approval_limit"

    def test_allowed_no_violations(self):
        pe = PolicyEvaluation(
            policy_file="test.csl",
            policy_hash="sha256:abc",
            result="ALLOWED",
            duration_ms=0.5,
        )
        d = pe.to_dict()
        assert d["result"] == "ALLOWED"
        assert d["violations"] == []


class TestCandidate:
    def test_roundtrip_with_evaluation(self, sample_candidate_blocked):
        d = sample_candidate_blocked.to_dict()
        restored = Candidate.from_dict(d)
        assert restored.candidate_id == "cand_002"
        assert restored.policy_evaluation is not None
        assert restored.policy_evaluation.result == "BLOCKED"

    def test_roundtrip_without_evaluation(self):
        c = Candidate(
            candidate_id="cand_001",
            strategy="test",
            llm_reasoning="because",
            llm_confidence=0.9,
            parameters={"x": 1},
        )
        d = c.to_dict()
        assert "policy_evaluation" not in d
        restored = Candidate.from_dict(d)
        assert restored.policy_evaluation is None


class TestAttempt:
    def test_roundtrip(self, sample_attempt):
        d = sample_attempt.to_dict()
        restored = Attempt.from_dict(d)
        assert restored.attempt_number == 1
        assert restored.outcome == "PARTIAL"
        assert len(restored.candidates) == 2


# ============================================================================
# DECISION AUDIT RECORD TESTS — spec §2.1 compliance
# ============================================================================

class TestDecisionAuditRecord:
    def test_to_dict_has_all_spec_sections(self, sample_audit_record):
        d = sample_audit_record.to_dict()
        required_sections = {
            "schema_version", "decision_id", "timestamp",
            "agent", "input", "reasoning", "decision",
            "compliance", "performance",
        }
        assert required_sections.issubset(set(d.keys()))

    def test_schema_version(self, sample_audit_record):
        assert sample_audit_record.schema_version == SCHEMA_VERSION

    def test_to_json_valid(self, sample_audit_record):
        json_str = sample_audit_record.to_json()
        parsed = json.loads(json_str)
        assert parsed["schema_version"] == SCHEMA_VERSION
        assert parsed["decision_id"].startswith("dec_")

    def test_from_json_roundtrip(self, sample_audit_record):
        json_str = sample_audit_record.to_json()
        restored = DecisionAuditRecord.from_json(json_str)
        assert restored.decision_id == sample_audit_record.decision_id
        assert restored.agent.model == "gpt-4o"
        assert restored.reasoning.total_candidates == 2
        assert restored.decision.result == "ALLOWED"
        assert restored.performance.total_duration_ms == 1247.3

    def test_full_roundtrip_dict(self, sample_audit_record):
        d = sample_audit_record.to_dict()
        restored = DecisionAuditRecord.from_dict(d)
        # Compare JSON serializations for deep equality
        assert restored.to_json() == sample_audit_record.to_json()

    def test_compact_format(self, sample_audit_record):
        compact = sample_audit_record.to_compact()
        required_keys = {
            "decision_id", "timestamp", "result", "action",
            "policy", "policy_hash", "violations", "attempts",
            "candidates_total", "candidates_passed", "selected",
            "duration_ms",
        }
        assert required_keys == set(compact.keys())

    def test_compact_json_single_line(self, sample_audit_record):
        compact_json = sample_audit_record.to_compact_json()
        assert "\n" not in compact_json
        parsed = json.loads(compact_json)
        assert parsed["result"] == "ALLOWED"

    def test_compliance_defaults(self, sample_audit_record):
        d = sample_audit_record.to_dict()
        compliance = d["compliance"]
        assert compliance["eu_ai_act"]["article_12_record_keeping"] is True
        assert compliance["formal_verification"]["verification_engine"] == "Z3"
        assert compliance["human_oversight"]["override_available"] is True

    def test_with_human_oversight(self, sample_audit_record):
        sample_audit_record.human_oversight_record = HumanOversightRecord(
            action="OVERRIDE",
            reason="Vendor not on approved list",
            override_decision="BLOCK",
        )
        d = sample_audit_record.to_dict()
        assert "human_oversight_record" in d
        assert d["human_oversight_record"]["action"] == "OVERRIDE"

    def test_without_human_oversight(self, sample_audit_record):
        d = sample_audit_record.to_dict()
        assert "human_oversight_record" not in d


# ============================================================================
# DECISION RESULT TESTS
# ============================================================================

class TestDecisionResult:
    def test_allowed_property(self, sample_audit_record):
        result = DecisionResult(
            result="ALLOWED",
            action="INCREASE_BUDGET",
            explanation="Within limits",
            parameters={"amount": 200000},
            audit=sample_audit_record,
        )
        assert result.allowed is True
        assert result.blocked is False

    def test_blocked_property(self, sample_audit_record):
        result = DecisionResult(
            result="BLOCKED",
            action="INCREASE_BUDGET",
            explanation="Exceeds manager limit",
            parameters={"amount": 300000},
            audit=sample_audit_record,
        )
        assert result.allowed is False
        assert result.blocked is True

    def test_decision_id_shortcut(self, sample_audit_record):
        result = DecisionResult(
            result="ALLOWED",
            action="test",
            explanation="test",
            parameters={},
            audit=sample_audit_record,
        )
        assert result.decision_id == sample_audit_record.decision_id

    def test_to_dict(self, sample_audit_record):
        result = DecisionResult(
            result="ALLOWED",
            action="test",
            explanation="test",
            parameters={"x": 1},
            audit=sample_audit_record,
        )
        d = result.to_dict()
        assert d["result"] == "ALLOWED"
        assert d["audit"]["schema_version"] == SCHEMA_VERSION
