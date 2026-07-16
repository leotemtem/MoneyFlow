"""Tests for environment-driven configuration."""

import pytest

from moneyflow.config import settings as settings_module
from moneyflow.config.settings import get_settings, reset_settings_cache


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_ai_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MONEYFLOW_AI_PROVIDER", raising=False)
    s = get_settings()
    assert s.ai_provider == "none"
    assert s.ai_enabled is False


def test_ai_provider_local(monkeypatch):
    monkeypatch.setenv("MONEYFLOW_AI_PROVIDER", "local")
    s = get_settings()
    assert s.ai_provider == "local"
    assert s.ai_enabled is True


def test_ai_provider_openai_case_insensitive(monkeypatch):
    monkeypatch.setenv("MONEYFLOW_AI_PROVIDER", "OpenAI")
    assert get_settings().ai_provider == "openai"


def test_invalid_ai_provider_falls_back_to_none(monkeypatch):
    monkeypatch.setenv("MONEYFLOW_AI_PROVIDER", "definitely-not-a-provider")
    assert get_settings().ai_provider == "none"


def test_database_url_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_settings().database_url.startswith("sqlite:///")


def test_database_url_respects_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@host:5432/db")
    assert get_settings().database_url == "postgresql://user:pw@host:5432/db"


def test_numeric_env_overrides(monkeypatch):
    monkeypatch.setenv("MONEYFLOW_DAILY_CSV_LIMIT", "3")
    monkeypatch.setenv("MONEYFLOW_AI_TEMPERATURE", "0.1")
    s = get_settings()
    assert s.daily_csv_limit == 3
    assert s.ai_temperature == pytest.approx(0.1)


def test_bad_numeric_env_uses_default(monkeypatch):
    monkeypatch.setenv("MONEYFLOW_DAILY_CSV_LIMIT", "not-a-number")
    assert get_settings().daily_csv_limit == 10


def test_reset_cache_reloads(monkeypatch):
    monkeypatch.setenv("MONEYFLOW_CURRENCY_SYMBOL", "$")
    assert get_settings().currency_symbol == "$"
    reset_settings_cache()
    monkeypatch.setenv("MONEYFLOW_CURRENCY_SYMBOL", "€")
    assert get_settings().currency_symbol == "€"
    assert settings_module.get_settings().currency_symbol == "€"
