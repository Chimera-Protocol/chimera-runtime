"""
chimera-runtime — Base LLM Provider

Abstract base class for all LLM providers.
Handles system prompt construction, structured output parsing,
and the candidate generation contract.

The system prompt instructs the LLM to:
  1. Analyze the request
  2. Generate N diverse strategy candidates
  3. Output structured JSON with strategy, parameters, reasoning, confidence
  4. On retry: incorporate rejection context (policy violations) to adapt

All providers must implement _call_llm() — the raw API call.
Everything else (prompt building, parsing, candidate construction) is shared.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models import Candidate, generate_candidate_id


# ============================================================================
# ERRORS
# ============================================================================

class LLMError(Exception):
    """Base error for LLM operations."""
    pass


class LLMAuthenticationError(LLMError):
    """API key is missing or invalid."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMTimeoutError(LLMError):
    """Request timed out."""
    pass


class LLMResponseParseError(LLMError):
    """Could not parse structured output from LLM response."""
    pass


# ============================================================================
# SYSTEM PROMPT TEMPLATE
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = """\
You are a decision-making agent operating under strict policy constraints.
Your job is to analyze a request and generate {n} diverse strategy candidates.

## Policy Variables
The following variables are defined in the governance policy. Every candidate MUST provide values for ALL of these:
{variable_spec}

## Output Format
You MUST respond with ONLY a JSON array. No markdown, no explanation, no backticks.
Each element is an object with exactly these keys:
- "strategy": A short name for this approach (string)
- "reasoning": Your detailed reasoning for why this strategy makes sense (string)
- "confidence": Your confidence in this strategy from 0.0 to 1.0 (number)
- "parameters": An object with values for EVERY policy variable listed above

## Rules
1. Generate exactly {n} candidates — no more, no less
2. Make candidates DIVERSE — vary the parameters meaningfully
3. At least one candidate should be conservative (likely to pass policy)
4. Each candidate's parameters must contain ALL policy variables
5. Parameter values must be within the declared ranges/enums shown above
{rejection_section}
## Example Response
[
  {{
    "strategy": "Conservative approach",
    "reasoning": "Stay well within limits to ensure approval",
    "confidence": 0.85,
    "parameters": {{{example_params}}}
  }},
  {{
    "strategy": "Moderate approach",
    "reasoning": "Balance impact with policy compliance",
    "confidence": 0.70,
    "parameters": {{{example_params}}}
  }}
]

Respond with ONLY the JSON array. No other text."""


REJECTION_SECTION_TEMPLATE = """
## Previous Attempt Failed
Your previous candidates were REJECTED by the policy engine. Here are the violations:
{violations}

You MUST adapt your strategy to avoid these violations. Generate new candidates
that comply with the constraints described above. Do NOT repeat the same parameter
values that caused violations."""


