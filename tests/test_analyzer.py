"""Tests for the deterministic financial analyzer."""

import pandas as pd
import pytest

from moneyflow.analytics.analyzer import FinancialAnalyzer


def _statement() -> pd.DataFrame:
    rows = [
        # Two months of activity with recurring Netflix and a clear outlier.
        ("2025-01-01", "Salary Deposit", 2500.00),
        ("2025-01-03", "Tesco Supermarket", -80.00),
        ("2025-01-05", "Netflix Subscription", -15.99),
        ("2025-01-08", "Uber Ride", -12.00),
        ("2025-01-15", "Starbucks Coffee", -4.50),
        ("2025-01-20", "Tesco Supermarket", -75.00),
        ("2025-01-28", "Laptop Purchase", -1200.00),  # large one-off outlier
        ("2025-02-01", "Salary Deposit", 2500.00),
        ("2025-02-03", "Tesco Supermarket", -82.00),
        ("2025-02-05", "Netflix Subscription", -15.99),
        ("2025-02-09", "Uber Ride", -13.50),
        ("2025-02-16", "Starbucks Coffee", -4.20),
        ("2025-02-25", "Shell Petrol Station", -55.00),
    ]
    df = pd.DataFrame(rows, columns=["Date", "Description", "Amount"])
    df["Date"] = pd.to_datetime(df["Date"])
    df["Type"] = df["Amount"].apply(lambda x: "Income" if x > 0 else "Expense")
    return df


@pytest.fixture
def analyzer() -> FinancialAnalyzer:
    return FinancialAnalyzer(_statement())


def test_summary_stats(analyzer):
    s = analyzer.get_summary_stats()
    assert s["total_income"] == pytest.approx(5000.00)
    assert s["num_income"] == 2
    assert s["num_transactions"] == 13
    assert s["total_expenses"] > 0
    # Net cashflow = income - expenses
    assert s["net_cashflow"] == pytest.approx(s["total_income"] - s["total_expenses"])
    assert s["start_date"] == "2025-01-01"
    assert s["end_date"] == "2025-02-25"


def test_categorisation_keywords(analyzer):
    cats = analyzer.categorize_expenses()["category_totals"]
    # Tesco -> Groceries (two shops), Netflix -> Entertainment, Uber -> Transport
    assert "Groceries" in cats
    assert "Entertainment" in cats
    assert "Transport" in cats
    assert cats["Groceries"] == pytest.approx(80.0 + 75.0 + 82.0)


def test_categorisation_word_boundary_avoids_substring():
    # "Gasoline" must not match the Utilities 'gas' keyword via substring.
    df = pd.DataFrame(
        {"Date": ["2025-01-01"], "Description": ["Gasoline Depot"], "Amount": [-30.0]}
    )
    df["Date"] = pd.to_datetime(df["Date"])
    cats = FinancialAnalyzer(df).categorize_expenses()["category_totals"]
    assert "Utilities" not in cats  # no false 'gas' substring hit


def test_monthly_breakdown(analyzer):
    monthly = analyzer.calculate_monthly_breakdown()
    assert [m["month"] for m in monthly] == ["2025-01", "2025-02"]
    for m in monthly:
        assert m["net"] == pytest.approx(m["income"] - m["expenses"])


def test_budget_recommendations_shape(analyzer):
    recs = analyzer.generate_budget_recommendations()
    assert isinstance(recs, list)
    for r in recs:
        assert {
            "category",
            "current_percentage",
            "recommended_percentage",
            "potential_savings",
        } <= r.keys()


def test_top_merchants_sorted(analyzer):
    top = analyzer.get_top_merchants(limit=5)
    assert top, "expected at least one merchant"
    spends = [m["total_spent"] for m in top]
    assert spends == sorted(spends, reverse=True)
    assert top[0]["merchant"] == "Laptop Purchase"  # biggest single spend


def test_recurring_detects_monthly_netflix(analyzer):
    recurring = analyzer.identify_recurring_transactions()
    names = [r["description"] for r in recurring]
    assert any("Netflix" in n for n in names)


def test_unusual_detects_large_outlier(analyzer):
    unusual = analyzer.detect_unusual_transactions()
    descs = [u["description"] for u in unusual]
    assert any("Laptop" in d for d in descs)


def test_unusual_user_keyword_rule_flags_match():
    df = pd.DataFrame(
        {
            "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "Description": ["Casino Royale", "Tesco", "Tesco"],
            "Amount": [-50.0, -20.0, -22.0],
        }
    )
    df["Date"] = pd.to_datetime(df["Date"])
    rules = {"flag_keywords": ["casino"], "use_statistical_detection": False}
    unusual = FinancialAnalyzer(df).detect_unusual_transactions(rules=rules)
    assert any("Casino" in u["description"] for u in unusual)


def test_empty_expenses_safe():
    df = pd.DataFrame({"Date": ["2025-01-01"], "Description": ["Salary"], "Amount": [1000.0]})
    df["Date"] = pd.to_datetime(df["Date"])
    a = FinancialAnalyzer(df)
    assert a.get_top_merchants() == []
    assert a.generate_budget_recommendations() == []
