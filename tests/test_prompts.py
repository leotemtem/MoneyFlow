"""Tests for the static financial prompt templates."""

import inspect

import pytest

from moneyflow.ai.prompts import FinancialPrompts


def _zero_arg_prompt_methods():
    for name, member in inspect.getmembers(FinancialPrompts, predicate=inspect.isfunction):
        if name.startswith("get_"):
            sig = inspect.signature(member)
            if len(sig.parameters) == 0:  # staticmethods with no args
                yield name, member


@pytest.mark.parametrize("name,method", list(_zero_arg_prompt_methods()))
def test_prompt_returns_nonempty_string(name, method):
    result = method()
    assert isinstance(result, str)
    assert result.strip(), f"{name} returned an empty prompt"


def test_category_deep_dive_includes_category():
    out = FinancialPrompts.get_category_deep_dive_prompt("Groceries")
    assert "Groceries" in out


def test_expected_prompt_helpers_exist():
    for name in (
        "get_overview_prompt",
        "get_budgeting_prompt",
        "get_savings_prompt",
        "get_budget_planner_analysis_prompt",
    ):
        assert callable(getattr(FinancialPrompts, name))
