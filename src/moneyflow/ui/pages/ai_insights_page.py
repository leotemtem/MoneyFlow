# SPDX-License-Identifier: MIT
"""AI Insights tab — optional, provider-agnostic AI-generated commentary."""

import streamlit as st

from moneyflow.ai.base import AIProviderError
from moneyflow.ai.prompts import FinancialPrompts

AI_DISCLAIMER = (
    "AI-generated insights are informational only, may be inaccurate, and are not "
    "financial, tax, legal, or investment advice. All figures shown elsewhere in the "
    "app are calculated deterministically; only this tab uses a language model."
)


def _run(fn, *args, **kwargs):
    """Call a provider method, degrading gracefully on failure."""
    try:
        return fn(*args, **kwargs)
    except AIProviderError as exc:
        st.error(f"AI request failed: {exc}")
    except Exception:  # pragma: no cover - defensive UI guard
        st.error("AI request failed unexpectedly. Check the application logs.")
    return None


def _show(text: str | None) -> None:
    if text:
        st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


def render():
    provider = st.session_state.get("ai_provider")
    if provider is None:
        st.info(
            "AI insights are disabled. Set MONEYFLOW_AI_PROVIDER to 'local' or 'openai' "
            "to enable this optional feature. Every other tab works without AI."
        )
        return

    if not st.session_state.llm_loaded:
        st.warning(f"Enable {provider.name} from the sidebar to generate AI insights.")
        return

    assistant = st.session_state.assistant

    st.subheader("AI Financial Insights")
    st.caption(AI_DISCLAIMER)

    st.markdown("#### Quick prompts")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Financial Overview", width="stretch"):
            with st.spinner("Summarising your finances..."):
                _show(
                    _run(
                        assistant.generate_insights,
                        st.session_state.financial_data,
                        max_tokens=220,
                        concise=True,
                    )
                )

    with col2:
        if st.button("Budgeting Advice", width="stretch"):
            with st.spinner("Creating budget plan..."):
                _show(
                    _run(
                        assistant.answer_question,
                        st.session_state.financial_data,
                        FinancialPrompts.get_budgeting_prompt(),
                        concise=True,
                        max_tokens=220,
                    )
                )

    with col3:
        if st.button("Savings Tips", width="stretch"):
            with st.spinner("Finding savings opportunities..."):
                _show(
                    _run(
                        assistant.answer_question,
                        st.session_state.financial_data,
                        FinancialPrompts.get_savings_prompt(),
                        concise=True,
                        max_tokens=220,
                    )
                )

    st.markdown("---")
    st.markdown("#### Ask a custom question")
    user_question = st.text_input(
        "Ask anything about your finances:",
        placeholder="e.g., How can I save more money? What are my biggest expenses?",
    )

    if st.button("Get Answer", type="primary"):
        if user_question:
            with st.spinner("Thinking..."):
                _show(
                    _run(
                        assistant.answer_question,
                        st.session_state.financial_data,
                        user_question,
                    )
                )
        else:
            st.warning("Please enter a question")
