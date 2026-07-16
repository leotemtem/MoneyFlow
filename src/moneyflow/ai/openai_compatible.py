# SPDX-License-Identifier: MIT
"""OpenAI-compatible chat-completions provider.

Works with any endpoint that implements the OpenAI ``/chat/completions`` API,
including local servers (Ollama, LM Studio, llama.cpp, vLLM) and hosted
services. Uses ``requests`` only — no vendor SDK required. API keys are read
from configuration and never logged.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from moneyflow.ai.base import (
    AIConfigurationError,
    AIProvider,
    AIProviderError,
    AIUnavailableError,
)
from moneyflow.ai.prompt_builder import build_messages
from moneyflow.config.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(AIProvider):
    """Call an OpenAI-compatible chat-completions endpoint over HTTP."""

    name = "OpenAI-compatible endpoint"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        settings = get_settings()
        base = base_url if base_url is not None else settings.ai_base_url
        self.base_url = base.rstrip("/")
        self.api_key = api_key if api_key is not None else settings.ai_api_key
        self.model = model if model is not None else settings.ai_model
        self.timeout = settings.ai_timeout
        self.max_tokens = settings.ai_max_tokens
        self.temperature = settings.ai_temperature

    def is_available(self) -> bool:
        """True when a base URL and model are configured (reachability tested at call time)."""
        return bool(self.base_url and self.model)

    def load(self) -> None:
        if not self.is_available():
            raise AIConfigurationError(
                "OpenAI-compatible provider needs MONEYFLOW_AI_BASE_URL and MONEYFLOW_AI_MODEL."
            )
        self._ready = True

    def generate_insights(
        self,
        financial_data: dict[str, Any],
        user_query: str | None = None,
        concise: bool = False,
        max_tokens: int | None = None,
        **_: Any,
    ) -> str:
        if not self._ready:
            self.load()

        messages = build_messages(financial_data, user_query, concise)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise AIUnavailableError("AI request timed out.") from exc
        except requests.RequestException as exc:
            # Deliberately do not include payload/response bodies (may echo data).
            raise AIUnavailableError("Could not reach the AI endpoint.") from exc

        if response.status_code >= 400:
            raise AIProviderError(f"AI endpoint returned HTTP {response.status_code}.")

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (ValueError, KeyError, IndexError) as exc:
            raise AIProviderError("AI endpoint returned an unexpected response shape.") from exc
