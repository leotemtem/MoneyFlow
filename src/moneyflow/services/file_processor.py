import streamlit as st

from moneyflow.analytics.analyzer import FinancialAnalyzer
from moneyflow.analytics.unusual_rules import get_default_unusual_rules
from moneyflow.parsing.csv_parser import CSVParser


def build_financial_data(analyzer, unusual_rules=None):
    """Build derived financial data used by pages and AI prompts."""
    rules = unusual_rules or get_default_unusual_rules()
    summary = analyzer.get_summary_stats()
    categories_data = analyzer.categorize_expenses()
    recurring = analyzer.identify_recurring_transactions()
    monthly = analyzer.calculate_monthly_breakdown()
    recommendations = analyzer.generate_budget_recommendations()
    try:
        unusual = analyzer.detect_unusual_transactions(rules=rules)
    except TypeError:
        unusual = analyzer.detect_unusual_transactions()
    top_merchants = analyzer.get_top_merchants()

    return {
        "summary": summary,
        "categories": categories_data["category_totals"],
        "recurring": recurring,
        "monthly": monthly,
        "recommendations": recommendations,
        "unusual": unusual,
        "top_merchants": top_merchants,
    }


def process_uploaded_file(uploaded_file):
    """Process uploaded CSV file"""
    try:
        parser = CSVParser()
        df = parser.parse_csv(uploaded_file)

        if df is not None and len(df) > 0:
            st.session_state.df = df
            st.session_state.analyzer = FinancialAnalyzer(df)
            # Reset subscription cache so it is re-detected for the new file
            st.session_state.subscriptions = []
            st.session_state.sub_summary = {}
            st.session_state._sub_mgr = None

            st.session_state.financial_data = build_financial_data(
                st.session_state.analyzer,
                st.session_state.get("unusual_rules", get_default_unusual_rules()),
            )

            return True
        else:
            st.error("Could not parse the CSV file. Please check the format.")
            return False
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return False
