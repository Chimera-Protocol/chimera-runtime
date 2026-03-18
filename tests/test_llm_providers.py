"""
Tests for chimera_runtime.llm

Validates:
  - BaseLLMProvider candidate parsing from various JSON formats
  - System prompt construction with variable specs and rejection context
  - Provider factory returns correct provider types
  - Each provider wraps errors into chimera-runtime error types
  - MockProvider can simulate full generate_candidates flow
  - build_variable_spec formats correctly
"""

import json
import importlib
import pytest
from typing import Any, Dict, List, Optional

from chimera_runtime.llm import (
    get_provider,
    BaseLLMProvider,
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseParseError,
    build_variable_spec,
)
from chimera_runtime.models import Candidate


# ============================================================================
# HELPERS
# ============================================================================

def _sdk_available(name: str) -> bool:
    """Check if an optional SDK is importable."""
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


# ============================================================================
# MOCK PROVIDER — for testing the base class logic
# ============================================================================

class MockProvider(BaseLLMProvider):
    """
    Test provider that returns canned responses.
    Allows testing all parsing/prompt logic without real API calls.
    """

    def __init__(self, canned_response: str = "", **kwargs: Any):
        super().__init__(model="mock-model", **kwargs)
        self.canned_response = canned_response
        self.last_messages: List[Dict[str, str]] = []
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        self.last_messages = messages
        self.call_count += 1
        return self.canned_response


# ============================================================================
# SAMPLE RESPONSES — simulating real LLM output formats
# ============================================================================

CLEAN_JSON_RESPONSE = json.dumps([
    {
        "strategy": "Conservative budget increase",
        "reasoning": "Stay within MANAGER limits by capping at $200K",
        "confidence": 0.85,
        "parameters": {"amount": 200000, "role": "MANAGER", "channel": "DIGITAL", "is_weekend": "NO", "urgency": "MEDIUM"}
    },
    {
        "strategy": "Moderate all-channel spread",
        "reasoning": "Distribute $180K across all channels for broader reach",
        "confidence": 0.72,
        "parameters": {"amount": 180000, "role": "MANAGER", "channel": "ALL", "is_weekend": "NO", "urgency": "MEDIUM"}
    },
    {
        "strategy": "Aggressive maximum allocation",
        "reasoning": "Push to the $250K MANAGER ceiling for maximum impact",
        "confidence": 0.60,
        "parameters": {"amount": 250000, "role": "MANAGER", "channel": "TV", "is_weekend": "NO", "urgency": "HIGH"}
    },
])

FENCED_JSON_RESPONSE = """Here are the strategy candidates:

```json
[
  {
    "strategy": "Safe approach",
    "reasoning": "Well within limits",
    "confidence": 0.9,
    "parameters": {"amount": 100000, "role": "MANAGER"}
  }
]
```

I hope these help!"""

WRAPPED_JSON_RESPONSE = """Based on the policy constraints, here are my recommendations:

[
  {
    "strategy": "Option A",
    "reasoning": "Low risk",
    "confidence": 0.8,
    "parameters": {"amount": 50000}
  },
  {
    "strategy": "Option B",
    "reasoning": "Medium risk",
    "confidence": 0.6,
    "parameters": {"amount": 150000}
  }
]

These options should satisfy the governance policy."""

SINGLE_CANDIDATE_RESPONSE = json.dumps([
    {
        "strategy": "Only option",
        "reasoning": "Sole viable approach",
        "confidence": 0.95,
        "parameters": {"x": 1}
    }
])


# ============================================================================
# CANDIDATE PARSING TESTS
# ============================================================================

