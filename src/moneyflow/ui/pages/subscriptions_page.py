import pandas as pd
import streamlit as st

from moneyflow.analytics.subscriptions import SubscriptionManager as SimpleSubscriptionManager
from moneyflow.services.subscription_service import run_subscription_detection
from moneyflow.ui.components.subscription_widgets import (
    render_cancellation_candidates,
    render_category_breakdown,
    render_subscription_table,
)


def render():
    if st.session_state.df is None:
        st.warning("No transactions loaded. Please upload a bank statement first.")
        return

    sub_tab1, sub_tab2 = st.tabs(["Detected Subscriptions", "Manage Subscriptions"])

    with sub_tab1:
        _render_detected(st.session_state.df)

    with sub_tab2:
        _render_manual(st.session_state.df)


def _render_detected(df):
    """Advanced auto-detection view using utils/subscription_manager."""
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.subheader("Subscription Manager")
        st.caption(
            "Automatically detected from your statement. Costs shown as monthly equivalents."
        )
    with col_h2:
        if st.button("Re-scan Statement", width="stretch"):
            run_subscription_detection()
            st.rerun()

    if not st.session_state.subscriptions and df is not None:
        run_subscription_detection()

    subscriptions = st.session_state.subscriptions
    summary = st.session_state.sub_summary

    if not subscriptions:
        st.info("No recurring subscriptions detected in your statement.")
        return

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Subscriptions Found", summary.get("count", 0))
    m2.metric("Total Monthly Cost", f"£{summary.get('total_monthly', 0):,.2f}")
    m3.metric("Total Annual Cost", f"£{summary.get('total_annual', 0):,.2f}")
    most_exp = summary.get("most_expensive")
    m4.metric(
        "Most Expensive",
        most_exp["name"] if most_exp else "-",
        f"£{most_exp['avg_monthly_cost']:.2f}/mo" if most_exp else None,
    )

    st.markdown("---")

    all_cats = sorted({s["category"] for s in subscriptions})
    selected_cats = st.multiselect(
        "Filter by category",
        options=all_cats,
        default=all_cats,
        label_visibility="collapsed",
        placeholder="Filter categories...",
    )
    filtered_subs = [s for s in subscriptions if s["category"] in selected_cats]

    det_tab1, det_tab2, det_tab3 = st.tabs(
        ["All Subscriptions", "By Category", "Cancellation Candidates"]
    )

    with det_tab1:
        render_subscription_table(filtered_subs)
        st.markdown("---")
        col_s1, col_s2 = st.columns([1, 3])
        with col_s1:
            if st.button("Save to Database", width="stretch"):
                ok, msg = st.session_state.db_handler.save_subscriptions(
                    st.session_state.username, subscriptions
                )
                st.success(msg) if ok else st.error(msg)
        with col_s2:
            db_count = st.session_state.db_handler.get_subscription_count(st.session_state.username)
            st.caption(
                f"Database has **{db_count}** active subscription(s) saved for your account."
            )

    with det_tab2:
        render_category_breakdown(filtered_subs, summary)

    with det_tab3:
        render_cancellation_candidates()


def _render_manual(df):
    """Simple manual subscription management view."""
    if "sub_manager" not in st.session_state:
        st.session_state.sub_manager = SimpleSubscriptionManager(df)

    manager = st.session_state.sub_manager
    st.subheader("Manage Subscriptions")

    all_subscriptions = manager.get_all_subscriptions()

    if not all_subscriptions:
        st.info("No subscriptions found. Add one manually below.")
    else:
        monthly_cost = manager.get_total_monthly_cost()
        annual_cost = manager.get_total_annual_cost()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monthly Cost", f"£{monthly_cost:.2f}")
        with col2:
            st.metric("Annual Cost", f"£{annual_cost:.2f}")
        with col3:
            st.metric("Total Subscriptions", len(all_subscriptions))

        st.markdown("---")

        upcoming = manager.get_upcoming_payments(7)
        if upcoming:
            st.warning(f"{len(upcoming)} payment(s) due in next 7 days")
            for sub in upcoming:
                days = sub["days_until"]
                if days == 0:
                    st.error(f"**{sub['name']}** - £{sub['monthly_cost']:.2f} - DUE TODAY!")
                else:
                    st.info(
                        f"**{sub['name']}** - £{sub['monthly_cost']:.2f} - Due in {days} day(s)"
                    )
            st.markdown("---")

        st.markdown("### Your Subscriptions")
        df_subs = pd.DataFrame(all_subscriptions)
        df_subs = df_subs[["name", "monthly_cost", "source", "next_payment"]]
        df_subs.columns = ["Subscription", "Monthly Cost", "Source", "Next Payment"]
        st.dataframe(df_subs.style.format({"Monthly Cost": "£{:.2f}"}), width="stretch")

        st.markdown("---")
        manual_subs = [s for s in all_subscriptions if s["source"] == "manual"]
        if manual_subs:
            st.markdown("### Manage Subscriptions")
            col1, col2 = st.columns([3, 1])
            with col1:
                to_remove = st.selectbox(
                    "Select subscription to remove",
                    options=[""] + [s["name"] for s in manual_subs],
                    key="remove_sub",
                )
            with col2:
                if st.button("Remove", disabled=not to_remove):
                    if manager.remove_manual_subscription(to_remove):
                        st.success(f"Removed {to_remove}")
                        st.rerun()
                    else:
                        st.error("Failed to remove")

    st.markdown("---")
    st.markdown("### Add Subscription Manually")
    st.caption("Add recurring payments that were not detected automatically.")

    with st.form("add_subscription", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            name = st.text_input("Subscription name", placeholder="e.g. Netflix")
        with col2:
            cost = st.number_input("Monthly cost (£)", min_value=0.0, step=0.50)
        with col3:
            next_date = st.date_input("Next payment")

        if st.form_submit_button("Add Subscription", width="stretch"):
            if name and cost > 0:
                if manager.add_manual_subscription(name, cost, next_date.strftime("%Y-%m-%d")):
                    st.success(f"Added {name}")
                    st.rerun()
                else:
                    st.error("Subscription already exists")
            else:
                st.error("Enter name and cost")

    if manager.get_total_monthly_cost() > 50:
        st.markdown("---")
        monthly = manager.get_total_monthly_cost()
        st.warning(f"Spending £{monthly:.2f}/month on subscriptions - consider reviewing")