# ============================================================================
# BASE PROVIDER
# ============================================================================

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Subclasses must implement:
      - _call_llm(messages) → raw response string
      - provider_name (property) → str

    Everything else is handled by the base:
      - System prompt construction
      - Candidate parsing from JSON
      - Rejection context formatting
      - Error wrapping
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.extra_config = kwargs

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def generate_candidates(
        self,
        request: str,
        context: Dict[str, Any],
        n: int = 3,
        variable_spec: str = "",
        rejection_context: Optional[str] = None,
    ) -> List[Candidate]:
        """
        Generate N strategy candidates for a given request.

        Args:
            request: Natural language request from the user
            context: Additional context (session_id, user_id, role, etc.)
            n: Number of candidates to generate
            variable_spec: Policy variable descriptions for the prompt
            rejection_context: If retrying, the violations from the previous attempt

        Returns:
            List of Candidate objects with strategy, parameters, reasoning, confidence

        Raises:
            LLMError: If the API call fails
            LLMResponseParseError: If the response cannot be parsed
        """
        system_prompt = self._build_system_prompt(n, variable_spec, rejection_context)
        user_message = self._build_user_message(request, context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        raw_response = self._call_llm(messages)
        candidates = self._parse_candidates(raw_response, n)

        return candidates

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g. 'openai', 'anthropic')."""
        ...

    @property
    def provider_info(self) -> Dict[str, Any]:
        """Return provider metadata for audit records."""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "temperature": self.temperature,
        }

    # ========================================================================
    # ABSTRACT — Must be implemented by subclasses
    # ========================================================================

    @abstractmethod
    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Make the raw API call to the LLM.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": str}

        Returns:
            Raw text response from the LLM

        Raises:
            LLMError subclasses for specific failure modes
        """
        ...

    # ========================================================================
    # PROMPT BUILDING
    # ========================================================================

    def _build_system_prompt(
        self,
        n: int,
        variable_spec: str,
        rejection_context: Optional[str],
    ) -> str:
        """Build the system prompt with variable spec and optional rejection context."""
        rejection_section = ""
        if rejection_context:
            rejection_section = REJECTION_SECTION_TEMPLATE.format(
                violations=rejection_context
            )

        example_params = self._build_example_params(variable_spec)

        return SYSTEM_PROMPT_TEMPLATE.format(
            n=n,
            variable_spec=variable_spec or "(No policy variables specified)",
            rejection_section=rejection_section,
            example_params=example_params,
        )

    def _build_user_message(self, request: str, context: Dict[str, Any]) -> str:
        """Build the user message with request and context."""
        parts = [f"Request: {request}"]
        if context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in sorted(context.items()))
            parts.append(f"Context: {ctx_str}")
        return "\n".join(parts)

    def _build_example_params(self, variable_spec: str) -> str:
        """Generate example parameter keys from variable spec for the prompt."""
        if not variable_spec:
            return '"key": "value"'

        params = []
        for line in variable_spec.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                var_name = line.split(":")[0].strip().strip("-").strip()
                if var_name:
                    params.append(f'"{var_name}": ...')

        return ", ".join(params) if params else '"key": "value"'

    # ========================================================================
    # RESPONSE PARSING
    # ========================================================================

    def _parse_candidates(self, raw_response: str, expected_n: int) -> List[Candidate]:
        """
        Parse LLM response into Candidate objects.

        Handles common LLM output quirks:
          - Markdown code fences
          - Leading/trailing whitespace
          - Extra text before/after JSON array
          - LLM returning a JSON object instead of array
        """
        json_str = self._extract_json_array(raw_response)

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise LLMResponseParseError(
                f"Failed to parse LLM response as JSON: {e}\n"
                f"Raw response (first 500 chars): {raw_response[:500]}"
            )

        if isinstance(parsed, dict):
            found_list = False
            for key, value in parsed.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    parsed = value
                    found_list = True
                    break

            if not found_list:
                # Treat single dict as a one-element array
                parsed = [parsed]

        if not isinstance(parsed, list):
            raise LLMResponseParseError(
                f"Expected JSON array, got {type(parsed).__name__}"
            )

        candidates: List[Candidate] = []
        for i, item in enumerate(parsed):
            if not isinstance(item, dict):
                continue

            candidates.append(Candidate(
                candidate_id=generate_candidate_id(i + 1),
                strategy=str(item.get("strategy", f"Strategy {i + 1}")),
                llm_reasoning=str(item.get("reasoning", "")),
                llm_confidence=float(item.get("confidence", 0.5)),
                parameters=item.get("parameters", {}),
            ))

        if not candidates:
            raise LLMResponseParseError(
                "LLM response contained no valid candidates"
            )

        return candidates

    def _extract_json_array(self, text: str) -> str:
        """
        Extract a JSON array from LLM response text.

        Handles:
          - Clean JSON array: [...]
          - JSON object (error): {...} → raises descriptive error
          - Markdown fenced: ```json [...] ```
          - Text around JSON: "Here are the candidates: [...]"
        """
        text = text.strip()

        # Try 1: Direct array — text starts with [
        if text.startswith("["):
            return text

        # Try 2: Detect JSON object (common LLM mistake) — fail fast with clear message
        if text.startswith("{"):
            # Let the caller parse it and raise "Expected JSON array"
            return text

        # Try 3: Strip markdown code fences
        fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
        if fenced:
            return fenced.group(1)

        # Try 4: Find the outermost [...] in the text
        bracket_match = re.search(r"\[.*\]", text, re.DOTALL)
        if bracket_match:
            return bracket_match.group(0)

        raise LLMResponseParseError(
            f"Could not find JSON array in LLM response.\n"
            f"Response (first 500 chars): {text[:500]}"
        )


# ============================================================================
# VARIABLE SPEC BUILDER
# ============================================================================

def build_variable_spec(
    variable_names: List[str],
    variable_domains: Dict[str, str],
) -> str:
    """
    Build a human-readable variable specification string for the LLM prompt.

    Args:
        variable_names: List of variable names from PolicyManager
        variable_domains: Dict of variable_name → domain string from csl-core

    Returns:
        Formatted string like:
          - amount: 0..1000000
          - role: {"ANALYST", "MANAGER", "DIRECTOR"}
    """
    if not variable_names:
        return "(No policy variables defined)"

    lines = []
    for name in sorted(variable_names):
        domain = variable_domains.get(name, "any")
        lines.append(f"  - {name}: {domain}")

    return "\n".join(lines)