class TestCandidateParsing:
    def test_parse_clean_json(self):
        provider = MockProvider(canned_response=CLEAN_JSON_RESPONSE)
        candidates = provider.generate_candidates("test request", {}, n=3)
        assert len(candidates) == 3
        assert all(isinstance(c, Candidate) for c in candidates)

    def test_candidate_fields_populated(self):
        provider = MockProvider(canned_response=CLEAN_JSON_RESPONSE)
        candidates = provider.generate_candidates("test", {})
        c = candidates[0]
        assert c.candidate_id == "cand_001"
        assert c.strategy == "Conservative budget increase"
        assert c.llm_reasoning == "Stay within MANAGER limits by capping at $200K"
        assert c.llm_confidence == 0.85
        assert c.parameters["amount"] == 200000
        assert c.parameters["role"] == "MANAGER"

    def test_candidate_ids_sequential(self):
        provider = MockProvider(canned_response=CLEAN_JSON_RESPONSE)
        candidates = provider.generate_candidates("test", {})
        assert candidates[0].candidate_id == "cand_001"
        assert candidates[1].candidate_id == "cand_002"
        assert candidates[2].candidate_id == "cand_003"

    def test_parse_fenced_markdown(self):
        provider = MockProvider(canned_response=FENCED_JSON_RESPONSE)
        candidates = provider.generate_candidates("test", {})
        assert len(candidates) == 1
        assert candidates[0].strategy == "Safe approach"

    def test_parse_wrapped_text(self):
        provider = MockProvider(canned_response=WRAPPED_JSON_RESPONSE)
        candidates = provider.generate_candidates("test", {})
        assert len(candidates) == 2
        assert candidates[0].strategy == "Option A"
        assert candidates[1].strategy == "Option B"

    def test_parse_single_candidate(self):
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        candidates = provider.generate_candidates("test", {})
        assert len(candidates) == 1

    def test_parse_missing_fields_uses_defaults(self):
        response = json.dumps([{"parameters": {"x": 1}}])
        provider = MockProvider(canned_response=response)
        candidates = provider.generate_candidates("test", {})
        assert len(candidates) == 1
        assert candidates[0].strategy == "Strategy 1"
        assert candidates[0].llm_confidence == 0.5
        assert candidates[0].llm_reasoning == ""

    def test_parse_empty_array_raises(self):
        provider = MockProvider(canned_response="[]")
        with pytest.raises(LLMResponseParseError, match="no valid candidates"):
            provider.generate_candidates("test", {})

    def test_parse_not_array_raises(self):
        """LLM returns a JSON object instead of array → clear error."""
        provider = MockProvider(canned_response='{"key": "value"}')
        with pytest.raises(LLMResponseParseError, match="Expected JSON array"):
            provider.generate_candidates("test", {})

    def test_parse_invalid_json_raises(self):
        provider = MockProvider(canned_response="this is not json at all")
        with pytest.raises(LLMResponseParseError):
            provider.generate_candidates("test", {})

    def test_parse_no_json_in_text_raises(self):
        provider = MockProvider(canned_response="I cannot generate candidates for this request.")
        with pytest.raises(LLMResponseParseError, match="Could not find JSON"):
            provider.generate_candidates("test", {})

    def test_non_dict_items_skipped(self):
        response = json.dumps([
            {"strategy": "Valid", "parameters": {"x": 1}, "reasoning": "ok", "confidence": 0.8},
            "invalid string item",
            42,
            {"strategy": "Also valid", "parameters": {"y": 2}, "reasoning": "ok2", "confidence": 0.7},
        ])
        provider = MockProvider(canned_response=response)
        candidates = provider.generate_candidates("test", {})
        assert len(candidates) == 2
        assert candidates[0].strategy == "Valid"
        assert candidates[1].strategy == "Also valid"


# ============================================================================
# SYSTEM PROMPT TESTS
# ============================================================================

class TestSystemPrompt:
    def test_prompt_includes_candidate_count(self):
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        provider.generate_candidates("test", {}, n=5)
        system_msg = provider.last_messages[0]["content"]
        assert "5" in system_msg

    def test_prompt_includes_variable_spec(self):
        spec = "  - amount: 0..1000000\n  - role: {\"MANAGER\", \"DIRECTOR\"}"
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        provider.generate_candidates("test", {}, variable_spec=spec)
        system_msg = provider.last_messages[0]["content"]
        assert "amount: 0..1000000" in system_msg
        assert "MANAGER" in system_msg

    def test_prompt_includes_rejection_context(self):
        rejection = "Constraint 'manager_approval_limit' violated: amount 300000 > 250000"
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        provider.generate_candidates("test", {}, rejection_context=rejection)
        system_msg = provider.last_messages[0]["content"]
        assert "Previous Attempt Failed" in system_msg
        assert "manager_approval_limit" in system_msg

    def test_prompt_no_rejection_when_none(self):
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        provider.generate_candidates("test", {})
        system_msg = provider.last_messages[0]["content"]
        assert "Previous Attempt Failed" not in system_msg

    def test_user_message_includes_request(self):
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        provider.generate_candidates("Increase budget by 40%", {})
        user_msg = provider.last_messages[1]["content"]
        assert "Increase budget by 40%" in user_msg

    def test_user_message_includes_context(self):
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        provider.generate_candidates("test", {"role": "MANAGER", "user_id": "usr_001"})
        user_msg = provider.last_messages[1]["content"]
        assert "role=MANAGER" in user_msg
        assert "user_id=usr_001" in user_msg

    def test_messages_structure(self):
        provider = MockProvider(canned_response=SINGLE_CANDIDATE_RESPONSE)
        provider.generate_candidates("test", {})
        assert len(provider.last_messages) == 2
        assert provider.last_messages[0]["role"] == "system"
        assert provider.last_messages[1]["role"] == "user"


