# SPDX-License-Identifier: MIT
"""Streamlit session-state initialisation."""

from __future__ import annotations

import streamlit as st

from moneyflow.ai import get_ai_provider
from moneyflow.analytics.unusual_rules import get_default_unusual_rules
from moneyflow.auth.handler import AuthHandler
from moneyflow.database.handler import DatabaseHandler


def init_session_state() -> None:
    defaults = {
        "analyzer": None,
        "df": None,
        "llm_loaded": False,
        "assistant": None,
        "financial_data": None,
        "authenticated": False,
        "show_landing": True,
        "username": None,
        "budget_plan": {},
        "savings_goal": 0,
        "emergency_fund_target": 0,
        "subscriptions": [],
        "sub_summary": {},
        "_sub_mgr": None,
        "unusual_rules": get_default_unusual_rules(),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "auth_handler" not in st.session_state:
        st.session_state.auth_handler = AuthHandler()

    if "db_handler" not in st.session_state:
        st.session_state.db_handler = DatabaseHandler()

    # Optional AI provider (None when AI is disabled — the app works without it).
    if "ai_provider" not in st.session_state:
        st.session_state.ai_provider = get_ai_provider()
