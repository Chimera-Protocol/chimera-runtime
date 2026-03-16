"""
chimera-compliance — LLM Provider Layer

Factory function to get the right provider by name.
All providers share the same interface (BaseLLMProvider).
"""

from __future__ import annotations

from typing import Any, Optional

from .base import (
    BaseLLMProvider,
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseParseError,
    build_variable_spec,
)


def get_provider(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> BaseLLMProvider:
    """
    Factory function to create an LLM provider by name.

    Args:
        provider: Provider name — "openai", "anthropic", "google", "ollama"
        model: Model identifier (e.g. "gpt-4o", "claude-sonnet-4-20250514")
        api_key: API key (optional, can also come from env vars)
        temperature: Sampling temperature (0.0 - 2.0)
        **kwargs: Additional provider-specific options

    Returns:
        Configured BaseLLMProvider instance

    Raises:
        LLMError: If the provider name is not recognized
    """
    provider_lower = provider.lower().strip()

    if provider_lower == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(model=model, api_key=api_key, temperature=temperature, **kwargs)

    elif provider_lower == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(model=model, api_key=api_key, temperature=temperature, **kwargs)

    elif provider_lower == "google":
        from .google_provider import GoogleProvider
        return GoogleProvider(model=model, api_key=api_key, temperature=temperature, **kwargs)

    elif provider_lower == "ollama":
        from .ollama_provider import OllamaProvider
        return OllamaProvider(model=model, api_key=api_key, temperature=temperature, **kwargs)

    else:
        available = ["openai", "anthropic", "google", "ollama"]
        raise LLMError(
            f"Unknown LLM provider: '{provider}'. "
            f"Available providers: {', '.join(available)}"
        )


__all__ = [
    "get_provider",
    "BaseLLMProvider",
    "LLMError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMResponseParseError",
    "build_variable_spec",
]
