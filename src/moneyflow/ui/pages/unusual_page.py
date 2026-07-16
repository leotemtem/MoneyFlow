import streamlit as st

from moneyflow.analytics.unusual_rules import (
    get_default_unusual_rules,
    normalise_keyword_list,
    suggest_unusual_rules,
)
from moneyflow.services.file_processor import build_financial_data


def _recalculate_unusual_transactions():
    if st.session_state.analyzer is None:
        return

    st.session_state.financial_data = build_financial_data(
        st.session_state.analyzer,
        st.session_state.unusual_rules,
    )


def _merge_rule_updates(updates):
    rules = st.session_state.unusual_rules.copy()

    for key, value in updates.items():
        if key == "ignore_categories":
            existing = set(rules.get("ignore_categories", []))
            existing.update(value)
            rules[key] = sorted(existing)
        elif key == "flag_keywords":
            existing = set(normalise_keyword_list(rules.get("flag_keywords", [])))
            existing.update(normalise_keyword_list(value))
            rules[key] = sorted(existing)
        else:
            rules[key] = value

    st.session_state.unusual_rules = rules
    _recalculate_unusual_transactions()


def _render_rule_controls(categories):
    rules = st.session_state.unusual_rules

    st.markdown("### Your unusual transaction rules")
    st.caption(
        "Define what feels unusual for you. These rules are applied alongside the automatic detector."
    )

    with st.form("unusual_rules_form"):
        use_statistical = st.checkbox(
            "Include automatic statistical detection",
            value=rules.get("use_statistical_detection", True),
            help="Keeps the current category, merchant, and outlier detection enabled.",
        )

        global_threshold = st.number_input(
            "Flag any expense over",
            min_value=0.0,
            value=float(rules.get("global_expense_threshold", 250.0)),
            step=10.0,
            format="%.2f",
        )

        c1, c2 = st.columns(2)
        with c1:
            flag_new_merchants = st.checkbox(
                "Flag new merchants",
                value=rules.get("flag_new_merchants", False),
                help="Flags merchants that appear only once in this uploaded statement.",
            )
        with c2:
            new_merchant_min_amount = st.number_input(
                "New merchant minimum",
                min_value=0.0,
                value=float(rules.get("new_merchant_min_amount", 75.0)),
                step=5.0,
                format="%.2f",
            )

        watched_keywords = st.text_input(
            "Watch keywords",
            value=", ".join(rules.get("flag_keywords", [])),
            help="Comma-separated words such as atm, fee, crypto, casino.",
        )
        ignored_keywords = st.text_input(
            "Ignore keywords",
            value=", ".join(rules.get("ignore_keywords", [])),
            help="Comma-separated words to exclude from unusual results.",
        )

        ignore_categories = st.multiselect(
            "Ignore categories",
            options=categories,
            default=[cat for cat in rules.get("ignore_categories", []) if cat in categories],
        )

        st.markdown("#### Category limits")
        st.caption("Optional. Set limits only for categories you care about.")

        category_thresholds = rules.get("category_thresholds", {}).copy()
        edited_thresholds = {}
        if categories:
            cols = st.columns(2)
            for idx, category in enumerate(categories):
                with cols[idx % 2]:
                    current_value = float(category_thresholds.get(category, 0.0) or 0.0)
                    value = st.number_input(
                        f"{category} over",
                        min_value=0.0,
                        value=current_value,
                        step=5.0,
                        format="%.2f",
                        key=f"unusual_threshold_{category}",
                    )
                    if value > 0:
                        edited_thresholds[category] = value

        submitted = st.form_submit_button("Apply rules", type="primary", width="stretch")

    if submitted:
        st.session_state.unusual_rules = {
            "use_statistical_detection": use_statistical,
            "global_expense_threshold": global_threshold,
            "category_thresholds": edited_thresholds,
            "flag_new_merchants": flag_new_merchants,
            "new_merchant_min_amount": new_merchant_min_amount,
            "flag_keywords": normalise_keyword_list(watched_keywords),
            "ignore_keywords": normalise_keyword_list(ignored_keywords),
            "ignore_categories": ignore_categories,
        }
        _recalculate_unusual_transactions()
        st.success("Unusual transaction rules updated.")
        st.rerun()

    if st.button("Reset to suggested defaults", width="stretch"):
        st.session_state.unusual_rules = get_default_unusual_rules()
        _recalculate_unusual_transactions()
        st.rerun()


