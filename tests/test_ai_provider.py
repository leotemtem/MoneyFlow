"""Tests for the optional AI provider abstraction.

These tests never contact a real model or network endpoint; the HTTP layer is
stubbed so provider behaviour (success, timeout, misconfiguration, disabled) is
exercised deterministically.
"""

import pytest
import requests

from moneyflow.ai import get_ai_provider
from moneyflow.ai.base import (
    AIConfigurationError,
    AIProviderError,
    AIUnavailableError,
)
from moneyflow.ai.openai_compatible import OpenAICompatibleProvider
from moneyflow.ai.prompt_builder import build_context, build_messages
from moneyflow.config.settings import Settings, reset_settings_cache


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_settings_cache()
    yield
    reset_settings_cache()


def _settings(provider="none", **overrides):
    base = dict(
        database_url="sqlite:///:memory:",
        debug=False,
        currency_symbol="£",
        daily_csv_limit=10,
        ai_provider=provider,
        ai_model="test-model",
        ai_base_url="http://localhost:1234/v1",
        ai_api_key="",
        ai_timeout=5,
        ai_max_tokens=128,
        ai_temperature=0.5,
    )
    base.update(overrides)
    return Settings(**base)


SAMPLE_DATA = {
    "summary": {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "date_range_days": 30,
        "num_transactions": 3,
        "num_income": 1,
        "num_expenses": 2,
        "total_income": 2500.0,
        "total_expenses": 100.0,
        "net_cashflow": 2400.0,
    },
    "categories": {"Groceries": 60.0, "Dining": 40.0},
    "recurring": [],
    "monthly": [],
    "recommendations": [],
    "unusual": [],
    "top_merchants": [],
}


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


# --------------------------------------------------------------------------
# Factory / disabled behaviour
# --------------------------------------------------------------------------


def test_factory_returns_none_when_disabled():
    assert get_ai_provider(_settings("none")) is None


def test_factory_returns_openai_provider():
    provider = get_ai_provider(_settings("openai"))
    assert isinstance(provider, OpenAICompatibleProvider)


def test_factory_returns_local_provider_without_loading():
    # Constructing the local provider must not import torch/transformers.
    from moneyflow.ai.local_mistral import LocalMistralProvider

    provider = get_ai_provider(_settings("local"))
    assert isinstance(provider, LocalMistralProvider)
    assert provider.ready is False


# --------------------------------------------------------------------------
# OpenAI-compatible provider
# --------------------------------------------------------------------------


def test_openai_provider_success(monkeypatch):
    provider = OpenAICompatibleProvider(base_url="http://x/v1", api_key="k", model="m")

    def fake_post(url, json, headers, timeout):
        assert "Authorization" in headers  # api key is sent
        return _FakeResponse(200, {"choices": [{"message": {"content": "  hello  "}}]})

    monkeypatch.setattr(requests, "post", fake_post)
    out = provider.generate_insights(SAMPLE_DATA, concise=True)
    assert out == "hello"


def test_openai_provider_timeout_raises_unavailable(monkeypatch):
    provider = OpenAICompatibleProvider(base_url="http://x/v1", model="m")

    def fake_post(*a, **k):
        raise requests.Timeout()

    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(AIUnavailableError):
        provider.generate_insights(SAMPLE_DATA)


def test_openai_provider_connection_error_raises_unavailable(monkeypatch):
    provider = OpenAICompatibleProvider(base_url="http://x/v1", model="m")
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError())
    )
    with pytest.raises(AIUnavailableError):
        provider.generate_insights(SAMPLE_DATA)


def test_openai_provider_http_error_raises_provider_error(monkeypatch):
    provider = OpenAICompatibleProvider(base_url="http://x/v1", model="m")
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResponse(500, {}))
    with pytest.raises(AIProviderError):
        provider.generate_insights(SAMPLE_DATA)


def test_openai_provider_bad_shape_raises_provider_error(monkeypatch):
    provider = OpenAICompatibleProvider(base_url="http://x/v1", model="m")
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResponse(200, {"nope": True}))
    with pytest.raises(AIProviderError):
        provider.generate_insights(SAMPLE_DATA)


def test_openai_provider_missing_config_raises_on_load():
    provider = OpenAICompatibleProvider(base_url="", model="")
    assert provider.is_available() is False
    with pytest.raises(AIConfigurationError):
        provider.load()


def test_error_message_does_not_leak_transaction_data(monkeypatch):
    provider = OpenAICompatibleProvider(base_url="http://x/v1", model="m")
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError())
    )
    try:
        provider.generate_insights(SAMPLE_DATA)
    except AIUnavailableError as exc:
        assert "Groceries" not in str(exc)
        assert "2500" not in str(exc)


# --------------------------------------------------------------------------
# Prompt builder
# --------------------------------------------------------------------------


def test_build_context_includes_key_figures():
    ctx = build_context(SAMPLE_DATA)
    assert "Groceries" in ctx
    assert "2,500.00" in ctx


def test_build_messages_shape():
    messages = build_messages(SAMPLE_DATA, user_query="How am I doing?")
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "How am I doing?" in messages[0]["content"]
