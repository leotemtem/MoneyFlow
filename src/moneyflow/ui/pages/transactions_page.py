from datetime import datetime

import pandas as pd
import streamlit as st


def render():
    if st.session_state.df is None:
        st.warning("No transactions to display. Please upload a bank statement.")
        return

    st.subheader("Transactions")
    st.caption("Filter, sort, review, and export parsed statement entries.")

    df = st.session_state.df.copy()
    date_range = None

    col1, col2, col3 = st.columns(3)

    with col1:
        transaction_types = ["All", "Income", "Expenses"]
        selected_type = st.selectbox("Transaction Type", transaction_types)

    with col2:
        if len(df) > 0:
            min_date = df["Date"].min().date()
            max_date = df["Date"].max().date()
            date_range = st.date_input(
                "Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
            )
        else:
            st.text_input("Date Range", value="No transactions", disabled=True)

    with col3:
        search_term = st.text_input("Search Description", placeholder="e.g., Netflix, Tesco")

    filtered_df = df.copy()

    if selected_type == "Income":
        filtered_df = filtered_df[filtered_df["Amount"] > 0]
    elif selected_type == "Expenses":
        filtered_df = filtered_df[filtered_df["Amount"] < 0]

    if date_range is not None and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["Date"].dt.date >= start_date) & (filtered_df["Date"].dt.date <= end_date)
        ]

    if search_term:
        filtered_df = filtered_df[
            filtered_df["Description"].str.contains(search_term, case=False, na=False)
        ]

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Transactions", f"{len(filtered_df):,}")
    with col2:
        total_income = filtered_df[filtered_df["Amount"] > 0]["Amount"].sum()
        st.metric("Total Income", f"£{total_income:,.2f}")
    with col3:
        total_expenses = abs(filtered_df[filtered_df["Amount"] < 0]["Amount"].sum())
        st.metric("Total Expenses", f"£{total_expenses:,.2f}")
    with col4:
        net_amount = total_income - total_expenses
        st.metric("Net Amount", f"£{net_amount:,.2f}")

    st.markdown("---")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{len(filtered_df)} of {len(df)} transactions shown**")
    with col2:
        sort_order = st.selectbox(
            "Sort by", ["Latest First", "Oldest First", "Highest Amount", "Lowest Amount"]
        )

    if sort_order == "Latest First":
        filtered_df = filtered_df.sort_values("Date", ascending=False)
    elif sort_order == "Oldest First":
        filtered_df = filtered_df.sort_values("Date", ascending=True)
    elif sort_order == "Highest Amount":
        filtered_df = filtered_df.sort_values("Amount", ascending=False)
    else:
        filtered_df = filtered_df.sort_values("Amount", ascending=True)

    display_df = filtered_df.copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
    display_df["Type"] = display_df["Amount"].apply(lambda x: "Income" if x > 0 else "Expense")

    if "Balance" in display_df.columns:
        display_columns = ["Date", "Description", "Amount", "Type", "Balance"]
    else:
        display_columns = ["Date", "Description", "Amount", "Type"]

    display_df = display_df[display_columns]

    styled_df = display_df.style.map(
        lambda x: "color: green" if x == "Income" else ("color: red" if x == "Expense" else ""),
        subset=["Type"],
    ).format(
        {"Amount": lambda x: f"£{x:,.2f}", "Balance": lambda x: f"£{x:,.2f}" if pd.notna(x) else ""}
    )

    st.dataframe(styled_df, width="stretch", height=500)

    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col2:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"moneyflow_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            width="stretch",
        )
