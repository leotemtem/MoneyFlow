import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from moneyflow.ai.prompts import FinancialPrompts


def render():
    if st.session_state.df is None or st.session_state.financial_data is None:
        st.warning("No financial data to plan budget. Please upload a bank statement first.")
        return

    st.subheader("Budget Planner")
    st.caption("Create a monthly plan, compare it with actual spending, and size savings targets.")

    summary = st.session_state.financial_data["summary"]
    categories = st.session_state.financial_data["categories"]
    monthly_avg_expenses = summary["total_expenses"] / max(1, summary["date_range_days"] / 30)
    monthly_avg_income = summary["total_income"] / max(1, summary["date_range_days"] / 30)

    budget_tab1, budget_tab2, budget_tab3 = st.tabs(
        ["Budget Setup", "Budget vs Actual", "Savings Goals"]
    )

    with budget_tab1:
        st.markdown("### Set Your Monthly Budget")
        st.info(
            f"Your average monthly income: **£{monthly_avg_income:,.2f}** | Average expenses: **£{monthly_avg_expenses:,.2f}**"
        )

        st.markdown("#### Quick Start Templates")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("50/30/20 Rule", width="stretch"):
                st.session_state.budget_template = "50/30/20"
                st.info("""
                **50/30/20 Budget Rule:**
                - 50% Needs (housing, food, utilities)
                - 30% Wants (entertainment, dining)
                - 20% Savings & Debt
                """)

        with col2:
            if st.button("Aggressive Savings", width="stretch"):
                st.session_state.budget_template = "aggressive"
                st.info("""
                **Aggressive Savings:**
                - 50% Needs
                - 20% Wants
                - 30% Savings
                """)

        with col3:
            if st.button("Based on Current Spending", width="stretch"):
                st.session_state.budget_template = "current"
                st.info("Budget based on your actual spending patterns")

        st.markdown("---")
        st.markdown("#### Category Budget Allocation")

        category_list = list(categories.keys())
        col1, col2 = st.columns(2)
        budget_total = 0
        temp_budget = {}

        for idx, category in enumerate(category_list):
            current_spending = categories[category]
            avg_monthly_spending = current_spending / max(1, summary["date_range_days"] / 30)

            with col1 if idx % 2 == 0 else col2:
                st.markdown(f"**{category}**")
                st.caption(f"Current monthly avg: £{avg_monthly_spending:.2f}")

                default_budget = st.session_state.budget_plan.get(category, avg_monthly_spending)
                budget_amount = st.number_input(
                    f"Monthly budget for {category}",
                    min_value=0.0,
                    value=float(default_budget),
                    step=10.0,
                    key=f"budget_{category}",
                    label_visibility="collapsed",
                )
                temp_budget[category] = budget_amount
                budget_total += budget_amount

        st.markdown("---")
        st.markdown("**Savings**")
        savings_budget = st.number_input(
            "Monthly savings target",
            min_value=0.0,
            value=float(st.session_state.savings_goal),
            step=50.0,
            key="budget_savings",
        )
        temp_budget["Savings"] = savings_budget
        budget_total += savings_budget

        st.markdown("---")
        st.markdown("### Budget Summary")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Budget", f"£{budget_total:,.2f}")
        with col2:
            difference = monthly_avg_income - budget_total
            st.metric(
                "vs Income",
                f"£{difference:,.2f}",
                delta=f"{'Surplus' if difference >= 0 else 'Deficit'}",
            )
        with col3:
            savings_rate = (
                (savings_budget / monthly_avg_income * 100) if monthly_avg_income > 0 else 0
            )
            st.metric("Savings Rate", f"{savings_rate:.1f}%")

        if st.button("Save Budget Plan", type="primary", width="stretch"):
            st.session_state.budget_plan = temp_budget.copy()
            del st.session_state.budget_plan["Savings"]
            st.session_state.savings_goal = savings_budget
            st.success("Budget plan saved successfully!")
            st.rerun()

        if budget_total > monthly_avg_income:
            st.warning(
                f"Your budget (£{budget_total:,.2f}) exceeds your average income (£{monthly_avg_income:,.2f}) by £{budget_total - monthly_avg_income:,.2f}"
            )
        elif savings_budget < monthly_avg_income * 0.1:
            st.info(
                f"Consider increasing savings to at least 10% of income (£{monthly_avg_income * 0.1:,.2f})"
            )

    with budget_tab2:
        if not st.session_state.budget_plan:
            st.info("Please set up your budget in the 'Budget Setup' tab first")
        else:
            st.markdown("### Budget vs Actual Spending")

            comparison_data = []
            total_budgeted = 0
            total_actual = 0

            for category in category_list:
                if category in st.session_state.budget_plan:
                    budgeted = st.session_state.budget_plan[category]
                    actual = categories[category] / max(1, summary["date_range_days"] / 30)
                    difference = budgeted - actual
                    percentage = (actual / budgeted * 100) if budgeted > 0 else 0

                    comparison_data.append(
                        {
                            "Category": category,
                            "Budgeted": budgeted,
                            "Actual": actual,
                            "Difference": difference,
                            "Used %": percentage,
                            "Status": "Under" if difference > 0 else "Over",
                        }
                    )

                    total_budgeted += budgeted
                    total_actual += actual

            if comparison_data:
                df_comparison = pd.DataFrame(comparison_data)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Budgeted", f"£{total_budgeted:,.2f}")
                with col2:
                    st.metric("Total Spent", f"£{total_actual:,.2f}")
                with col3:
                    diff = total_budgeted - total_actual
                    st.metric(
                        "Difference",
                        f"£{abs(diff):,.2f}",
                        delta=f"{'Under' if diff > 0 else 'Over'} budget",
                    )
                with col4:
                    categories_over = len([c for c in comparison_data if c["Status"] == "Over"])
                    st.metric("Categories Over", categories_over)

                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure()
                    fig.add_trace(
                        go.Bar(
                            name="Budgeted",
                            x=df_comparison["Category"],
                            y=df_comparison["Budgeted"],
                            marker_color="#40798c",
                        )
                    )
                    fig.add_trace(
                        go.Bar(
                            name="Actual",
                            x=df_comparison["Category"],
                            y=df_comparison["Actual"],
                            marker_color="#b54708",
                        )
                    )
                    fig.update_layout(
                        title="Budget vs Actual by Category",
                        xaxis_title="Category",
                        yaxis_title="Amount (£)",
                        barmode="group",
                        height=400,
                    )
                    st.plotly_chart(fig, width="stretch")

                with col2:
                    status_counts = df_comparison["Status"].value_counts()
                    fig = px.pie(
                        values=status_counts.values,
                        names=status_counts.index,
                        title="Budget Status Overview",
                        color_discrete_map={"Under": "#15803d", "Over": "#b42318"},
                        hole=0.4,
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width="stretch")

                st.markdown("### Detailed Breakdown")
                styled_df = (
                    df_comparison.style.format(
                        {
                            "Budgeted": "£{:.2f}",
                            "Actual": "£{:.2f}",
                            "Difference": "£{:.2f}",
                            "Used %": "{:.1f}%",
                        }
                    )
                    .map(
                        lambda x: (
                            "color: #15803d"
                            if str(x) == "Under"
                            else ("color: #b42318" if str(x) == "Over" else "")
                        ),
                        subset=["Status"],
                    )
                    .map(
                        lambda x: (
                            "color: #b42318; font-weight: bold"
                            if isinstance(x, (int, float)) and x > 100
                            else ""
                        ),
                        subset=["Used %"],
                    )
                )
                st.dataframe(styled_df, width="stretch")

                if st.session_state.llm_loaded:
                    st.markdown("---")
                    if st.button("Get AI Budget Analysis", width="stretch"):
                        with st.spinner("Analyzing your budget performance..."):
                            budget_context = st.session_state.financial_data.copy()
                            budget_context["budget_plan"] = st.session_state.budget_plan
                            budget_context["budget_comparison"] = comparison_data
                            insights = st.session_state.assistant.answer_question(
                                budget_context,
                                FinancialPrompts.get_budget_planner_analysis_prompt(),
                            )
                            st.markdown(
                                f'<div class="insight-box">{insights}</div>', unsafe_allow_html=True
                            )

    with budget_tab3:
        st.markdown("### Savings Goals & Emergency Fund")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Monthly Savings Goal")
            current_savings_goal = st.session_state.savings_goal
            recommended_savings = monthly_avg_income * 0.2
            st.info(f"Recommended (20% rule): £{recommended_savings:,.2f}/month")

            new_savings_goal = st.number_input(
                "Set monthly savings goal",
                min_value=0.0,
                value=float(current_savings_goal),
                step=50.0,
                key="savings_goal_input",
            )

            if st.button("Update Savings Goal"):
                st.session_state.savings_goal = new_savings_goal
                st.success(f"Savings goal updated to £{new_savings_goal:,.2f}/month")

            if new_savings_goal > 0:
                st.markdown("**Savings Projection:**")
                projections = {
                    "3 months": new_savings_goal * 3,
                    "6 months": new_savings_goal * 6,
                    "1 year": new_savings_goal * 12,
                    "2 years": new_savings_goal * 24,
                    "5 years": new_savings_goal * 60,
                }
                for period, amount in projections.items():
                    st.metric(period, f"£{amount:,.2f}")

        with col2:
            st.markdown("#### Emergency Fund")
            st.info("""
            **Emergency Fund Guidelines:**
            - Minimum: 3 months of expenses
            - Recommended: 6 months
            - Ideal: 12 months
            """)

            emergency_months = st.slider(
                "Target months of expenses", min_value=3, max_value=12, value=6, step=1
            )
            emergency_target = monthly_avg_expenses * emergency_months
            st.session_state.emergency_fund_target = emergency_target

            st.metric(
                "Emergency Fund Target",
                f"£{emergency_target:,.2f}",
                delta=f"{emergency_months} months of expenses",
            )

            if new_savings_goal > 0:
                months_to_goal = emergency_target / new_savings_goal
                st.info(
                    f"At £{new_savings_goal:,.2f}/month, you'll reach your emergency fund in **{months_to_goal:.1f} months** ({months_to_goal / 12:.1f} years)"
                )

        st.markdown("---")
        st.markdown("### Savings Strategies")

        strategies_col1, strategies_col2 = st.columns(2)
        with strategies_col1:
            st.markdown("""
            **Automated Savings:**
            - Set up automatic transfers on payday
            - Use the "pay yourself first" principle
            - Round-up savings on purchases
            - Direct deposit split to savings account
            """)
        with strategies_col2:
            st.markdown("""
            **Boost Your Savings:**
            - Save windfalls (bonuses, tax refunds)
            - Challenge yourself (52-week challenge)
            - Cut one unnecessary subscription
            - Reduce dining out by 25%
            """)

        if st.session_state.llm_loaded:
            st.markdown("---")
            if st.button("Get Personalized Savings Plan", width="stretch"):
                with st.spinner("Creating your personalized savings plan..."):
                    savings_context = st.session_state.financial_data.copy()
                    savings_context["savings_goal"] = new_savings_goal
                    savings_context["emergency_fund_target"] = emergency_target
                    insights = st.session_state.assistant.answer_question(
                        savings_context, FinancialPrompts.get_savings_goal_prompt()
                    )
                    st.markdown(
                        f'<div class="insight-box">{insights}</div>', unsafe_allow_html=True
                    )
