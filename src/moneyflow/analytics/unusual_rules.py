"""User-configurable unusual transaction rules."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd

DEFAULT_UNUSUAL_RULES: dict[str, Any] = {
    "use_statistical_detection": True,
    "global_expense_threshold": 250.0,
    "category_thresholds": {},
    "flag_new_merchants": False,
    "new_merchant_min_amount": 75.0,
    "flag_keywords": ["atm", "cash", "fee", "crypto", "gambling", "casino"],
    "ignore_keywords": ["salary", "rent"],
    "ignore_categories": ["Transfer"],
}


def get_default_unusual_rules() -> dict[str, Any]:
    return deepcopy(DEFAULT_UNUSUAL_RULES)


def normalise_keyword_list(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = value.split(",")

    return sorted({item.strip().lower() for item in raw_items if item and item.strip()})


def suggest_unusual_rules(
    df: pd.DataFrame, category_totals: dict[str, float]
) -> list[dict[str, Any]]:
    """Suggest useful unusual-transaction rules from the uploaded statement."""
    suggestions: list[dict[str, Any]] = []
    expenses = df[df["Amount"] < 0].copy()

    if expenses.empty:
        return suggestions

    amounts = expenses["Amount"].abs()
    p90 = float(amounts.quantile(0.90))
    p95 = float(amounts.quantile(0.95))

    if p95 >= 50:
        suggestions.append(
            {
                "label": f"Flag expenses above £{p95:.0f}",
                "description": "Useful for spotting large one-off spending without reading every transaction.",
                "updates": {"global_expense_threshold": round(p95, 2)},
            }
        )

    if "Transfer" in category_totals:
        suggestions.append(
            {
                "label": "Ignore transfers",
                "description": "Transfers often move money between accounts and can overwhelm unusual spending results.",
                "updates": {"ignore_categories": ["Transfer"]},
            }
        )

    merchant_counts = expenses["Description"].astype(str).str.lower().value_counts()
    single_merchant_count = int((merchant_counts == 1).sum())
    if single_merchant_count >= 3:
        suggestions.append(
            {
                "label": f"Flag new merchants over £{max(50, p90):.0f}",
                "description": "Highlights bigger transactions at merchants that only appear once in this statement.",
                "updates": {
                    "flag_new_merchants": True,
                    "new_merchant_min_amount": round(max(50, p90), 2),
                },
            }
        )

    risky_keywords = [
        keyword
        for keyword in ["atm", "cash", "fee", "crypto", "gambling", "casino"]
        if expenses["Description"].astype(str).str.lower().str.contains(keyword, regex=False).any()
    ]
    if risky_keywords:
        suggestions.append(
            {
                "label": f"Watch keywords: {', '.join(risky_keywords)}",
                "description": "These words appear in your statement and are often worth reviewing.",
                "updates": {"flag_keywords": risky_keywords},
            }
        )

    return suggestions[:4]
