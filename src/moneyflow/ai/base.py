# SPDX-License-Identifier: MIT
"""Provider-agnostic interface for MoneyFlow's optional AI insights.

AI is strictly optional: the core application (parsing, analytics, dashboards,
persistence) works with no provider configured. Concrete providers implement
this interface for a local model or an OpenAI-compatible HTTP endpoint.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProviderError(RuntimeError):
    """Base class for all AI provider failures."""


class AIConfigurationError(AIProviderError):
    """Raised when a provider is misconfigured (missing model, URL, key, ...)."""


class AIUnavailableError(AIProviderError):
    """Raised when a provider's dependencies or endpoint are unavailable."""


class AIProvider(ABC):
    """Abstract AI provider.

    Lifecycle: construct cheaply, call :meth:`load` to perform any expensive
    setup (e.g. loading a local model), then call :meth:`generate_insights` /
    :meth:`answer_question`. Providers must never leak raw transaction data into
    logs or exception messages.
    """

    #: Human-readable provider name shown in the UI.
    name: str = "AI provider"

    def __init__(self) -> None:
        self._ready = False

    @property
    def ready(self) -> bool:
        """True once :meth:`load` has completed successfully."""
        return self._ready

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider could plausibly run (deps/config present).

        This is a cheap check; it does not guarantee a successful generation.
        """

    def load(self) -> None:
        """Perform any expensive one-time setup. Idempotent. Default: no-op."""
        self._ready = True

    @abstractmethod
    def generate_insights(
        self,
        financial_data: dict[str, Any],
        user_query: str | None = None,
        concise: bool = False,
        max_tokens: int | None = None,
        **_: Any,
    ) -> str:
        """Generate an insight string from the deterministic financial summary."""

    def answer_question(
        self,
        financial_data: dict[str, Any],
        question: str,
        concise: bool = False,
        max_tokens: int | None = None,
        **_: Any,
    ) -> str:
        """Answer a specific question. Default delegates to :meth:`generate_insights`."""
        return self.generate_insights(
            financial_data,
            user_query=question,
            concise=concise,
            max_tokens=max_tokens,
        )