# ============================================================================
# PROVIDER FACTORY TESTS
# ============================================================================

class TestProviderFactory:
    def test_get_openai_provider(self):
        provider = get_provider("openai", model="gpt-4o", api_key="test")
        assert provider.provider_name == "openai"
        assert provider.model == "gpt-4o"

    def test_get_anthropic_provider(self):
        provider = get_provider("anthropic", model="claude-sonnet-4-20250514", api_key="test")
        assert provider.provider_name == "anthropic"

    def test_get_google_provider(self):
        provider = get_provider("google", model="gemini-2.0-flash", api_key="test")
        assert provider.provider_name == "google"

    def test_get_ollama_provider(self):
        provider = get_provider("ollama", model="llama3")
        assert provider.provider_name == "ollama"

    def test_unknown_provider_raises(self):
        with pytest.raises(LLMError, match="Unknown LLM provider"):
            get_provider("unknown_provider", model="test")

    def test_case_insensitive(self):
        provider = get_provider("OpenAI", model="gpt-4o", api_key="test")
        assert provider.provider_name == "openai"

    def test_provider_info(self):
        provider = get_provider("openai", model="gpt-4o", api_key="test", temperature=0.3)
        info = provider.provider_info
        assert info["provider"] == "openai"
        assert info["model"] == "gpt-4o"
        assert info["temperature"] == 0.3


# ============================================================================
# PROVIDER ERROR HANDLING TESTS
# These tests validate error behavior regardless of whether SDK is installed.
# If SDK is missing → LLMError("not installed").
# If SDK is present but no key → LLMAuthenticationError("API key not found").
# Both are valid — the provider correctly reports what's wrong.
# ============================================================================

class TestOpenAIErrors:
    def test_no_key_or_no_package_raises_llm_error(self):
        """Without API key, OpenAI provider should raise some LLMError."""
        provider = get_provider("openai", model="gpt-4o")
        provider.api_key = None
        with pytest.raises(LLMError):
            provider._get_client()

    @pytest.mark.skipif(not _sdk_available("openai"), reason="openai SDK not installed")
    def test_missing_api_key_raises_auth_error(self):
        """With SDK installed but no key → LLMAuthenticationError."""
        provider = get_provider("openai", model="gpt-4o")
        provider.api_key = None
        with pytest.raises(LLMAuthenticationError, match="API key not found"):
            provider._get_client()


class TestAnthropicErrors:
    def test_no_key_or_no_package_raises_llm_error(self):
        """Without API key, Anthropic provider should raise some LLMError."""
        provider = get_provider("anthropic", model="claude-sonnet-4-20250514")
        provider.api_key = None
        with pytest.raises(LLMError):
            provider._get_client()

    @pytest.mark.skipif(not _sdk_available("anthropic"), reason="anthropic SDK not installed")
    def test_missing_api_key_raises_auth_error(self):
        """With SDK installed but no key → LLMAuthenticationError."""
        provider = get_provider("anthropic", model="claude-sonnet-4-20250514")
        provider.api_key = None
        with pytest.raises(LLMAuthenticationError, match="API key not found"):
            provider._get_client()


class TestGoogleErrors:
    def test_no_key_or_no_package_raises_llm_error(self):
        """Without API key, Google provider should raise some LLMError."""
        provider = get_provider("google", model="gemini-2.0-flash")
        provider.api_key = None
        with pytest.raises(LLMError):
            provider._ensure_configured()

    @pytest.mark.skipif(not _sdk_available("google.generativeai"), reason="google SDK not installed")
    def test_missing_api_key_raises_auth_error(self):
        """With SDK installed but no key → LLMAuthenticationError."""
        provider = get_provider("google", model="gemini-2.0-flash")
        provider.api_key = None
        with pytest.raises(LLMAuthenticationError, match="API key not found"):
            provider._ensure_configured()


