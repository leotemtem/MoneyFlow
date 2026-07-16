# SPDX-License-Identifier: MIT
"""Optional AI insights for MoneyFlow (local model or OpenAI-compatible endpoint)."""

from moneyflow.ai.base import (
    AIConfigurationError,
    AIProvider,
    AIProviderError,
    AIUnavailableError,
)
from moneyflow.ai.factory import get_ai_provider

__all__ = [
    "AIProvider",
    "AIProviderError",
    "AIConfigurationError",
    "AIUnavailableError",
    "get_ai_provider",
]
