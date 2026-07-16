# SPDX-License-Identifier: MIT
"""Construct the configured AI provider (or ``None`` when AI is disabled)."""

from __future__ import annotations

import logging

from moneyflow.ai.base import AIProvider
from moneyflow.config.settings import (
    AI_PROVIDER_LOCAL,
    AI_PROVIDER_OPENAI,
    Settings,
    get_settings,
)

logger = logging.getLogger(__name__)


def get_ai_provider(settings: Settings | None = None) -> AIProvider | None:
    """Return an :class:`AIProvider` for the configured backend, or ``None``.

    ``None`` means AI is disabled — callers must treat AI insights as an
    optional feature and keep working without them.
    """
    settings = settings or get_settings()

    if settings.ai_provider == AI_PROVIDER_OPENAI:
        from moneyflow.ai.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider()

    if settings.ai_provider == AI_PROVIDER_LOCAL:
        from moneyflow.ai.local_mistral import LocalMistralProvider

        return LocalMistralProvider()

    return None
