# SPDX-License-Identifier: MIT
"""Streamlit service for enabling the optional AI provider."""

from __future__ import annotations

import logging

import streamlit as st

from moneyflow.ai.base import AIProviderError

logger = logging.getLogger(__name__)


def enable_ai() -> None:
    """Load the configured AI provider and mark it ready in session state.

    Safe to call when no provider is configured — it simply informs the user.
    """
    provider = st.session_state.get("ai_provider")
    if provider is None:
        st.warning(
            "No AI provider is configured. Set MONEYFLOW_AI_PROVIDER to 'local' or "
            "'openai' (see README) to enable AI insights."
        )
        return

    status = st.empty()
    status.info(f"Enabling {provider.name}... local models can take several minutes to load.")
    try:
        provider.load()
        st.session_state.assistant = provider
        st.session_state.llm_loaded = True
        status.success(f"{provider.name} ready")
        st.rerun()
    except AIProviderError as exc:
        status.error(f"Could not enable AI: {exc}")
    except Exception:  # pragma: no cover - defensive UI guard
        logger.exception("Unexpected error while enabling AI provider")
        status.error("Could not enable AI. Check the application logs for details.")


# Backwards-compatible alias for existing call sites.
load_llm = enable_ai
