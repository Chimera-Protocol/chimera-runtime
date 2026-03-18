"""
Tests for chimera_runtime.agent and chimera_runtime.oversight

Validates the full neuro→symbolic→audit pipeline:
  - ChimeraAgent.decide() with mock LLM + real CSL policy
  - Candidate generation → policy evaluation → selection
  - Retry loop: all blocked → rejection context → retry
  - Halt/resume mechanism (Art. 14)
  - HumanOversight: auto, sdk callback, override
  - Full DecisionAuditRecord construction and completeness
  - DecisionResult properties (.allowed, .blocked, .decision_id)
"""

import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from chimera_runtime.agent import ChimeraAgent, ChimeraAgentError, AgentHalted
from chimera_runtime.oversight import HumanOversight, OversightError
from chimera_runtime.llm.base import BaseLLMProvider, LLMError
from chimera_runtime.models import (
    Candidate,
    DecisionResult,
    DecisionAuditRecord,
    PolicyEvaluation,
    HumanOversightRecord,
    generate_candidate_id,
    SCHEMA_VERSION,
)
from chimera_runtime.policy import PolicyManager


# ============================================================================
# PATHS
# ============================================================================

POLICY_DIR = Path(__file__).parent.parent / "policies"
GOVERNANCE_CSL = POLICY_DIR / "governance.csl"


def _csl_available() -> bool:
    """Check if csl-core is importable and governance.csl exists."""
    try:
        from chimera_core import load_guard
        return GOVERNANCE_CSL.exists()
    except ImportError:
        return False


# ============================================================================
# MOCK LLM PROVIDER — returns configurable canned candidates
# ============================================================================

class MockLLM(BaseLLMProvider):
    """
    Mock LLM that returns pre-configured candidate lists per call.
    Each call to _call_llm pops the next response from the queue.
    """

    def __init__(self, responses: Optional[List[str]] = None, **kwargs: Any):
        super().__init__(model="mock-model", **kwargs)
        self._responses: List[str] = responses or []
        self._call_index = 0
        self.call_count = 0
        self.last_messages: List[Dict[str, str]] = []

    @property
    def provider_name(self) -> str:
        return "mock"

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        self.last_messages = messages
        self.call_count += 1

        if self._call_index < len(self._responses):
            response = self._responses[self._call_index]
            self._call_index += 1
            return response

        raise LLMError("MockLLM: no more canned responses")


# ============================================================================
# RESPONSE BUILDERS — create realistic LLM JSON responses
# ============================================================================

def make_candidates_json(candidates: List[Dict[str, Any]]) -> str:
    """Build a JSON string that the MockLLM returns."""
    return json.dumps(candidates)


# Candidates that PASS governance.csl (MANAGER, <250K, weekday)
PASSING_CANDIDATES = make_candidates_json([
    {
        "strategy": "Conservative digital campaign",
        "reasoning": "Allocate $150K to digital only, well within MANAGER limits",
        "confidence": 0.90,
        "parameters": {
            "amount": 150000,
            "role": "MANAGER",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
            "department": "marketing",
        },
    },
    {
        "strategy": "Moderate multi-channel",
        "reasoning": "Split $200K across digital and print",
        "confidence": 0.75,
        "parameters": {
            "amount": 200000,
            "role": "MANAGER",
            "channel": "ALL",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
            "department": "marketing",
        },
    },
    {
        "strategy": "Aggressive TV push",
        "reasoning": "Full $240K into TV advertising",
        "confidence": 0.60,
        "parameters": {
            "amount": 240000,
            "role": "MANAGER",
            "channel": "TV",
            "is_weekend": "NO",
            "urgency": "HIGH",
            "department": "marketing",
        },
    },
])

