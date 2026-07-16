# SPDX-License-Identifier: MIT
"""Streamlit page configuration and theme CSS for MoneyFlow."""

import streamlit as st

THEME_TOKENS = {
    "light": {
        "bg": "#F7F8FA",
        "surface": "#FFFFFF",
        "text": "#182230",
        "border": "#D9DEE7",
        "muted": "#667085",
        "primary": "#176B5F",
        "primary_dark": "#14564D",
        "income": "#15803D",
        "expense": "#B42318",
        "warning": "#B54708",
        "input_bg": "#FFFFFF",
        "button_bg": "#FFFFFF",
        "placeholder": "#98A2B3",
        "sidebar_bg": "#FFFFFF",
        "sidebar_surface": "#F7F8FA",
        "sidebar_text": "#182230",
        "sidebar_muted": "#667085",
        "sidebar_border": "#D9DEE7",
        "sidebar_input_bg": "#FFFFFF",
        "sidebar_input_text": "#182230",
        "sidebar_placeholder": "#98A2B3",
    },
    "dark": {
        "bg": "#0B1118",
        "surface": "#111827",
        "text": "#F4F6FB",
        "border": "#344054",
        "muted": "#CDD5DF",
        "primary": "#5DD6BC",
        "primary_dark": "#45BDA8",
        "income": "#4ADE80",
        "expense": "#FB7185",
        "warning": "#FBBF24",
        "input_bg": "#111827",
        "button_bg": "#111827",
        "placeholder": "#98A2B3",
        "sidebar_bg": "#101828",
        "sidebar_surface": "#1D2939",
        "sidebar_text": "#F2F4F7",
        "sidebar_muted": "#CDD5DF",
        "sidebar_border": "#1D2939",
        "sidebar_input_bg": "#1D2939",
        "sidebar_input_text": "#F2F4F7",
        "sidebar_placeholder": "#98A2B3",
    },
}


