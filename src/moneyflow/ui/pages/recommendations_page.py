import streamlit as st


def render():
    if not st.session_state.financial_data:
        st.warning("No financial data loaded. Please upload a bank statement first.")
        return

    recommendations = st.session_state.financial_data["recommendations"]

    st.subheader("Budget Recommendations")
    st.caption(
        "Categories where your spending exceeds recommended guidelines (based on the 50/30/20 rule)."
    )

    if recommendations:
        for rec in recommendations:
            severity_label = "High priority" if rec["severity"] == "high" else "Medium priority"

            with st.expander(
                f"{severity_label}: {rec['category']} - Potential savings £{rec['potential_savings']:.2f}"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Current Spending",
                        f"£{rec['current_spending']:,.2f}",
                        f"{rec['current_percentage']:.1f}% of expenses",
                    )
                with col2:
                    st.metric(
                        "Recommended %",
                        f"{rec['recommended_percentage']}%",
                        f"-{rec['current_percentage'] - rec['recommended_percentage']:.1f}%",
                    )
    else:
        st.success(
            "Your spending looks balanced; no categories are significantly over the recommended guidelines."
        )