# Candidates that FAIL governance.csl (exceed MANAGER limit / analyst)
FAILING_CANDIDATES = make_candidates_json([
    {
        "strategy": "Overspend approach",
        "reasoning": "Go big with $400K",
        "confidence": 0.80,
        "parameters": {
            "amount": 400000,
            "role": "MANAGER",
            "channel": "TV",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
            "department": "marketing",
        },
    },
    {
        "strategy": "Analyst direct spend",
        "reasoning": "Analyst tries to spend directly",
        "confidence": 0.70,
        "parameters": {
            "amount": 50000,
            "role": "ANALYST",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "LOW",
            "department": "marketing",
        },
    },
    {
        "strategy": "Weekend non-critical",
        "reasoning": "Deploy on weekend without urgency",
        "confidence": 0.65,
        "parameters": {
            "amount": 100000,
            "role": "DIRECTOR",
            "channel": "DIGITAL",
            "is_weekend": "YES",
            "urgency": "LOW",
            "department": "marketing",
        },
    },
])

# Mixed: one passes, two fail
MIXED_CANDIDATES = make_candidates_json([
    {
        "strategy": "Overspend risky",
        "reasoning": "Try $500K as MANAGER",
        "confidence": 0.85,
        "parameters": {
            "amount": 500000,
            "role": "MANAGER",
            "channel": "TV",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
            "department": "marketing",
        },
    },
    {
        "strategy": "Safe conservative",
        "reasoning": "Keep under $200K as MANAGER",
        "confidence": 0.78,
        "parameters": {
            "amount": 180000,
            "role": "MANAGER",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
            "department": "marketing",
        },
    },
    {
        "strategy": "Analyst violation",
        "reasoning": "Analyst can't spend",
        "confidence": 0.50,
        "parameters": {
            "amount": 10000,
            "role": "ANALYST",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "LOW",
            "department": "marketing",
        },
    },
])


# ============================================================================
# AGENT DECIDE TESTS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed or policy missing")
class TestAgentDecide:
    """Test the full decide() pipeline with mock LLM + real CSL policy."""

    def _make_agent(self, responses: List[str], **kwargs: Any) -> ChimeraAgent:
        """Helper to create an agent with mock LLM and real policy."""
        mock_llm = MockLLM(responses=responses)
        pm = PolicyManager(str(GOVERNANCE_CSL))
        return ChimeraAgent(
            llm_provider=mock_llm,
            policy_manager=pm,
            **kwargs,
        )

    def test_all_candidates_pass(self):
        """All 3 candidates pass → selects highest confidence."""
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Increase marketing budget")

        assert result.allowed
        assert not result.blocked
        assert result.result == "ALLOWED"
        assert result.action == "Conservative digital campaign"  # highest confidence (0.90)
        assert result.parameters["amount"] == 150000
        assert result.audit.decision_id.startswith("dec_")

    def test_all_candidates_blocked(self):
        """All candidates blocked across all retries → BLOCKED."""
        agent = self._make_agent(
            [FAILING_CANDIDATES, FAILING_CANDIDATES, FAILING_CANDIDATES],
            max_retries=3,
        )
        result = agent.decide("Overspend budget")

        assert result.blocked
        assert not result.allowed
        assert result.result == "BLOCKED"
        assert result.action == "BLOCKED"
        assert "blocked" in result.explanation.lower()

    def test_mixed_candidates_selects_allowed(self):
        """2 blocked, 1 allowed → selects the allowed one."""
        agent = self._make_agent([MIXED_CANDIDATES])
        result = agent.decide("Marketing spend request")

        assert result.allowed
        assert result.action == "Safe conservative"
        assert result.parameters["amount"] == 180000

    def test_retry_after_first_all_blocked(self):
        """First attempt all blocked → retry → second attempt has passing candidates."""
        agent = self._make_agent(
            [FAILING_CANDIDATES, PASSING_CANDIDATES],
            max_retries=3,
        )
        result = agent.decide("Budget request")

        assert result.allowed
        assert result.action == "Conservative digital campaign"

        # Verify there were 2 attempts
        assert result.audit.reasoning.total_attempts == 2
        assert len(result.audit.reasoning.attempts) == 2
        assert result.audit.reasoning.attempts[0].outcome == "ALL_BLOCKED"
        assert result.audit.reasoning.attempts[1].outcome in ("ALL_PASSED", "PARTIAL")

    def test_retry_includes_rejection_context(self):
        """On retry, the LLM should receive rejection context."""
        mock_llm = MockLLM(responses=[FAILING_CANDIDATES, PASSING_CANDIDATES])
        pm = PolicyManager(str(GOVERNANCE_CSL))
        agent = ChimeraAgent(llm_provider=mock_llm, policy_manager=pm, max_retries=3)

        result = agent.decide("Budget request")

        # The second call should have rejection context in the system prompt
        assert mock_llm.call_count == 2
        system_prompt = mock_llm.last_messages[0]["content"]
        assert "Previous Attempt Failed" in system_prompt

    def test_max_retries_respected(self):
        """Agent stops after max_retries attempts."""
        agent = self._make_agent(
            [FAILING_CANDIDATES] * 5,
            max_retries=2,
        )
        result = agent.decide("Impossible request")

        assert result.blocked
        assert result.audit.reasoning.total_attempts == 2

    def test_single_retry(self):
        """max_retries=1 means only one attempt, no retry."""
        agent = self._make_agent(
            [FAILING_CANDIDATES],
            max_retries=1,
        )
        result = agent.decide("Will fail")

        assert result.blocked
        assert result.audit.reasoning.total_attempts == 1


