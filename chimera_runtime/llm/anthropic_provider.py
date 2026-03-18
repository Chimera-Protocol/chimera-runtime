"""
chimera-runtime — Anthropic LLM Provider

Supports Claude Sonnet 4, Claude Opus, and any Anthropic Messages API model.
Anthropic uses a separate system parameter instead of a system message.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .base import (
    BaseLLMProvider,
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic LLM provider.

    Usage:
        provider = AnthropicProvider(model="claude-sonnet-4-20250514", api_key="sk-ant-...")
        candidates = provider.generate_candidates(...)
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: float = 60.0,
        **kwargs: Any,
    ):
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CHIMERA_API_KEY")
        super().__init__(model=model, api_key=resolved_key, temperature=temperature, **kwargs)
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client = None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _get_client(self) -> Any:
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise LLMError(
                    "Anthropic package not installed. "
                    "Install with: pip install chimera-runtime[anthropic]"
                )

            if not self.api_key:
                raise LLMAuthenticationError(
                    "Anthropic API key not found. Set ANTHROPIC_API_KEY or CHIMERA_API_KEY "
                    "environment variable, or pass api_key to the provider."
                )

            self._client = Anthropic(
                api_key=self.api_key,
                timeout=self.timeout,
            )

        return self._client

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call Anthropic Messages API.
        Anthropic requires system prompt as a separate parameter.
        """
        client = self._get_client()

        # Separate system from user/assistant messages
        system_content = ""
        api_messages: List[Dict[str, str]] = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                api_messages.append(msg)

        if not api_messages:
            api_messages = [{"role": "user", "content": "Generate candidates."}]

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_content,
                messages=api_messages,
            )

            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)

            content = "".join(text_parts)

            if not content:
                raise LLMError("Anthropic returned empty response content")

            return content

        except ImportError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__

            if "authentication" in error_str or "api_key" in error_str or "401" in error_str:
                raise LLMAuthenticationError(f"Anthropic authentication failed: {e}") from e
            elif "rate_limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}") from e
            elif "timeout" in error_str or "timed out" in error_str:
                raise LLMTimeoutError(f"Anthropic request timed out: {e}") from e
            elif error_type in ("APIError", "AnthropicError", "APIConnectionError"):
                raise LLMError(f"Anthropic API error: {e}") from e
            else:
                raise LLMError(f"Anthropic call failed ({error_type}): {e}") from e
