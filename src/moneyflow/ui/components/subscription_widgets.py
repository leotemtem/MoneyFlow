import pandas as pd
import plotly.express as px
import streamlit as st


def render_subscription_table(subscriptions: list):
    """Render the detailed subscriptions table with expand/collapse per row."""

    if not subscriptions:
        st.info("No subscriptions match the selected filters.")
        return

    rows = []

    for s in subscriptions:
        rows.append(
            {
                "Service": s["name"],
                "Category": s["category"],
                "Frequency": s["frequency"],
                "Monthly (£)": s["avg_monthly_cost"],
                "Annual (£)": s["annual_cost"],
                "Last Payment": s["last_payment"],
                "Next Est.": s["next_estimated"],
                "Seen": s["occurrences"],
                "Known": "Yes" if s.get("known_service") else "No",
            }
        )

    df_table = pd.DataFrame(rows)

    def _red_gradient(col):
        mn, mx = col.min(), col.max()
        rng = mx - mn if mx != mn else 1

        return [f"background-color: rgba(220,50,50,{0.1 + 0.6 * (v - mn) / rng:.2f})" for v in col]

    styled = df_table.style.format({"Monthly (£)": "£{:.2f}", "Annual (£)": "£{:.2f}"}).apply(
        _red_gradient, subset=["Monthly (£)"]
    )

    st.dataframe(styled, width="stretch", height=min(420, 50 + len(rows) * 38))

    st.markdown("#### Details")

    for s in subscriptions:
        with st.expander(f"{s['name']} - £{s['avg_monthly_cost']:.2f}/mo ({s['frequency']})"):
            c1, c2, c3 = st.columns(3)

            c1.metric("Monthly Cost", f"£{s['avg_monthly_cost']:.2f}")
            c2.metric("Annual Cost", f"£{s['annual_cost']:.2f}")
            c3.metric("Times Seen", s["occurrences"])

            c4, c5, c6 = st.columns(3)

            c4.metric("First Payment", s["first_payment"])
            c5.metric("Last Payment", s["last_payment"])
            c6.metric("Next Estimated", s["next_estimated"])

            st.caption(f"Raw description: `{s['description']}`")

            if s.get("all_amounts"):
                st.caption("Payment amounts seen: " + ", ".join(f"£{a}" for a in s["all_amounts"]))


def render_category_breakdown(subscriptions: list, summary: dict):
    """Pie chart + per-category tables."""
    if not subscriptions:
        st.info("No subscriptions to display.")
        return

    # Build per-category data from filtered list
    by_cat: dict = {}
    for s in subscriptions:
        cat = s["category"]
        if cat not in by_cat:
            by_cat[cat] = {"count": 0, "monthly_cost": 0.0, "items": []}
        by_cat[cat]["count"] += 1
        by_cat[cat]["monthly_cost"] += s["avg_monthly_cost"]
        by_cat[cat]["items"].append(s)

    col_chart, col_stats = st.columns([1, 1])

    with col_chart:
        labels = list(by_cat.keys())
        values = [by_cat[c]["monthly_cost"] for c in labels]
        fig = px.pie(
            names=labels,
            values=values,
            title="Monthly cost by category",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textinfo="label+percent")
        fig.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with col_stats:
        st.markdown("**Category Summary**")
        for cat, info in sorted(by_cat.items(), key=lambda x: x[1]["monthly_cost"], reverse=True):
            st.markdown(
                f"**{cat}** - {info['count']} sub(s) | "
                f"£{info['monthly_cost']:.2f}/mo | "
                f"£{info['monthly_cost'] * 12:.2f}/yr"
            )

    st.markdown("---")
    for cat, info in sorted(by_cat.items(), key=lambda x: x[1]["monthly_cost"], reverse=True):
        with st.expander(f"{cat}  ({info['count']} subscriptions)"):
            render_subscription_table(info["items"])


def render_cancellation_candidates():
    """Show subscriptions that haven't been charged recently."""
    mgr = st.session_state.get("_sub_mgr")
    if mgr is None or not st.session_state.subscriptions:
        st.info("Run a scan first.")
        return

    months = st.slider("Flag as inactive after how many months?", 1, 6, 2)
    candidates = mgr.get_cancellation_candidates(st.session_state.subscriptions, months)

    if not candidates:
        st.success("All detected subscriptions have recent payments; none appear forgotten.")
        return

    st.warning(
        f"{len(candidates)} subscription(s) haven't been charged in the last {months} "
        "month(s); you may have cancelled them or they could be forgotten."
    )

    for c in candidates:
        with st.expander(
            f"{c['name']} - last charged {c['last_payment']} "
            f"({c['months_since_last']:.1f} months ago) - £{c['avg_monthly_cost']:.2f}/mo"
        ):
            col1, col2 = st.columns(2)
            col1.metric("Last Payment", c["last_payment"])
            col2.metric("Months Since", f"{c['months_since_last']:.1f}")
            st.caption(f"Annual cost if still active: £{c['annual_cost']:.2f}")
