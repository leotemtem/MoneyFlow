"""Integration coverage for a realistic statement-processing workflow."""

from __future__ import annotations

import io

import pytest

pytestmark = pytest.mark.integration

from moneyflow.analytics.analyzer import FinancialAnalyzer
from moneyflow.analytics.subscriptions import SubscriptionManager
from moneyflow.parsing.csv_parser import CSVParser


def test_uploaded_statement_can_be_parsed_analyzed_and_persisted(tmp_db):
    csv_data = io.StringIO(
        "\n".join(
            [
                "Date,Description,Amount,Balance",
                "2026-01-01,Salary,2500.00,2500.00",
                "2026-01-05,Tesco Supermarket,-85.50,2414.50",
                "2026-01-10,Netflix Monthly,-15.99,2398.51",
                "2026-02-01,Salary,2500.00,4898.51",
                "2026-02-10,Netflix Monthly,-15.99,4882.52",
                "2026-03-01,Salary,2500.00,7382.52",
                "2026-03-10,Netflix Monthly,-15.99,7366.53",
            ]
        )
    )

    parsed = CSVParser().parse_csv(csv_data)
    analyzer = FinancialAnalyzer(parsed)
    summary = analyzer.get_summary_stats()
    categories = analyzer.categorize_expenses()["category_totals"]
    subscriptions = SubscriptionManager(parsed).detect_subscriptions()

    tmp_db.register_user("workflow_user", "pass123")
    transactions_saved, _ = tmp_db.save_transactions("workflow_user", parsed)
    subscriptions_saved, _ = tmp_db.save_subscriptions("workflow_user", subscriptions)

    assert summary["total_income"] == pytest.approx(7500.00)
    assert summary["total_expenses"] == pytest.approx(133.47)
    assert categories["Groceries"] == pytest.approx(85.50)
    assert categories["Entertainment"] == pytest.approx(47.97)
    assert [sub["name"] for sub in subscriptions] == ["Netflix"]
    assert transactions_saved
    assert subscriptions_saved
    assert tmp_db.get_transaction_count("workflow_user") == len(parsed)
    assert tmp_db.get_subscription_count("workflow_user") == 1
