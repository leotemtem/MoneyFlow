# SPDX-License-Identifier: MIT
"""MoneyFlow — Streamlit application entry point (page routing)."""

import pandas as pd
import streamlit as st

import moneyflow.ui.pages.ai_insights_page as ai_insights_page
import moneyflow.ui.pages.auth_page as auth_page
import moneyflow.ui.pages.budget_planner_page as budget_planner_page
import moneyflow.ui.pages.overview_page as overview_page
import moneyflow.ui.pages.recommendations_page as recommendations_page
import moneyflow.ui.pages.recurring_page as recurring_page
import moneyflow.ui.pages.subscriptions_page as subscriptions_page
import moneyflow.ui.pages.transactions_page as transactions_page
import moneyflow.ui.pages.unusual_page as unusual_page
from moneyflow.state.session_state import init_session_state
from moneyflow.ui.components.landing_page import show_landing_page
from moneyflow.ui.components.sidebar import render_sidebar
from moneyflow.ui.theme import configure_page, inject_theme


def main():
    configure_page()
    inject_theme()
    init_session_state()

    if st.session_state.show_landing and not st.session_state.authenticated:
        show_landing_page()
        return

    if not st.session_state.authenticated:
        auth_page.render()
        return

    render_sidebar()

    if st.session_state.df is None:
        st.markdown(
            """
            <div class="main-header">
                <div class="main-header__eyebrow">Local finance analysis</div>
                <div class="main-header__title">MoneyFlow</div>
                <div class="main-header__subtitle">
                    Upload a bank statement to review cashflow, recurring payments,
                    budget pressure, and AI-assisted insights in one workspace.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="empty-state">
                <h3>No statement loaded</h3>
                <p>Use the sidebar to upload a CSV bank statement. MoneyFlow will parse, categorize, and prepare the dashboard locally.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Example CSV Format")
        example_df = pd.DataFrame(
            {
                "Date": ["2024-01-01", "2024-01-05", "2024-01-10"],
                "Description": ["Salary Deposit", "Tesco Supermarket", "Netflix Subscription"],
                "Amount": [2500.00, -85.50, -12.99],
                "Balance": [2500.00, 2414.50, 2401.51],
            }
        )
        st.dataframe(example_df, width="stretch")
        return

    tx_count = len(st.session_state.df)
    date_min = st.session_state.df["Date"].min().strftime("%d %b %Y")
    date_max = st.session_state.df["Date"].max().strftime("%d %b %Y")
    st.markdown(
        f"""
        <div class="main-header">
            <div class="main-header__eyebrow">Financial workspace</div>
            <div class="main-header__title">MoneyFlow</div>
            <div class="main-header__subtitle">
                {tx_count:,} transactions analysed from {date_min} to {date_max}.
                Review the key movements first, then drill into transactions and recommendations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    overview_page.render_metrics()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        [
            "Overview",
            "Transactions",
            "Budget Planner",
            "Recurring",
            "Budget Recommendations",
            "Unusual",
            "Subscriptions",
            "AI Insights",
        ]
    )

    with tab1:
        overview_page.render()
    with tab2:
        transactions_page.render()
    with tab3:
        budget_planner_page.render()
    with tab4:
        recurring_page.render()
    with tab5:
        recommendations_page.render()
    with tab6:
        unusual_page.render()
    with tab7:
        subscriptions_page.render()
    with tab8:
        ai_insights_page.render()


if __name__ == "__main__":
    main()
