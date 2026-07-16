import pandas as pd
import streamlit as st


def render():
    if not st.session_state.financial_data:
        st.warning("No financial data loaded. Please upload a bank statement first.")
        return

    recurring = st.session_state.financial_data["recurring"]

    if recurring:
        st.subheader("Recurring Transactions")
        st.caption(
            "Likely subscriptions and regular bills detected from repeated statement patterns."
        )

        df_recurring = pd.DataFrame(recurring)
        df_recurring = df_recurring[
            ["description", "avg_amount", "frequency", "avg_interval_days", "total_spent"]
        ]
        df_recurring.columns = [
            "Description",
            "Avg Amount (£)",
            "Frequency",
            "Avg Days Between",
            "Total Spent (£)",
        ]

        st.dataframe(
            df_recurring.style.format(
                {
                    "Avg Amount (£)": "£{:.2f}",
                    "Avg Days Between": "{:.1f}",
                    "Total Spent (£)": "£{:.2f}",
                }
            ),
            width="stretch",
        )

        total_recurring = sum(r["total_spent"] for r in recurring)
        st.metric("Total Recurring Spend", f"£{total_recurring:,.2f}")
    else:
        st.info("No recurring transactions detected in this statement.")
