"""
chimera-compliance — Ollama LLM Provider

Supports any local model running via Ollama (llama3, mistral, codellama, etc.).
Uses Ollama's HTTP REST API directly — no external package needed.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from .base import (
    BaseLLMProvider,
    LLMError,
    LLMTimeoutError,
)


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaProvider(BaseLLMProvider):
    """
    Ollama local LLM provider.

    No API key needed — communicates with a local Ollama server.
    Uses the HTTP API directly (zero external dependencies).

    Usage:
        provider = OllamaProvider(model="llama3")
        candidates = provider.generate_candidates(...)
    """

    def __init__(
        self,
        model: str = "llama3",
        api_key: Optional[str] = None,  # Unused, kept for interface consistency
        temperature: float = 0.7,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        timeout: float = 120.0,
        **kwargs: Any,
    ):
        super().__init__(model=model, api_key=api_key, temperature=temperature, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call Ollama's /api/chat endpoint via HTTP.
        Uses stdlib urllib — no external dependencies needed.
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
            },
        }

        request_body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
                data = json.loads(response_body)

                content = data.get("message", {}).get("content", "")

                if not content:
                    raise LLMError(
                        f"Ollama returned empty response. "
                        f"Model: {self.model}, Status: {response.status}"
                    )

                return content

        except urllib.error.URLError as e:
            reason = str(getattr(e, "reason", e))
            if "refused" in reason.lower() or "connection" in reason.lower():
                raise LLMError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    f"Is Ollama running? Start with: ollama serve\n"
                    f"Error: {reason}"
                ) from e
            raise LLMError(f"Ollama request failed: {reason}") from e

        except TimeoutError as e:
            raise LLMTimeoutError(
                f"Ollama request timed out after {self.timeout}s. "
                f"Model: {self.model}. Try a smaller model or increase timeout."
            ) from e

        except json.JSONDecodeError as e:
            raise LLMError(f"Ollama returned invalid JSON: {e}") from e

        except Exception as e:
            if "timeout" in str(e).lower():
                raise LLMTimeoutError(f"Ollama timed out: {e}") from e
            raise LLMError(f"Ollama call failed: {e}") from e
