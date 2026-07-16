"""
Financial Analyzer
Performs calculations and analysis on bank statement data
"""

import re

import numpy as np
import pandas as pd

from moneyflow.analytics.unusual_rules import get_default_unusual_rules, normalise_keyword_list


class FinancialAnalyzer:
    """Analyze financial data and generate insights"""

    def __init__(self, df):
        """
        Initialize with standardized DataFrame

        Args:
            df: DataFrame with columns [Date, Description, Amount, Type]
        """
        self.df = df.copy()
        self.df["Date"] = pd.to_datetime(self.df["Date"])

    def get_summary_stats(self):
        """Calculate summary statistics"""
        total_income = self.df[self.df["Amount"] > 0]["Amount"].sum()
        total_expenses = abs(self.df[self.df["Amount"] < 0]["Amount"].sum())
        net_cashflow = total_income - total_expenses

        avg_income = self.df[self.df["Amount"] > 0]["Amount"].mean()
        avg_expense = abs(self.df[self.df["Amount"] < 0]["Amount"].mean())

        num_transactions = len(self.df)
        num_income = len(self.df[self.df["Amount"] > 0])
        num_expenses = len(self.df[self.df["Amount"] < 0])

        date_range = (self.df["Date"].max() - self.df["Date"].min()).days

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_cashflow": round(net_cashflow, 2),
            "avg_income": round(avg_income, 2) if not pd.isna(avg_income) else 0,
            "avg_expense": round(avg_expense, 2) if not pd.isna(avg_expense) else 0,
            "num_transactions": num_transactions,
            "num_income": num_income,
            "num_expenses": num_expenses,
            "date_range_days": date_range,
            "start_date": self.df["Date"].min().strftime("%Y-%m-%d"),
            "end_date": self.df["Date"].max().strftime("%Y-%m-%d"),
        }

    def categorize_expenses(self):
        """Categorize expenses based on description keywords"""
        categories = {
            "Groceries": [
                "grocery",
                "supermarket",
                "tesco",
                "sainsbury",
                "asda",
                "aldi",
                "lidl",
                "morrisons",
                "waitrose",
                "whole foods",
                "trader joe",
            ],
            "Dining": [
                "restaurant",
                "cafe",
                "coffee",
                "starbucks",
                "mcdonald",
                "kfc",
                "pizza",
                "burger",
                "food",
                "dining",
                "takeaway",
                "delivery",
            ],
            "Transport": [
                "uber",
                "lyft",
                "taxi",
                "train",
                "bus",
                "metro",
                "subway",
                "transport",
                "fuel",
                "gas",
                "petrol",
                "parking",
                "tfl",
            ],
            "Shopping": [
                "amazon",
                "ebay",
                "shop",
                "store",
                "retail",
                "clothing",
                "fashion",
                "zara",
                "h&m",
                "nike",
                "adidas",
            ],
            "Utilities": [
                "electric",
                "gas",
                "water",
                "internet",
                "phone",
                "mobile",
                "broadband",
                "utility",
                "council tax",
            ],
            "Entertainment": [
                "netflix",
                "spotify",
                "cinema",
                "theatre",
                "gym",
                "fitness",
                "subscription",
                "gaming",
                "steam",
                "playstation",
                "xbox",
            ],
            "Healthcare": [
                "pharmacy",
                "doctor",
                "hospital",
                "medical",
                "health",
                "dental",
                "optician",
                "insurance",
            ],
            "Transfer": ["transfer", "payment", "sent", "paypal", "venmo", "withdrawal"],
            "Other": [],
        }

        expenses_df = self.df[self.df["Amount"] < 0].copy()
        expenses_df["Category"] = "Other"

        for idx, row in expenses_df.iterrows():
            desc_lower = str(row["Description"]).lower()

            for category, keywords in categories.items():
                if category == "Other":
                    continue
                if any(
                    re.search(r"\b" + re.escape(keyword) + r"\b", desc_lower)
                    for keyword in keywords
                ):
                    expenses_df.at[idx, "Category"] = category
                    break

        # Calculate category totals
        category_totals = (
            expenses_df.groupby("Category")["Amount"]
            .apply(lambda x: abs(x.sum()))
            .sort_values(ascending=False)
        )

        return {
            "expenses_df": expenses_df,
            "category_totals": category_totals.to_dict(),
            "category_counts": expenses_df["Category"].value_counts().to_dict(),
        }

    def identify_recurring_transactions(self, similarity_threshold=0.7):
        """Identify recurring transactions (subscriptions, bills)"""
        # Group by similar descriptions
        recurring = []

        expenses_df = self.df[self.df["Amount"] < 0].copy()

        # Group by rounded amounts and similar descriptions
        for desc in expenses_df["Description"].unique():
            similar_transactions = expenses_df[
                expenses_df["Description"].str.contains(
                    desc[:15], case=False, na=False, regex=False
                )
            ]

            if len(similar_transactions) >= 2:
                # Check if transactions occur regularly
                dates = similar_transactions["Date"].sort_values()
                if len(dates) >= 2:
                    intervals = [
                        (dates.iloc[i + 1] - dates.iloc[i]).days for i in range(len(dates) - 1)
                    ]
                    avg_interval = np.mean(intervals)

                    # If average interval is roughly monthly (20-40 days)
                    if 20 <= avg_interval <= 40:
                        recurring.append(
                            {
                                "description": desc,
                                "avg_amount": abs(similar_transactions["Amount"].mean()),
                                "frequency": len(similar_transactions),
                                "avg_interval_days": round(avg_interval, 1),
                                "total_spent": abs(similar_transactions["Amount"].sum()),
                            }
                        )

        return sorted(recurring, key=lambda x: x["total_spent"], reverse=True)

    def calculate_monthly_breakdown(self):
        """Calculate monthly income and expenses"""
        df_copy = self.df.copy()
        df_copy["Month"] = df_copy["Date"].dt.to_period("M")

        monthly_data = []

        for month in df_copy["Month"].unique():
            month_df = df_copy[df_copy["Month"] == month]

            income = month_df[month_df["Amount"] > 0]["Amount"].sum()
            expenses = abs(month_df[month_df["Amount"] < 0]["Amount"].sum())

            monthly_data.append(
                {
                    "month": str(month),
                    "income": round(income, 2),
                    "expenses": round(expenses, 2),
                    "net": round(income - expenses, 2),
                }
            )

        return sorted(monthly_data, key=lambda x: x["month"])

    def generate_budget_recommendations(self):
        """Generate budget recommendations based on spending patterns"""
        summary = self.get_summary_stats()
        categories = self.categorize_expenses()

        total_expenses = summary["total_expenses"]
        category_totals = categories["category_totals"]

        recommendations = []

        # Recommended budget percentages (50/30/20 rule adapted)
        recommended_percentages = {
            "Groceries": 15,
            "Utilities": 10,
            "Transport": 10,
            "Dining": 5,
            "Entertainment": 5,
            "Shopping": 10,
            "Healthcare": 5,
            "Transfer": 0,
            "Other": 10,
        }

        for category, spent in category_totals.items():
            percentage = (spent / total_expenses * 100) if total_expenses > 0 else 0
            recommended_pct = recommended_percentages.get(category, 10)

            # Skip Transfer category with 0% recommended (no meaningful threshold)
            if recommended_pct == 0:
                continue

            if percentage > recommended_pct * 1.2:  # Spending >20% more than recommended
                severity = "high" if percentage > recommended_pct * 1.5 else "medium"
                recommendations.append(
                    {
                        "category": category,
                        "current_spending": round(spent, 2),
                        "current_percentage": round(percentage, 1),
                        "recommended_percentage": recommended_pct,
                        "potential_savings": round(
                            spent - (total_expenses * recommended_pct / 100), 2
                        ),
                        "severity": severity,
                    }
                )

        return sorted(recommendations, key=lambda x: x["potential_savings"], reverse=True)

    def detect_unusual_transactions(self, std_threshold=2.0, rules=None):
        """
        Detect unusual/outlier transactions using multiple detection methods:
        1. Category-aware detection (compare within same spending category)
        2. Merchant-specific detection (unusual for that specific merchant)
        3. Global outlier detection (across all transactions)
        4. Frequency-based detection (rare large transactions)
        """
        active_rules = get_default_unusual_rules()
        if rules:
            active_rules.update(rules)

        unusual = []
        seen_transactions = set()  # To avoid duplicates

        # Get categorized expenses for category-aware detection
        categories_data = self.categorize_expenses()
        expenses_with_categories = categories_data["expenses_df"]

        # Method 1: Category-aware detection for expenses
        for category in expenses_with_categories["Category"].unique():
            category_subset = expenses_with_categories[
                expenses_with_categories["Category"] == category
            ].copy()

            if len(category_subset) < 3:
                continue

            amounts = category_subset["Amount"].abs()
            mean_amt = amounts.mean()
            std_amt = amounts.std()

            # Use IQR method if standard deviation is too small
            if std_amt < 1.0:
                q75 = amounts.quantile(0.75)
                iqr = amounts.quantile(0.75) - amounts.quantile(0.25)
                if iqr > 0:
                    threshold_amount = q75 + 2.0 * iqr
                    unusual_mask = amounts > threshold_amount
                else:
                    continue
            else:
                z_scores = (amounts - mean_amt) / std_amt
                unusual_mask = z_scores > std_threshold

            for idx, row in category_subset[unusual_mask].iterrows():
                amount = abs(row["Amount"])
                z_score = abs((amount - mean_amt) / std_amt) if std_amt > 0 else 0

                # Calculate how much higher than category average
                pct_above_avg = ((amount - mean_amt) / mean_amt * 100) if mean_amt > 0 else 0

                tx_key = (row["Date"].strftime("%Y-%m-%d"), row["Description"], amount)
                if tx_key not in seen_transactions:
                    seen_transactions.add(tx_key)
                    unusual.append(
                        {
                            "date": row["Date"].strftime("%Y-%m-%d"),
                            "description": row["Description"],
                            "amount": round(amount, 2),
                            "category": category,
                            "z_score": round(z_score, 2),
                            "type": "expense",
                            "reason": f"{round(pct_above_avg)}% above average {category} spending (avg: £{mean_amt:.2f})",
                            "severity": "high" if z_score > 3.0 else "medium",
                        }
                    )

        # Method 2: Merchant-specific detection (recurring merchants with unusual amounts)
        expenses_df = self.df[self.df["Amount"] < 0].copy()
        merchant_groups = expenses_df.groupby("Description")

        for merchant, merchant_df in merchant_groups:
            if len(merchant_df) >= 2:  # At least 2 transactions from same merchant
                amounts = merchant_df["Amount"].abs()
                mean_amt = amounts.mean()
                std_amt = amounts.std()

                if std_amt > 0:
                    for idx, row in merchant_df.iterrows():
                        amount = abs(row["Amount"])
                        z_score = abs((amount - mean_amt) / std_amt)

                        if z_score > 2.5:  # Stricter threshold for merchant-specific
                            pct_above_avg = (
                                ((amount - mean_amt) / mean_amt * 100) if mean_amt > 0 else 0
                            )
                            tx_key = (row["Date"].strftime("%Y-%m-%d"), row["Description"], amount)

                            if tx_key not in seen_transactions:
                                seen_transactions.add(tx_key)
                                unusual.append(
                                    {
                                        "date": row["Date"].strftime("%Y-%m-%d"),
                                        "description": row["Description"],
                                        "amount": round(amount, 2),
                                        "category": "N/A",
                                        "z_score": round(z_score, 2),
                                        "type": "expense",
                                        "reason": f"{round(pct_above_avg)}% higher than usual for this merchant (usually £{mean_amt:.2f})",
                                        "severity": "high" if z_score > 4.0 else "medium",
                                    }
                                )

        # Method 3: Global outlier detection for income
        income_subset = self.df[self.df["Amount"] > 0].copy()
        if len(income_subset) >= 3:
            amounts = income_subset["Amount"].abs()
            mean_amt = amounts.mean()
            std_amt = amounts.std()

            if std_amt < 1.0:
                q75 = amounts.quantile(0.75)
                iqr = amounts.quantile(0.75) - amounts.quantile(0.25)
                if iqr > 0:
                    threshold_amount = q75 + 2.0 * iqr
                    unusual_mask = amounts > threshold_amount
                else:
                    unusual_mask = pd.Series([False] * len(amounts))
            else:
                z_scores = (amounts - mean_amt) / std_amt
                unusual_mask = z_scores > std_threshold

            for idx, row in income_subset[unusual_mask].iterrows():
                amount = abs(row["Amount"])
                z_score = abs((amount - mean_amt) / std_amt) if std_amt > 0 else 0
                pct_above_avg = ((amount - mean_amt) / mean_amt * 100) if mean_amt > 0 else 0

                tx_key = (row["Date"].strftime("%Y-%m-%d"), row["Description"], amount)
                if tx_key not in seen_transactions:
                    seen_transactions.add(tx_key)
                    unusual.append(
                        {
                            "date": row["Date"].strftime("%Y-%m-%d"),
                            "description": row["Description"],
                            "amount": round(amount, 2),
                            "category": "Income",
                            "z_score": round(z_score, 2),
                            "type": "income",
                            "reason": f"{round(pct_above_avg)}% above average income (avg: £{mean_amt:.2f})",
                            "severity": "high" if z_score > 3.0 else "medium",
                        }
                    )

        # Method 4: Large one-off transactions (infrequent amounts)
        all_expenses = self.df[self.df["Amount"] < 0].copy()
        if len(all_expenses) > 0:
            # Find large transactions that occur infrequently
            amount_rounded = all_expenses["Amount"].abs().round(-1)  # Round to nearest 10
            amount_counts = amount_rounded.value_counts()

            # Identify amounts that appear only 1-2 times and are in top 10% by value
            top_10_pct = all_expenses["Amount"].abs().quantile(0.90)

            for idx, row in all_expenses.iterrows():
                amount = abs(row["Amount"])
                amount_round = round(amount, -1) if amount >= 10 else amount

                if amount >= top_10_pct and amount_counts.get(amount_round, 0) <= 2:
                    tx_key = (row["Date"].strftime("%Y-%m-%d"), row["Description"], amount)

                    if (
                        tx_key not in seen_transactions and amount >= 100
                    ):  # Only for significant amounts
                        seen_transactions.add(tx_key)
                        unusual.append(
                            {
                                "date": row["Date"].strftime("%Y-%m-%d"),
                                "description": row["Description"],
                                "amount": round(amount, 2),
                                "category": "N/A",
                                "z_score": 0,
                                "type": "expense",
                                "reason": "Rare large expense - in top 10% of spending",
                                "severity": "medium" if amount < 500 else "high",
                            }
                        )

        if not active_rules.get("use_statistical_detection", True):
            unusual = []
            seen_transactions = set()

        # Method 5: User-defined rules
        ignore_keywords = normalise_keyword_list(active_rules.get("ignore_keywords", []))
        flag_keywords = normalise_keyword_list(active_rules.get("flag_keywords", []))
        ignore_categories = set(active_rules.get("ignore_categories", []))
        category_thresholds = active_rules.get("category_thresholds", {}) or {}
        global_threshold = float(active_rules.get("global_expense_threshold") or 0)
        flag_new_merchants = bool(active_rules.get("flag_new_merchants"))
        new_merchant_min_amount = float(active_rules.get("new_merchant_min_amount") or 0)

        expenses_with_categories = self.categorize_expenses()["expenses_df"]
        merchant_counts = (
            expenses_with_categories["Description"].astype(str).str.lower().value_counts()
        )

        def is_ignored(row):
            desc = str(row["Description"]).lower()
            if row.get("Category") in ignore_categories:
                return True
            return any(keyword in desc for keyword in ignore_keywords)

        def add_user_flag(row, amount, reason, severity="medium", rule_name="User rule"):
            tx_key = (row["Date"].strftime("%Y-%m-%d"), row["Description"], amount)
            if tx_key in seen_transactions:
                for trans in unusual:
                    existing_key = (trans["date"], trans["description"], trans["amount"])
                    if existing_key == tx_key and reason not in trans.get("reason", ""):
                        trans["reason"] = f"{trans.get('reason', '')}; {reason}"
                        trans["rule_source"] = trans.get("rule_source", "Automatic + user rule")
                return

            seen_transactions.add(tx_key)
            unusual.append(
                {
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "description": row["Description"],
                    "amount": round(amount, 2),
                    "category": row.get("Category", "N/A"),
                    "z_score": 0,
                    "type": "expense",
                    "reason": reason,
                    "severity": severity,
                    "rule_source": rule_name,
                }
            )

        for _, row in expenses_with_categories.iterrows():
            if is_ignored(row):
                continue

            amount = abs(row["Amount"])
            desc = str(row["Description"]).lower()
            category = row.get("Category", "Other")

            if global_threshold and amount >= global_threshold:
                severity = "high" if amount >= global_threshold * 2 else "medium"
                add_user_flag(
                    row,
                    amount,
                    f"Matches your rule: expenses over £{global_threshold:.2f}",
                    severity,
                    "User amount rule",
                )

            category_threshold = category_thresholds.get(category)
            if category_threshold and amount >= float(category_threshold):
                severity = "high" if amount >= float(category_threshold) * 2 else "medium"
                add_user_flag(
                    row,
                    amount,
                    f"Matches your rule: {category} over £{float(category_threshold):.2f}",
                    severity,
                    "User category rule",
                )

            matched_keywords = [keyword for keyword in flag_keywords if keyword in desc]
            if matched_keywords:
                add_user_flag(
                    row,
                    amount,
                    f"Matches your watched keyword: {', '.join(matched_keywords)}",
                    "medium",
                    "User keyword rule",
                )

            if flag_new_merchants and amount >= new_merchant_min_amount:
                merchant_key = desc
                if merchant_counts.get(merchant_key, 0) == 1:
                    add_user_flag(
                        row,
                        amount,
                        f"Merchant appears once in this statement and amount is over £{new_merchant_min_amount:.2f}",
                        "medium",
                        "User new merchant rule",
                    )

        return sorted(unusual, key=lambda x: x["amount"], reverse=True)

    def get_top_merchants(self, limit=10):
        """
        Get top merchants/vendors by total spending
        Returns merchant names and spending patterns from CSV descriptions
        """
        expenses_df = self.df[self.df["Amount"] < 0].copy()

        if len(expenses_df) == 0:
            return []

        # Group by description (merchant name)
        merchant_stats = (
            expenses_df.groupby("Description")
            .agg({"Amount": ["sum", "count", "mean"]})
            .reset_index()
        )

        merchant_stats.columns = ["merchant", "total_spent", "transaction_count", "avg_amount"]
        merchant_stats["total_spent"] = merchant_stats["total_spent"].abs()
        merchant_stats["avg_amount"] = merchant_stats["avg_amount"].abs()

        # Sort by total spent
        merchant_stats = merchant_stats.sort_values("total_spent", ascending=False).head(limit)

        top_merchants = []
        for _, row in merchant_stats.iterrows():
            top_merchants.append(
                {
                    "merchant": row["merchant"],
                    "total_spent": round(row["total_spent"], 2),
                    "transaction_count": int(row["transaction_count"]),
                    "avg_amount": round(row["avg_amount"], 2),
                }
            )

        return top_merchants
