import streamlit as st

from moneyflow.analytics.subscriptions import SubscriptionManager


def run_subscription_detection():
    """Run SubscriptionManager against current DataFrame and cache results."""
    if st.session_state.df is None:
        return

    mgr = SubscriptionManager(st.session_state.df)

    subs = mgr.detect_subscriptions()

    st.session_state.subscriptions = subs
    st.session_state.sub_summary = mgr.get_summary(subs)
    st.session_state._sub_mgr = mgr
