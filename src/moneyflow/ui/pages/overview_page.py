import streamlit as st

from moneyflow.ui.components.charts import (
    display_category_chart,
    display_daily_spending_heatmap,
    display_monthly_trend,
    display_running_balance_chart,
)


def render_metrics():
    if not st.session_state.financial_data:
        return

    summary = st.session_state.financial_data["summary"]
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Income", value=f"£{summary['total_income']:,.2f}")
    with col2:
        st.metric(label="Total Expenses", value=f"£{summary['total_expenses']:,.2f}")
    with col3:
        net_cf = summary["net_cashflow"]
        st.metric(
            label="Net Cashflow",
            value=f"£{net_cf:,.2f}",
            delta=f"{'Surplus' if net_cf > 0 else 'Deficit'}",
        )
    with col4:
        st.metric(label="Period", value=f"{summary['date_range_days']} days")


def render():
    st.subheader("Dashboard Overview")

    col1, col2 = st.columns(2)
    with col1:
        display_category_chart()
    with col2:
        display_monthly_trend()

    st.markdown("---")
    st.subheader("Spending Rhythm")
    display_daily_spending_heatmap()

    st.markdown("---")
    st.subheader("Balance Movement")
    display_running_balance_chart()

    st.subheader("Recent Transactions")
    display_df = st.session_state.df.head(20).copy()
    display_df["Amount"] = display_df["Amount"].apply(lambda x: f"£{x:.2f}")
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_df, width="stretch")
