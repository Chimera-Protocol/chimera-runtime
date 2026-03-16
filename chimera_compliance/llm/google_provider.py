"""
chimera-compliance — Google Gemini LLM Provider

Supports Gemini 2.0 Flash, Gemini 2.0 Pro, and any Google Generative AI model.
Uses the google-generativeai SDK.
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


class GoogleProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider.

    Usage:
        provider = GoogleProvider(model="gemini-2.0-flash", api_key="AIza...")
        candidates = provider.generate_candidates(...)
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
        **kwargs: Any,
    ):
        resolved_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("CHIMERA_API_KEY")
        super().__init__(model=model, api_key=resolved_key, temperature=temperature, **kwargs)
        self.max_output_tokens = max_output_tokens
        self._configured = False

    @property
    def provider_name(self) -> str:
        return "google"

    def _ensure_configured(self) -> None:
        """Configure the Google Generative AI SDK."""
        if self._configured:
            return

        try:
            import google.generativeai as genai
        except ImportError:
            raise LLMError(
                "Google Generative AI package not installed. "
                "Install with: pip install chimera-compliance[google]"
            )

        if not self.api_key:
            raise LLMAuthenticationError(
                "Google API key not found. Set GOOGLE_API_KEY or CHIMERA_API_KEY "
                "environment variable, or pass api_key to the provider."
            )

        genai.configure(api_key=self.api_key)
        self._configured = True

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call Google Gemini API.
        Gemini uses system_instruction + contents format.
        """
        self._ensure_configured()

        import google.generativeai as genai

        system_instruction = ""
        contents: List[Dict[str, Any]] = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [msg["content"]]})

        if not contents:
            contents = [{"role": "user", "parts": ["Generate candidates."]}]

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="application/json",
            )

            model_kwargs: Dict[str, Any] = {
                "model_name": self.model,
                "generation_config": generation_config,
            }
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction

            model = genai.GenerativeModel(**model_kwargs)
            response = model.generate_content(contents)

            if not response.text:
                raise LLMError("Google Gemini returned empty response")

            return response.text

        except ImportError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__

            if "api_key" in error_str or "authentication" in error_str or "permission" in error_str:
                raise LLMAuthenticationError(f"Google authentication failed: {e}") from e
            elif "quota" in error_str or "rate" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"Google rate limit exceeded: {e}") from e
            elif "timeout" in error_str or "deadline" in error_str:
                raise LLMTimeoutError(f"Google request timed out: {e}") from e
            else:
                raise LLMError(f"Google Gemini call failed ({error_type}): {e}") from e