class TestOllamaErrors:
    def test_connection_refused_message(self):
        """Ollama should give helpful error when server isn't running."""
        provider = get_provider("ollama", model="llama3", base_url="http://localhost:99999")
        with pytest.raises(LLMError, match="Cannot connect|request failed|Ollama"):
            provider._call_llm([{"role": "user", "content": "test"}])


# ============================================================================
# VARIABLE SPEC BUILDER TESTS
# ============================================================================

class TestBuildVariableSpec:
    def test_basic_spec(self):
        spec = build_variable_spec(
            ["amount", "role"],
            {"amount": "0..1000000", "role": '{"MANAGER", "DIRECTOR"}'},
        )
        assert "amount: 0..1000000" in spec
        assert 'role: {"MANAGER", "DIRECTOR"}' in spec

    def test_sorted_output(self):
        spec = build_variable_spec(
            ["zebra", "alpha", "middle"],
            {"zebra": "0..10", "alpha": "0..5", "middle": "0..8"},
        )
        lines = spec.strip().split("\n")
        assert "alpha" in lines[0]
        assert "middle" in lines[1]
        assert "zebra" in lines[2]

    def test_empty_variables(self):
        spec = build_variable_spec([], {})
        assert "No policy variables" in spec

    def test_missing_domain_uses_any(self):
        spec = build_variable_spec(["unknown_var"], {})
        assert "unknown_var: any" in spec


# ============================================================================
# INTEGRATION: MOCK FULL FLOW
# ============================================================================

class TestFullMockFlow:
    """Simulate the full generate_candidates → parse → return flow."""

    def test_full_flow_with_variable_spec(self):
        provider = MockProvider(canned_response=CLEAN_JSON_RESPONSE)
        spec = "  - amount: 0..1000000\n  - role: {\"MANAGER\"}"
        candidates = provider.generate_candidates(
            request="Increase marketing budget by 40%",
            context={"user_id": "usr_001", "role": "MANAGER"},
            n=3,
            variable_spec=spec,
        )
        assert len(candidates) == 3
        assert provider.call_count == 1

        # Verify system prompt was built correctly
        system_msg = provider.last_messages[0]["content"]
        assert "amount: 0..1000000" in system_msg
        assert "3" in system_msg  # n=3

        # Verify user message
        user_msg = provider.last_messages[1]["content"]
        assert "Increase marketing budget" in user_msg
        assert "role=MANAGER" in user_msg

    def test_retry_flow_with_rejection(self):
        """Simulate: first attempt blocked → retry with rejection context."""
        provider = MockProvider(canned_response=CLEAN_JSON_RESPONSE)

        # Attempt 1
        candidates_1 = provider.generate_candidates("test", {}, n=3)
        assert len(candidates_1) == 3
        assert provider.call_count == 1

        # Attempt 2 with rejection
        rejection = "Constraint 'manager_approval_limit' violated: amount 300000 > 250000"
        candidates_2 = provider.generate_candidates("test", {}, n=3, rejection_context=rejection)
        assert len(candidates_2) == 3
        assert provider.call_count == 2

        # Verify rejection was in the system prompt
        system_msg = provider.last_messages[0]["content"]
        assert "manager_approval_limit" in system_msg
        assert "Previous Attempt Failed" in system_msg

    def test_candidate_policy_evaluation_initially_none(self):
        """Candidates from LLM should not have policy_evaluation set yet."""
        provider = MockProvider(canned_response=CLEAN_JSON_RESPONSE)
        candidates = provider.generate_candidates("test", {})
        for c in candidates:
            assert c.policy_evaluation is None

    def test_candidates_are_serializable(self):
        """Every candidate should roundtrip through to_dict/from_dict."""
        provider = MockProvider(canned_response=CLEAN_JSON_RESPONSE)
        candidates = provider.generate_candidates("test", {})
        for c in candidates:
            d = c.to_dict()
            restored = Candidate.from_dict(d)
            assert restored.candidate_id == c.candidate_id
            assert restored.strategy == c.strategy
            assert restored.parameters == c.parameters
