"""
chimera-compliance — OpenAI LLM Provider

Supports GPT-4o, GPT-4.1, GPT-4o-mini, and any OpenAI-compatible model.
Uses JSON mode for structured output when available.
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


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider.

    Usage:
        provider = OpenAIProvider(model="gpt-4o", api_key="sk-...")
        candidates = provider.generate_candidates(
            request="Increase marketing budget",
            context={"role": "MANAGER"},
            n=3,
            variable_spec="  - amount: 0..1000000\\n  - role: ...",
        )
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        **kwargs: Any,
    ):
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("CHIMERA_API_KEY")
        super().__init__(model=model, api_key=resolved_key, temperature=temperature, **kwargs)
        self.base_url = base_url
        self.timeout = timeout
        self._client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    def _get_client(self) -> Any:
        """Lazy-initialize the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise LLMError(
                    "OpenAI package not installed. "
                    "Install with: pip install chimera-compliance[openai]"
                )

            if not self.api_key:
                raise LLMAuthenticationError(
                    "OpenAI API key not found. Set OPENAI_API_KEY or CHIMERA_API_KEY "
                    "environment variable, or pass api_key to the provider."
                )

            client_kwargs: Dict[str, Any] = {
                "api_key": self.api_key,
                "timeout": self.timeout,
            }
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self._client = OpenAI(**client_kwargs)

        return self._client

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call OpenAI Chat Completions API.
        Uses response_format=json_object for models that support it.
        """
        client = self._get_client()

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        # Enable JSON mode for supported models
        json_mode_models = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"}
        if any(self.model.startswith(m) for m in json_mode_models):
            request_kwargs["response_format"] = {"type": "json_object"}

        try:
            response = client.chat.completions.create(**request_kwargs)
            content = response.choices[0].message.content

            if content is None:
                raise LLMError("OpenAI returned empty response content")

            return content

        except ImportError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__

            if "authentication" in error_str or "api_key" in error_str or "401" in error_str:
                raise LLMAuthenticationError(f"OpenAI authentication failed: {e}") from e
            elif "rate_limit" in error_str or "rate limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
            elif "timeout" in error_str or "timed out" in error_str:
                raise LLMTimeoutError(f"OpenAI request timed out: {e}") from e
            elif error_type in ("APIError", "OpenAIError", "APIConnectionError"):
                raise LLMError(f"OpenAI API error: {e}") from e
            else:
                raise LLMError(f"OpenAI call failed ({error_type}): {e}") from e
