# SPDX-License-Identifier: MIT
"""Build provider-agnostic prompts from the deterministic financial summary.

The financial figures themselves are always computed deterministically by
:mod:`moneyflow.analytics`; these helpers only format that summary into text
for a language model. The same context feeds both the local-model flat prompt
and the OpenAI-compatible chat messages.
"""

from __future__ import annotations

from typing import Any

from moneyflow.config.settings import get_settings


def build_context(financial_data: dict[str, Any]) -> str:
    """Format the analytics summary into a compact textual context block."""
    cur = get_settings().currency_symbol

    summary = financial_data.get("summary", {})
    categories = financial_data.get("categories", {})
    recurring = financial_data.get("recurring", [])
    monthly = financial_data.get("monthly", [])
    recommendations = financial_data.get("recommendations", [])
    unusual = financial_data.get("unusual", [])
    top_merchants = financial_data.get("top_merchants", [])

    context = f"""Transaction Data Analysis:
Period: {summary.get("start_date", "N/A")} to {summary.get("end_date", "N/A")} ({summary.get("date_range_days", 0)} days)
Total Transactions: {summary.get("num_transactions", 0)}
- Income Transactions: {summary.get("num_income", 0)} totaling {cur}{summary.get("total_income", 0):,.2f}
- Expense Transactions: {summary.get("num_expenses", 0)} totaling {cur}{summary.get("total_expenses", 0):,.2f}
- Net Cashflow: {cur}{summary.get("net_cashflow", 0):,.2f}"""

    if summary.get("date_range_days", 0) > 0:
        daily = summary.get("total_expenses", 0) / summary.get("date_range_days", 1)
        context += f"\n- Average Daily Spending: {cur}{daily:.2f}"
        context += f"\n- Average Weekly Spending: {cur}{daily * 7:.2f}"

    context += "\n\nExpense Breakdown by Detected Category:\n"
    total_expenses = summary.get("total_expenses", 1)
    for category, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        pct = (amount / total_expenses * 100) if total_expenses > 0 else 0
        context += f"- {category}: {cur}{amount:,.2f} ({pct:.1f}% of total)\n"

    if top_merchants:
        context += "\nTop Merchants (by total spending):\n"
        for idx, merchant in enumerate(top_merchants[:10], 1):
            context += (
                f"{idx}. '{merchant['merchant']}' - {cur}{merchant['total_spent']:.2f} "
                f"({merchant['transaction_count']} transactions, avg {cur}{merchant['avg_amount']:.2f})\n"
            )

    if recurring:
        context += "\nRecurring Transactions Identified:\n"
        for idx, item in enumerate(recurring[:8], 1):
            context += (
                f"{idx}. '{item['description']}' - {cur}{item['avg_amount']:.2f} every "
                f"~{item['avg_interval_days']} days (appears {item['frequency']} times, "
                f"total: {cur}{item['total_spent']:.2f})\n"
            )
        total_recurring = sum(item["total_spent"] for item in recurring[:8])
        context += f"-> Top recurring transactions account for {cur}{total_recurring:.2f}\n"

    if unusual:
        context += "\nUnusual Transactions Detected:\n"
        high_priority = [u for u in unusual if u.get("severity") == "high"][:5]
        medium_priority = [u for u in unusual if u.get("severity") == "medium"][:3]
        for label, group in (
            ("High Priority", high_priority),
            ("Medium Priority", medium_priority),
        ):
            if not group:
                continue
            context += f"{label}:\n"
            for trans in group:
                context += (
                    f"- {trans['date']}: '{trans['description']}' - {cur}{trans['amount']:.2f}"
                )
                context += f" ({trans.get('reason') or trans.get('type', 'expense')})\n"

    if recommendations:
        context += "\nBudget Analysis:\n"
        for rec in recommendations[:5]:
            context += (
                f"- {rec['category']}: Spending {rec['current_percentage']:.1f}% "
                f"(recommended: {rec['recommended_percentage']}%) - "
                f"Potential monthly savings: {cur}{rec['potential_savings']:.2f}\n"
            )

    if monthly and len(monthly) > 1:
        context += "\nMonthly Trend:\n"
        for month_data in monthly[-3:]:
            context += (
                f"- {month_data['month']}: Income {cur}{month_data['income']:,.2f}, "
                f"Expenses {cur}{month_data['expenses']:,.2f}, Net: {cur}{month_data['net']:,.2f}\n"
            )
        if len(monthly) >= 2:
            trend = "improving" if monthly[-1]["net"] > monthly[-2]["net"] else "declining"
            context += f"-> Cashflow trend: {trend}\n"

    return context


def build_instruction(user_query: str | None = None, concise: bool = False) -> str:
    """Build the system/task instruction for the model."""
    if user_query:
        style = (
            """
Response style:
- Keep the answer clear and skimmable
- Use at most 5 bullets
- Put the most important action first
- Avoid technical finance/statistics terms; explain any in everyday language
- Do not include introductions or long explanations"""
            if concise
            else """
Response style:
- Be clear, practical, and data-driven
- Use headings or bullets where useful
- Avoid technical jargon and generic advice"""
        )
        return f"""You are a helpful financial analysis assistant reviewing a summary of a user's bank transactions. Answer the following question using specific details from the data provided:

{user_query}

Guidance:
- Reference actual merchant names, categories, dates and amounts from the data
- Give practical, actionable observations based on the spending patterns shown
- This is informational only and is not regulated financial advice
{style}"""

    if concise:
        return """You are a helpful financial analysis assistant. Give a short, friendly snapshot of the user's finances using the data provided.

Format exactly:
**Snapshot:** one sentence.

**What stands out**
- 3 bullets maximum

**Do next**
- 2 bullets maximum

Keep it easy to read, use plain language, and only include useful specific numbers. This is informational only and not regulated financial advice."""

    return """You are a helpful financial analysis assistant. Provide a clear, data-driven analysis using specific details from the summary provided:

1. Financial Health Overview: reference the actual cashflow numbers and trends
2. Spending Pattern Insights: mention specific merchants, categories and descriptions
3. Top Spending Areas: where most money goes, with vendor names
4. Unusual Transactions: explain why flagged items stand out
5. Recurring Costs: identify subscriptions/bills and possible optimisations
6. Budget Recommendations: category-specific, based on actual spending
7. Actionable Next Steps: concrete actions from the data

Be specific, not generic. This is informational only and not regulated financial advice."""


def build_messages(
    financial_data: dict[str, Any],
    user_query: str | None = None,
    concise: bool = False,
) -> list[dict[str, str]]:
    """Build OpenAI-style chat messages (system instruction + data context)."""
    return [
        {"role": "system", "content": build_instruction(user_query, concise)},
        {"role": "user", "content": build_context(financial_data)},
    ]


def build_flat_prompt(
    financial_data: dict[str, Any],
    user_query: str | None = None,
    concise: bool = False,
) -> str:
    """Build a single instruction-format prompt for local instruct models."""
    instruction = build_instruction(user_query, concise)
    context = build_context(financial_data)
    return f"<s>[INST] {instruction}\n\n{context}\n[/INST]"
