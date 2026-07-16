import pandas as pd

from moneyflow.analytics.analyzer import FinancialAnalyzer
from moneyflow.analytics.unusual_rules import get_default_unusual_rules, suggest_unusual_rules


def _df():
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(
                [
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-03",
                    "2026-01-04",
                ]
            ),
            "Description": [
                "Salary",
                "Tesco Supermarket",
                "Crypto Exchange",
                "Bank Transfer",
            ],
            "Amount": [2500.0, -40.0, -350.0, -500.0],
        }
    )


def test_user_amount_rule_flags_large_expense():
    rules = get_default_unusual_rules()
    rules.update(
        {
            "use_statistical_detection": False,
            "global_expense_threshold": 300.0,
            "ignore_categories": [],
            "ignore_keywords": [],
            "flag_keywords": [],
        }
    )

    unusual = FinancialAnalyzer(_df()).detect_unusual_transactions(rules=rules)

    descriptions = {item["description"] for item in unusual}
    assert "Crypto Exchange" in descriptions
    assert "Bank Transfer" in descriptions


def test_ignore_category_removes_transfer_flags():
    rules = get_default_unusual_rules()
    rules.update(
        {
            "use_statistical_detection": False,
            "global_expense_threshold": 300.0,
            "ignore_categories": ["Transfer"],
            "ignore_keywords": [],
            "flag_keywords": [],
        }
    )

    unusual = FinancialAnalyzer(_df()).detect_unusual_transactions(rules=rules)

    descriptions = {item["description"] for item in unusual}
    assert "Crypto Exchange" in descriptions
    assert "Bank Transfer" not in descriptions


def test_keyword_rule_flags_matching_description():
    rules = get_default_unusual_rules()
    rules.update(
        {
            "use_statistical_detection": False,
            "global_expense_threshold": 0.0,
            "ignore_categories": [],
            "ignore_keywords": [],
            "flag_keywords": ["crypto"],
        }
    )

    unusual = FinancialAnalyzer(_df()).detect_unusual_transactions(rules=rules)

    assert [item["description"] for item in unusual] == ["Crypto Exchange"]
    assert "crypto" in unusual[0]["reason"].lower()


def test_suggest_unusual_rules_returns_actionable_updates():
    analyzer = FinancialAnalyzer(_df())
    categories = analyzer.categorize_expenses()["category_totals"]

    suggestions = suggest_unusual_rules(_df(), categories)

    assert suggestions
    assert all("label" in suggestion for suggestion in suggestions)
    assert all("updates" in suggestion for suggestion in suggestions)