def configure_page():
    """Configure the Streamlit page (must run before other st calls)."""
    st.set_page_config(
        page_title="MoneyFlow",
        page_icon="MF",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_theme():
    """Inject the MoneyFlow theme CSS variables and styles."""
    active_theme = getattr(st.context.theme, "type", "light") or "light"
    theme = THEME_TOKENS.get(active_theme, THEME_TOKENS["light"])

    st.markdown(
        f"""
    <style>
        :root {{
            --mf-config-bg: {theme["bg"]};
            --mf-config-surface: {theme["surface"]};
            --mf-config-text: {theme["text"]};
            --mf-config-border: {theme["border"]};
            --mf-config-muted: {theme["muted"]};
            --mf-config-primary: {theme["primary"]};
            --mf-config-primary-dark: {theme["primary_dark"]};
            --mf-config-income: {theme["income"]};
            --mf-config-expense: {theme["expense"]};
            --mf-config-warning: {theme["warning"]};
            --mf-config-input-bg: {theme["input_bg"]};
            --mf-config-button-bg: {theme["button_bg"]};
            --mf-config-placeholder: {theme["placeholder"]};
            --mf-config-sidebar-bg: {theme["sidebar_bg"]};
            --mf-config-sidebar-surface: {theme["sidebar_surface"]};
            --mf-config-sidebar-text: {theme["sidebar_text"]};
            --mf-config-sidebar-muted: {theme["sidebar_muted"]};
            --mf-config-sidebar-border: {theme["sidebar_border"]};
            --mf-config-sidebar-input-bg: {theme["sidebar_input_bg"]};
            --mf-config-sidebar-input-text: {theme["sidebar_input_text"]};
            --mf-config-sidebar-placeholder: {theme["sidebar_placeholder"]};
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <style>
        :root {
            --mf-bg: var(--mf-config-bg, #f7f8fa);
            --mf-surface: var(--mf-config-surface, #ffffff);
            --mf-text: var(--mf-config-text, #182230);
            --mf-border: var(--mf-config-border, #d9dee7);
            --mf-muted: var(--mf-config-muted, #667085);
            --mf-primary: var(--mf-config-primary, #176b5f);
            --mf-primary-dark: var(--mf-config-primary-dark, #14564d);
            --mf-income: var(--mf-config-income, #15803d);
            --mf-expense: var(--mf-config-expense, #b42318);
            --mf-warning: var(--mf-config-warning, #b54708);
            --mf-input-bg: var(--mf-config-input-bg, #ffffff);
            --mf-button-bg: var(--mf-config-button-bg, #ffffff);
            --mf-placeholder: var(--mf-config-placeholder, #98a2b3);
            --mf-sidebar-bg: var(--mf-config-sidebar-bg, #ffffff);
            --mf-sidebar-surface: var(--mf-config-sidebar-surface, #f7f8fa);
            --mf-sidebar-text: var(--mf-config-sidebar-text, #182230);
            --mf-sidebar-muted: var(--mf-config-sidebar-muted, #667085);
            --mf-sidebar-border: var(--mf-config-sidebar-border, #d9dee7);
            --mf-sidebar-input-bg: var(--mf-config-sidebar-input-bg, #ffffff);
            --mf-sidebar-input-text: var(--mf-config-sidebar-input-text, #182230);
            --mf-sidebar-placeholder: var(--mf-config-sidebar-placeholder, #98a2b3);
        }

        html[data-theme="light"],
        body[data-theme="light"],
        [data-theme="light"],
        [data-baseweb-theme="light"],
        [data-baseweb="baseweb"][data-theme="light"] {
            --mf-bg: #f7f8fa;
            --mf-surface: #ffffff;
            --mf-text: #182230;
            --mf-border: #d9dee7;
            --mf-muted: #667085;
            --mf-primary: #176b5f;
            --mf-primary-dark: #14564d;
            --mf-income: #15803d;
            --mf-expense: #b42318;
            --mf-warning: #b54708;
            --mf-input-bg: #ffffff;
            --mf-button-bg: #ffffff;
            --mf-placeholder: #98a2b3;
            --mf-sidebar-bg: #ffffff;
            --mf-sidebar-surface: #f7f8fa;
            --mf-sidebar-text: #182230;
            --mf-sidebar-muted: #667085;
            --mf-sidebar-border: #d9dee7;
            --mf-sidebar-input-bg: #ffffff;
            --mf-sidebar-input-text: #182230;
            --mf-sidebar-placeholder: #98a2b3;
        }

        html[data-theme="dark"],
        body[data-theme="dark"],
        [data-theme="dark"],
        [data-baseweb-theme="dark"],
        [data-baseweb="baseweb"][data-theme="dark"] {
            --mf-bg: #0b1118;
            --mf-surface: #111827;
            --mf-text: #f4f6fb;
            --mf-border: #344054;
            --mf-muted: #cdd5df;
            --mf-primary: #5dd6bc;
            --mf-primary-dark: #45bda8;
            --mf-income: #4ade80;
            --mf-expense: #fb7185;
            --mf-warning: #fbbf24;
            --mf-input-bg: #111827;
            --mf-button-bg: #111827;
            --mf-placeholder: #98a2b3;
            --mf-sidebar-bg: #101828;
            --mf-sidebar-surface: #1d2939;
            --mf-sidebar-text: #f2f4f7;
            --mf-sidebar-muted: #cdd5df;
            --mf-sidebar-border: #1d2939;
            --mf-sidebar-input-bg: #1d2939;
            --mf-sidebar-input-text: #f2f4f7;
            --mf-sidebar-placeholder: #98a2b3;
        }

        .stApp {
            background: var(--mf-bg);
            color: var(--mf-text);
        }

        [data-testid="stAppViewContainer"] {
            background: var(--mf-bg);
        }

        header[data-testid="stHeader"] {
            background: var(--mf-bg);
            color: var(--mf-text);
        }

        header[data-testid="stHeader"] *,
        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] [role="button"],
        [data-testid="stToolbar"],
        [data-testid="stToolbar"] *,
        [data-testid="stMainMenu"],
        [data-testid="stStatusWidget"] {
            color: var(--mf-text);
        }

        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] [role="button"],
        [data-testid="stToolbar"],
        [data-testid="stMainMenu"],
        [data-testid="stStatusWidget"] {
            background: transparent;
        }

        header[data-testid="stHeader"] svg {
            color: var(--mf-text);
            fill: currentColor;
        }

        [data-testid="stDecoration"] {
            background: var(--mf-primary);
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }

        .block-container,
        .block-container p,
        .block-container li,
        .block-container label,
        .block-container span,
        .block-container div,
        .block-container [data-testid="stMarkdownContainer"] {
            color: var(--mf-text);
        }

        .block-container [data-testid="stCaptionContainer"] p,
        .block-container .stCaption,
        .block-container small {
            color: var(--mf-muted);
        }

        section[data-testid="stSidebar"] {
            background: var(--mf-sidebar-bg);
            border-right: 1px solid var(--mf-sidebar-border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--mf-sidebar-text);
        }

        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
        section[data-testid="stSidebar"] .stMarkdown p {
            color: var(--mf-sidebar-muted);
        }

        h1, h2, h3,
        .block-container h1,
        .block-container h2,
        .block-container h3 {
            letter-spacing: 0;
            color: var(--mf-text);
        }

        .block-container a {
            color: var(--mf-primary);
        }

        .block-container input,
        .block-container textarea,
        .block-container select,
        .block-container [contenteditable="true"] {
            background: var(--mf-input-bg);
            color: var(--mf-text);
            caret-color: var(--mf-text);
        }

        .block-container input::placeholder,
        .block-container textarea::placeholder {
            color: var(--mf-placeholder);
            opacity: 1;
        }

        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] select,
        section[data-testid="stSidebar"] [contenteditable="true"] {
            background: var(--mf-sidebar-input-bg);
            color: var(--mf-sidebar-input-text);
            caret-color: var(--mf-sidebar-input-text);
        }

        section[data-testid="stSidebar"] input::placeholder,
        section[data-testid="stSidebar"] textarea::placeholder {
            color: var(--mf-sidebar-placeholder);
            opacity: 1;
        }

        .main-header {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            margin-bottom: 1.15rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--mf-border);
        }

        .main-header__eyebrow {
            color: var(--mf-primary);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .main-header__title {
            color: var(--mf-text);
            font-size: clamp(2rem, 5vw, 2.65rem);
            font-weight: 750;
            line-height: 1.05;
        }

        .main-header__subtitle {
            color: var(--mf-muted);
            font-size: 1rem;
            max-width: 760px;
        }

        .metric-card {
            background-color: var(--mf-surface);
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid var(--mf-border);
        }

        .insight-box {
            background-color: #12312c;
            color: #eef8f5;
            padding: 1.5rem;
            border-radius: 0.5rem;
            border-left: 4px solid #47b39c;
            margin: 1rem 0;
            font-size: 0.95rem;
            line-height: 1.7;
        }

        .insight-box p, .insight-box li, .insight-box ul, .insight-box ol {
            color: #eef8f5;
        }

        .insight-box strong, .insight-box b {
            color: #9ee4d2;
        }

        .empty-state {
            background: var(--mf-surface);
            border: 1px solid var(--mf-border);
            border-radius: 0.5rem;
            padding: 1.25rem;
            margin: 1rem 0 1.25rem;
        }

        .empty-state h3 {
            margin: 0 0 0.25rem 0;
            font-size: 1.15rem;
        }

        .empty-state p {
            margin: 0;
            color: var(--mf-muted);
        }

        [data-testid="stMetric"] {
            background: var(--mf-surface);
            border: 1px solid var(--mf-border);
            border-radius: 0.5rem;
            padding: 0.85rem 1rem;
        }

        [data-testid="stMetric"] label,
        [data-testid="stMetric"] [data-testid="stMetricLabel"],
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: var(--mf-text);
        }

        [data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: var(--mf-muted);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
            border-bottom: 1px solid var(--mf-border);
        }

        .stTabs [data-baseweb="tab"] {
            color: var(--mf-muted);
            border-radius: 0.45rem 0.45rem 0 0;
            padding: 0.65rem 0.9rem;
        }

        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] span {
            color: var(--mf-muted);
        }

        .stTabs [aria-selected="true"] {
            color: var(--mf-primary);
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span {
            color: var(--mf-primary);
        }

        div.stButton > button,
        div.stDownloadButton > button {
            border-radius: 0.45rem;
            border: 1px solid var(--mf-border);
            font-weight: 650;
            color: var(--mf-text);
            background: var(--mf-button-bg);
        }

        div.stButton > button *,
        div.stDownloadButton > button * {
            color: inherit;
        }

        div.stButton > button[kind="primary"] {
            background: var(--mf-primary);
            border-color: var(--mf-primary);
            color: #ffffff;
        }

        div.stButton > button[kind="primary"]:hover {
            background: var(--mf-primary-dark);
            border-color: var(--mf-primary-dark);
            color: #ffffff;
        }

        section[data-testid="stSidebar"] div.stButton > button,
        section[data-testid="stSidebar"] div.stDownloadButton > button {
            background: var(--mf-sidebar-surface);
            border: 1px solid var(--mf-sidebar-border);
            color: var(--mf-sidebar-text);
        }

        section[data-testid="stSidebar"] div.stButton > button:hover,
        section[data-testid="stSidebar"] div.stDownloadButton > button:hover {
            border-color: var(--mf-primary);
            color: var(--mf-primary);
        }

        section[data-testid="stSidebar"] [data-testid="stExpander"] {
            background: var(--mf-sidebar-surface);
            border: 1px solid var(--mf-sidebar-border);
            border-radius: 0.5rem;
        }

        section[data-testid="stSidebar"] hr {
            border-color: var(--mf-sidebar-border);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--mf-border);
            border-radius: 0.5rem;
            overflow: hidden;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
