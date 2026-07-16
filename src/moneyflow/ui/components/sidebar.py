# SPDX-License-Identifier: MIT
"""Application sidebar: account menu, AI toggle, upload, and saved data."""

import logging
from datetime import datetime

import streamlit as st

from moneyflow.analytics.analyzer import FinancialAnalyzer
from moneyflow.analytics.unusual_rules import get_default_unusual_rules
from moneyflow.services.file_processor import build_financial_data, process_uploaded_file
from moneyflow.services.llm_service import enable_ai
from moneyflow.ui.components.logo_animation import render_logo_animation

logger = logging.getLogger(__name__)


def render_sidebar():
    """Render the application sidebar."""

    with st.sidebar:
        render_logo_animation(height=150, compact=True)
        st.markdown("## MoneyFlow")
        st.caption("Private statement analysis")

        show_user_menu()

        st.markdown("---")

        # AI provider (optional)
        st.markdown("### AI Insights")
        provider = st.session_state.get("ai_provider")
        if provider is None:
            st.caption(
                "AI is disabled. Set MONEYFLOW_AI_PROVIDER to 'local' or 'openai' to enable "
                "optional AI insights."
            )
        elif not st.session_state.llm_loaded:
            st.caption(f"{provider.name} is optional for generated advice.")
            if st.button("Enable AI insights", width="stretch"):
                enable_ai()
        else:
            st.success(f"{provider.name} ready")

        st.markdown("---")

        # File upload
        st.markdown("### Bank Statement")
        uploaded_file = st.file_uploader(
            "CSV statement",
            type=["csv"],
            help="Upload your bank statement in CSV format",
        )

        if uploaded_file is not None:
            st.caption(uploaded_file.name)
            allowed, used, limit = st.session_state.db_handler.check_upload_rate_limit(
                st.session_state.username
            )
            if not allowed:
                st.warning(f"Daily limit reached ({limit} analyses per day). Try again tomorrow.")
            else:
                remaining = limit - used
                if st.button("Process Statement", type="primary", width="stretch"):
                    if process_uploaded_file(uploaded_file):
                        st.session_state.db_handler.record_csv_upload(st.session_state.username)
                        st.success(
                            f"Statement processed ({remaining - 1} analyses remaining today)"
                        )

        # Database operations
        if st.session_state.df is not None:
            st.markdown("---")
            st.markdown("### Saved Data")

            if st.button("Save to Database", width="stretch"):
                success, msg = st.session_state.db_handler.save_transactions(
                    st.session_state.username,
                    st.session_state.df,
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

            if st.button("Load from Database", width="stretch"):
                df = st.session_state.db_handler.get_user_transactions(st.session_state.username)
                if not df.empty:
                    st.session_state.df = df
                    st.session_state.analyzer = FinancialAnalyzer(df)
                    st.session_state.financial_data = build_financial_data(
                        st.session_state.analyzer,
                        st.session_state.get("unusual_rules", get_default_unusual_rules()),
                    )
                    st.success(f"Loaded {len(df)} transactions from database")
                    st.rerun()
                else:
                    st.info("No transactions found in database")

            tx_count = st.session_state.db_handler.get_transaction_count(st.session_state.username)
            st.metric("Saved Transactions", tx_count)


def show_user_menu():
    """Display user menu in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Account")
    st.sidebar.markdown(f"**{st.session_state.username}**")

    user_info = st.session_state.auth_handler.get_user_info(st.session_state.username)
    if user_info.get("last_login"):
        try:
            last_login = datetime.fromisoformat(user_info["last_login"])
            st.sidebar.caption(f"Last login: {last_login.strftime('%Y-%m-%d %H:%M')}")
        except (ValueError, TypeError):
            logger.debug("Could not parse last_login timestamp for display")

    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.authenticated = False
        st.session_state.show_landing = True
        st.session_state.username = None
        st.session_state.df = None
        st.session_state.analyzer = None
        st.session_state.financial_data = None
        st.rerun()

    with st.sidebar.expander("Change password"):
        with st.form("change_password_form", clear_on_submit=True):
            old_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Update Password"):
                if not old_password or not new_password or not confirm_password:
                    st.error("All fields are required")
                elif new_password != confirm_password:
                    st.error("New passwords do not match")
                else:
                    success, message = st.session_state.auth_handler.change_password(
                        st.session_state.username,
                        old_password,
                        new_password,
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