def _render_suggestions(categories):
    suggestions = suggest_unusual_rules(
        st.session_state.df, st.session_state.financial_data["categories"]
    )
    if not suggestions:
        return

    st.markdown("### Suggested rules")
    st.caption("Based on this statement. Apply the ones that match how you think about your money.")

    for idx, suggestion in enumerate(suggestions):
        with st.container(border=True):
            st.markdown(f"**{suggestion['label']}**")
            st.caption(suggestion["description"])
            if st.button("Apply suggestion", key=f"apply_unusual_suggestion_{idx}"):
                _merge_rule_updates(suggestion["updates"])
                st.success("Suggestion applied.")
                st.rerun()


def _render_transaction_group(title, transactions):
    if not transactions:
        return

    st.markdown(f"### {title}")
    for trans in transactions:
        with st.expander(f"£{trans['amount']:,.2f} - {trans['description']} ({trans['date']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Amount", f"£{trans['amount']:,.2f}")
                st.write(f"**Category:** {trans.get('category', 'N/A')}")
                st.write(f"**Type:** {trans.get('type', 'N/A').capitalize()}")
            with col2:
                st.write(f"**Date:** {trans['date']}")
                if trans.get("z_score", 0) > 0:
                    st.write(f"**Deviation Score:** {trans['z_score']:.2f}")
                if trans.get("rule_source"):
                    st.write(f"**Source:** {trans['rule_source']}")
            st.info(
                f"**Why unusual:** {trans.get('reason', 'Significantly different from typical patterns')}"
            )


def _render_ai_review(unusual):
    if not st.session_state.get("llm_loaded"):
        st.caption(
            "Enable an AI provider in the sidebar to get a short AI review of these unusual transactions."
        )
        return

    if not unusual:
        return

    if st.button("Ask AI to review these flags", width="stretch"):
        top_items = unusual[:8]
        rule_summary = st.session_state.unusual_rules
        transaction_summary = "\n".join(
            f"- {item['date']}: {item['description']} £{item['amount']:.2f} ({item.get('reason', 'flagged')})"
            for item in top_items
        )
        question = f"""Using my current unusual-transaction rules, review these flagged transactions.

Current rules:
{rule_summary}

Flagged transactions:
{transaction_summary}

Tell me:
- Which 3 deserve attention first
- Why each one matters
- What I should check next

Use plain English for someone without financial knowledge. Avoid technical terms like z-score, standard deviation, or outlier unless you explain them simply. Keep it practical."""

        with st.spinner("Reviewing unusual transactions..."):
            try:
                answer = st.session_state.assistant.answer_question(
                    st.session_state.financial_data,
                    question,
                    concise=True,
                    max_length=260,
                )
            except TypeError:
                answer = st.session_state.assistant.answer_question(
                    st.session_state.financial_data,
                    question,
                )
            st.markdown(f'<div class="insight-box">{answer}</div>', unsafe_allow_html=True)


def render():
    if not st.session_state.financial_data:
        st.warning("No financial data loaded. Please upload a bank statement first.")
        return

    st.subheader("Unusual Transactions")
    st.caption(
        "Use automatic detection, your own rules, and suggested rules to decide what deserves review."
    )

    categories = sorted(st.session_state.financial_data.get("categories", {}).keys())

    rules_tab, results_tab = st.tabs(["Rules", "Results"])

    with rules_tab:
        _render_suggestions(categories)
        st.markdown("---")
        _render_rule_controls(categories)

    with results_tab:
        unusual = st.session_state.financial_data["unusual"]

        if unusual:
            high_severity = [t for t in unusual if t.get("severity") == "high"]
            medium_severity = [t for t in unusual if t.get("severity") == "medium"]

            c1, c2, c3 = st.columns(3)
            c1.metric("Unusual Transactions", len(unusual))
            c2.metric("High Priority", len(high_severity))
            c3.metric("Medium Priority", len(medium_severity))

            _render_ai_review(unusual)

            _render_transaction_group("High Priority", high_severity)
            _render_transaction_group("Medium Priority", medium_severity)
        else:
            st.info("No unusual transactions detected with your current rules.")
