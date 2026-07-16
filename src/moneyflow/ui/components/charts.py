import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CHART_COLORS = [
    "#176b5f",
    "#40798c",
    "#8f5f29",
    "#7a5c99",
    "#c2410c",
    "#2563eb",
    "#64748b",
    "#0f766e",
]


def apply_chart_layout(fig, title: str, height: int = 420):
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", font=dict(size=18)),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#182230"),
        margin=dict(l=40, r=30, t=56, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def display_category_chart():
    """Display expense category breakdown"""

    if st.session_state.financial_data:
        categories = st.session_state.financial_data["categories"]

        df_cat = pd.DataFrame(list(categories.items()), columns=["Category", "Amount"])

        df_cat = df_cat.sort_values("Amount", ascending=False)
        total_amount = df_cat["Amount"].sum()
        df_cat["Percent"] = df_cat["Amount"] / total_amount if total_amount else 0
        df_cat["SliceLabel"] = df_cat.apply(
            lambda row: (
                f"{row['Category']}<br>{row['Percent']:.1%}"
                if row["Percent"] >= 0.08
                else (f"{row['Percent']:.1%}" if row["Percent"] >= 0.04 else "")
            ),
            axis=1,
        )

        fig = px.pie(
            df_cat,
            values="Amount",
            names="Category",
            hole=0.4,
            color_discrete_sequence=CHART_COLORS,
        )

        fig.update_traces(
            textposition="inside",
            text=df_cat["SliceLabel"],
            textinfo="text",
            hovertemplate="%{label}<br>£%{value:,.2f}<br>%{percent}<extra></extra>",
            insidetextorientation="horizontal",
            textfont=dict(size=11),
            showlegend=False,
        )

        apply_chart_layout(fig, "Expense Breakdown by Category", height=420)
        fig.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=56, b=20),
        )

        st.plotly_chart(fig, width="stretch")


def display_monthly_trend():
    """Display monthly income/expense trend"""
    if st.session_state.financial_data:
        monthly = st.session_state.financial_data["monthly"]

        df_monthly = pd.DataFrame(monthly)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df_monthly["month"], y=df_monthly["income"], name="Income", marker_color="#15803d"
            )
        )

        fig.add_trace(
            go.Bar(
                x=df_monthly["month"],
                y=df_monthly["expenses"],
                name="Expenses",
                marker_color="#b42318",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df_monthly["month"],
                y=df_monthly["net"],
                name="Net",
                mode="lines+markers",
                line=dict(color="#176b5f", width=3),
                yaxis="y2",
            )
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Amount (£)",
            yaxis2=dict(title="Net Cashflow (£)", overlaying="y", side="right"),
            barmode="group",
            hovermode="x unified",
        )
        apply_chart_layout(fig, "Monthly Income vs Expenses", height=460)

        st.plotly_chart(fig, width="stretch")


def display_daily_spending_heatmap():
    # daily spending heatmap
    df = st.session_state.df
    if df is None:
        return

    expenses = df[df["Amount"] < 0].copy()
    expenses["Amount"] = expenses["Amount"].abs()
    expenses["DateOnly"] = expenses["Date"].dt.date

    daily = expenses.groupby("DateOnly")["Amount"].sum().reset_index()
    daily.columns = ["Date", "Total_Spent"]
    daily["Date"] = pd.to_datetime(daily["Date"])

    if daily.empty:
        st.info("No spending data.")
        return

    years = sorted(daily["Date"].dt.year.unique(), reverse=True)
    selected_year = st.radio("Year", years, horizontal=True) if len(years) > 1 else years[0]

    year_data = daily[daily["Date"].dt.year == selected_year].copy()
    year_data["week"] = year_data["Date"].dt.isocalendar().week.astype(int)
    year_data["weekday"] = year_data["Date"].dt.weekday

    months_present = year_data["Date"].dt.month.unique()
    if len(months_present) == 1:
        title = year_data["Date"].dt.strftime("%B %Y").iloc[0]
    else:
        title = str(selected_year)

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    hover_text = [
        f"{row['Date'].strftime('%A, %d %B %Y')}<br>Spent: £{row['Total_Spent']:,.2f}"
        for _, row in year_data.iterrows()
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=year_data["week"],
            y=year_data["weekday"],
            mode="markers",
            marker=dict(
                size=22,
                symbol="square",
                color=year_data["Total_Spent"],
                colorscale=[
                    [0, "#fff7ed"],
                    [0.45, "#fdba74"],
                    [1, "#b42318"],
                ],
                showscale=True,
                colorbar=dict(title="£ spent"),
                line=dict(width=1, color="#ffffff"),
            ),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis=dict(
            title="Week",
            tickmode="linear",
            tick0=int(year_data["week"].min()),
            dtick=1,
            range=[year_data["week"].min() - 0.5, year_data["week"].max() + 0.5],
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(7)),
            ticktext=day_labels,
            autorange="reversed",
            range=[-0.5, 6.5],
        ),
    )
    apply_chart_layout(fig, f"Daily Spending - {title}", height=420)

    st.plotly_chart(fig, width="stretch")


def display_running_balance_chart():
    # running balance chart
    df = st.session_state.df
    if df is None:
        return

    if "Balance" not in df.columns:
        st.info("Need a Balance column for this chart.")
        return

    df = df.dropna(subset=["Balance"]).sort_values("Date")

    hover_text = [
        f"{row['Date'].strftime('%d %B %Y')}<br>{row['Description']}<br>"
        f"Transaction: £{row['Amount']:,.2f}<br>Balance: £{row['Balance']:,.2f}"
        for _, row in df.iterrows()
    ]
    colours = ["#15803d" if amt > 0 else "#b42318" for amt in df["Amount"]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"], y=df["Balance"], mode="lines", line=dict(color="#176b5f", width=2.5)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Balance"],
            mode="markers",
            marker=dict(size=6, color=colours),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )

    fig.update_layout(xaxis_title="Date", yaxis_title="Balance (£)", showlegend=False)
    apply_chart_layout(fig, "Running Balance", height=380)

    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Highest balance", f"£{df['Balance'].max():,.2f}")
        st.caption(df.loc[df["Balance"].idxmax(), "Date"].strftime("%d %B %Y"))
    with col2:
        st.metric("Lowest balance", f"£{df['Balance'].min():,.2f}")
        st.caption(df.loc[df["Balance"].idxmin(), "Date"].strftime("%d %B %Y"))
