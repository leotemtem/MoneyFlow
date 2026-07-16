# SPDX-License-Identifier: MIT
"""Centralised, environment-driven configuration for MoneyFlow.

All runtime configuration is read from environment variables (optionally loaded
from a local ``.env`` file). Nothing here holds secrets by default: sensible,
safe defaults let the application run locally with SQLite and no AI provider.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Repository/runtime data directory (created on demand for the SQLite default).
DATA_DIR = Path(os.getenv("MONEYFLOW_DATA_DIR", "data")).expanduser()

# Valid AI provider identifiers.
AI_PROVIDER_NONE = "none"
AI_PROVIDER_LOCAL = "local"
AI_PROVIDER_OPENAI = "openai"
VALID_AI_PROVIDERS = frozenset({AI_PROVIDER_NONE, AI_PROVIDER_LOCAL, AI_PROVIDER_OPENAI})


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of MoneyFlow configuration."""

    # --- Persistence -------------------------------------------------------
    database_url: str

    # --- Application -------------------------------------------------------
    debug: bool
    currency_symbol: str
    daily_csv_limit: int

    # --- AI provider -------------------------------------------------------
    ai_provider: str
    ai_model: str
    ai_base_url: str
    ai_api_key: str
    ai_timeout: int
    ai_max_tokens: int
    ai_temperature: float

    @property
    def ai_enabled(self) -> bool:
        """True when a non-``none`` AI provider is configured."""
        return self.ai_provider in {AI_PROVIDER_LOCAL, AI_PROVIDER_OPENAI}


def _default_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # Safe default: a local SQLite file so the app runs with zero configuration.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(DATA_DIR / 'moneyflow.db').as_posix()}"


def _normalise_ai_provider() -> str:
    provider = os.getenv("MONEYFLOW_AI_PROVIDER", AI_PROVIDER_NONE).strip().lower()
    if provider not in VALID_AI_PROVIDERS:
        # Unknown value → disable AI rather than crash the app.
        return AI_PROVIDER_NONE
    return provider


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached, validated settings for this process."""
    return Settings(
        database_url=_default_database_url(),
        debug=_env_bool("MONEYFLOW_DEBUG", False),
        currency_symbol=os.getenv("MONEYFLOW_CURRENCY_SYMBOL", "£"),
        daily_csv_limit=_env_int("MONEYFLOW_DAILY_CSV_LIMIT", 10),
        ai_provider=_normalise_ai_provider(),
        ai_model=os.getenv("MONEYFLOW_AI_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
        ai_base_url=os.getenv("MONEYFLOW_AI_BASE_URL", "http://localhost:11434/v1"),
        ai_api_key=os.getenv("MONEYFLOW_AI_API_KEY", ""),
        ai_timeout=_env_int("MONEYFLOW_AI_TIMEOUT", 60),
        ai_max_tokens=_env_int("MONEYFLOW_AI_MAX_TOKENS", 512),
        ai_temperature=_env_float("MONEYFLOW_AI_TEMPERATURE", 0.7),
    )


def reset_settings_cache() -> None:
    """Clear the cached settings (used by tests that patch the environment)."""
    get_settings.cache_clear()