# ============================================================================
# AUDIT RECORD TESTS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed or policy missing")
class TestAuditRecord:
    """Verify the audit record is complete and spec-compliant."""

    def _make_agent(self, responses: List[str]) -> ChimeraAgent:
        mock_llm = MockLLM(responses=responses)
        pm = PolicyManager(str(GOVERNANCE_CSL))
        return ChimeraAgent(llm_provider=mock_llm, policy_manager=pm)

    def test_audit_has_all_sections(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")
        audit = result.audit

        assert audit.schema_version == SCHEMA_VERSION
        assert audit.decision_id.startswith("dec_")
        assert audit.timestamp.endswith("Z")
        assert audit.agent is not None
        assert audit.input is not None
        assert audit.reasoning is not None
        assert audit.decision is not None
        assert audit.compliance is not None
        assert audit.performance is not None

    def test_audit_agent_info(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")
        ai = result.audit.agent

        assert ai.name == "chimera-runtime"
        assert ai.version == "0.1.0"
        assert ai.model == "mock-model"
        assert ai.model_provider == "mock"

    def test_audit_reasoning_trace(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")
        r = result.audit.reasoning

        assert r.total_candidates == 3
        assert r.total_attempts == 1
        assert len(r.attempts) == 1
        assert r.selected_candidate is not None
        assert r.selection_reasoning != ""

    def test_audit_decision_info(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")
        d = result.audit.decision

        assert d.result == "ALLOWED"
        assert d.action_taken == "Conservative digital campaign"
        assert d.policy_file != ""
        assert d.policy_hash.startswith("sha256:")

    def test_audit_compliance_defaults(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")
        c = result.audit.compliance

        assert c.eu_ai_act["article_12_record_keeping"] is True
        assert c.eu_ai_act["article_14_human_oversight"] is True
        assert c.formal_verification["verification_engine"] == "Z3"

    def test_audit_performance_timing(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")
        p = result.audit.performance

        assert p.total_duration_ms > 0
        assert p.policy_evaluation_ms >= 0

    def test_audit_serialization_roundtrip(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")

        json_str = result.audit.to_json()
        restored = DecisionAuditRecord.from_json(json_str)

        assert restored.decision_id == result.audit.decision_id
        assert restored.decision.result == result.audit.decision.result
        assert restored.reasoning.total_candidates == result.audit.reasoning.total_candidates

    def test_audit_compact_format(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")

        compact = result.audit.to_compact()
        assert compact["result"] == "ALLOWED"
        assert compact["decision_id"].startswith("dec_")
        assert compact["policy_hash"].startswith("sha256:")
        assert compact["attempts"] == 1

    def test_candidates_have_policy_evaluations(self):
        """Every candidate in the audit should have its policy evaluation attached."""
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")

        for attempt in result.audit.reasoning.attempts:
            for candidate in attempt.candidates:
                assert candidate.policy_evaluation is not None
                assert candidate.policy_evaluation.result in ("ALLOWED", "BLOCKED")


# ============================================================================
# DECISION RESULT TESTS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed or policy missing")
class TestDecisionResult:

    def _make_agent(self, responses: List[str]) -> ChimeraAgent:
        mock_llm = MockLLM(responses=responses)
        pm = PolicyManager(str(GOVERNANCE_CSL))
        return ChimeraAgent(llm_provider=mock_llm, policy_manager=pm)

    def test_allowed_result_properties(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")

        assert result.allowed is True
        assert result.blocked is False
        assert result.result == "ALLOWED"
        assert result.decision_id.startswith("dec_")
        assert result.parameters != {}
        assert result.explanation != ""

    def test_blocked_result_properties(self):
        agent = self._make_agent([FAILING_CANDIDATES] * 3)
        result = agent.decide("Impossible request")

        assert result.allowed is False
        assert result.blocked is True
        assert result.result == "BLOCKED"
        assert result.parameters == {}

    def test_result_to_dict(self):
        agent = self._make_agent([PASSING_CANDIDATES])
        result = agent.decide("Budget request")

        d = result.audit.to_dict()
        assert "schema_version" in d
        assert "decision_id" in d
        assert "agent" in d
        assert "reasoning" in d
        assert "decision" in d


# ============================================================================
# HALT / RESUME TESTS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed or policy missing")
class TestHaltResume:

    def _make_agent(self) -> ChimeraAgent:
        mock_llm = MockLLM(responses=[PASSING_CANDIDATES])
        pm = PolicyManager(str(GOVERNANCE_CSL))
        return ChimeraAgent(llm_provider=mock_llm, policy_manager=pm)

    def test_halt_raises_on_decide(self):
        agent = self._make_agent()
        agent.halt("Safety concern")
        assert agent.is_halted

        with pytest.raises(AgentHalted, match="halted"):
            agent.decide("This should fail")

    def test_resume_after_halt(self):
        agent = self._make_agent()
        agent.halt()
        assert agent.is_halted

        agent.resume()
        assert not agent.is_halted

        # Should work again
        result = agent.decide("Now it works")
        assert result.allowed

    def test_consecutive_block_counter(self):
        agent = ChimeraAgent(
            llm_provider=MockLLM(responses=[FAILING_CANDIDATES] * 10),
            policy_manager=PolicyManager(str(GOVERNANCE_CSL)),
            max_retries=1,
        )

        result1 = agent.decide("Will fail 1")
        assert result1.blocked
        assert agent.consecutive_blocks == 1

        result2 = agent.decide("Will fail 2")
        assert result2.blocked
        assert agent.consecutive_blocks == 2

    def test_decision_counter(self):
        mock_llm = MockLLM(responses=[PASSING_CANDIDATES, PASSING_CANDIDATES])
        pm = PolicyManager(str(GOVERNANCE_CSL))
        agent = ChimeraAgent(llm_provider=mock_llm, policy_manager=pm)

        assert agent.decision_count == 0
        agent.decide("First")
        assert agent.decision_count == 1
        agent.decide("Second")
        assert agent.decision_count == 2


# ============================================================================
# HUMAN OVERSIGHT TESTS
# ============================================================================

class TestHumanOversight:

    def test_auto_mode_always_approves(self):
        oversight = HumanOversight(mode="auto")
        candidate = Candidate(
            candidate_id="cand_001",
            strategy="Test",
            llm_reasoning="test",
            llm_confidence=0.9,
            parameters={"x": 1},
        )
        assert oversight.request_confirmation(candidate) is True

    def test_sdk_mode_calls_callback(self):
        callback = MagicMock(return_value=True)
        oversight = HumanOversight(mode="sdk", confirm_callback=callback)

        candidate = Candidate(
            candidate_id="cand_001",
            strategy="Test",
            llm_reasoning="test",
            llm_confidence=0.9,
            parameters={"x": 1},
        )
        result = oversight.request_confirmation(candidate)

        assert result is True
        callback.assert_called_once()

    def test_sdk_mode_callback_rejects(self):
        callback = MagicMock(return_value=False)
        oversight = HumanOversight(mode="sdk", confirm_callback=callback)

        candidate = Candidate(
            candidate_id="cand_001",
            strategy="Test",
            llm_reasoning="test",
            llm_confidence=0.9,
            parameters={"x": 1},
        )
        assert oversight.request_confirmation(candidate) is False

    def test_sdk_mode_requires_callback(self):
        with pytest.raises(OversightError, match="confirm_callback"):
            HumanOversight(mode="sdk")

    def test_invalid_mode_raises(self):
        with pytest.raises(OversightError, match="Unknown oversight mode"):
            HumanOversight(mode="invalid")

    def test_apply_override_confirm(self):
        oversight = HumanOversight(mode="auto")
        record = oversight.apply_override(action="CONFIRM", reason="Looks good")

        assert isinstance(record, HumanOversightRecord)
        assert record.action == "CONFIRM"
        assert record.reason == "Looks good"
        assert record.timestamp.endswith("Z")

    def test_apply_override_override(self):
        oversight = HumanOversight(mode="auto")
        record = oversight.apply_override(action="OVERRIDE", reason="Too risky")

        assert record.action == "OVERRIDE"
        assert record.override_decision == "HUMAN_OVERRIDE"

    def test_apply_override_stop(self):
        oversight = HumanOversight(mode="auto")
        record = oversight.apply_override(action="STOP", reason="Emergency")

        assert record.action == "STOP"

    def test_apply_override_invalid_action(self):
        oversight = HumanOversight(mode="auto")
        with pytest.raises(OversightError, match="Invalid override action"):
            oversight.apply_override(action="INVALID")


# ============================================================================
# OVERSIGHT INTEGRATION WITH AGENT
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed or policy missing")
class TestOversightIntegration:

    def test_sdk_callback_approves(self):
        """SDK callback returns True → decision proceeds normally."""
        callback = MagicMock(return_value=True)
        oversight = HumanOversight(mode="sdk", confirm_callback=callback)

        mock_llm = MockLLM(responses=[PASSING_CANDIDATES])
        pm = PolicyManager(str(GOVERNANCE_CSL))
        agent = ChimeraAgent(
            llm_provider=mock_llm,
            policy_manager=pm,
            oversight=oversight,
        )

        result = agent.decide("Budget request")
        assert result.allowed
        callback.assert_called_once()

    def test_sdk_callback_rejects(self):
        """SDK callback returns False → INTERRUPTED."""
        callback = MagicMock(return_value=False)
        oversight = HumanOversight(mode="sdk", confirm_callback=callback)

        mock_llm = MockLLM(responses=[PASSING_CANDIDATES])
        pm = PolicyManager(str(GOVERNANCE_CSL))
        agent = ChimeraAgent(
            llm_provider=mock_llm,
            policy_manager=pm,
            oversight=oversight,
        )

        result = agent.decide("Budget request")
        assert result.result == "INTERRUPTED"
        assert result.action == "DECLINED_BY_HUMAN"
        assert result.audit.human_oversight_record is not None
        assert result.audit.human_oversight_record.action == "STOP"

    def test_blocked_decision_no_confirmation_needed(self):
        """When all candidates are blocked, no confirmation is needed."""
        callback = MagicMock(return_value=True)
        oversight = HumanOversight(mode="sdk", confirm_callback=callback)

        mock_llm = MockLLM(responses=[FAILING_CANDIDATES] * 3)
        pm = PolicyManager(str(GOVERNANCE_CSL))
        agent = ChimeraAgent(
            llm_provider=mock_llm,
            policy_manager=pm,
            oversight=oversight,
            max_retries=1,
        )

        result = agent.decide("Will be blocked")
        assert result.blocked
        callback.assert_not_called()  # No confirmation needed for blocks


# ============================================================================
# FACTORY TESTS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed or policy missing")
class TestFromConfig:

    def test_from_config_with_defaults(self):
        """from_config with default config should create a working agent."""
        from chimera_runtime.models import AgentConfig
        config = AgentConfig()
        config.policy.file = str(GOVERNANCE_CSL)
        config.llm.api_key = "test-key"

        # This will create a real provider — just verify it doesn't crash
        agent = ChimeraAgent.from_config(config=config)
        assert agent is not None

    def test_from_config_with_overrides(self):
        """Overrides should take precedence over config."""
        from chimera_runtime.models import AgentConfig
        config = AgentConfig()
        config.policy.file = str(GOVERNANCE_CSL)

        agent = ChimeraAgent.from_config(
            config=config,
            model="gpt-4o-mini",
            api_key="override-key",
        )
        assert agent._llm.model == "gpt-4o-mini"
