import streamlit as st

from moneyflow.ui.components.logo_animation import render_logo_animation


def show_landing_page():

    st.markdown(
        """
    <style>
        .landing-title {
            font-size: 3.25rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 0.5rem;
            letter-spacing: 0;
            text-align: center;
        }

        .landing-logo-wrap {
            max-width: 520px;
            margin: 0 auto 0.35rem;
        }

        .landing-title .flow-blue {
            color: #176b5f;
        }

        .hero-tagline {
            font-size: 1.25rem;
            opacity: 0.85;
            margin-bottom: 1.5rem;
            text-align: center
        }

        .section-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0;
            opacity: 0.6;
            margin-top: 2rem;
            margin-bottom: 1rem;
            text-align: center;
        }

        .stAlert p {
        text-align: center;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    _, hero_col, _ = st.columns([1, 2, 1])

    with hero_col:
        st.markdown('<div class="landing-logo-wrap">', unsafe_allow_html=True)
        render_logo_animation(height=300)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="landing-title">
                <span>Money</span><span class="flow-blue">Flow</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="hero-tagline">Track spending, uncover patterns, and better understand your financial habits.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Get Started", type="primary", width="stretch"):
            st.session_state.show_landing = False
            st.rerun()

        st.info("Financial data is processed locally and is not shared with third parties.")

    # How it works section
    st.markdown('<div class="section-label">How it works</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)

    with s1:
        with st.container(border=True):
            st.markdown("**1. Upload**")
            st.caption("Upload your bank transaction CSV file.")

    with s2:
        with st.container(border=True):
            st.markdown("**2. Analyse**")
            st.caption("Your transactions are categorised automatically.")

    with s3:
        with st.container(border=True):
            st.markdown("**3. Get Insights**")
            st.caption("Get AI-driven insights and visual breakdowns of your spending.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Features section
    st.markdown('<div class="section-label">Features</div>', unsafe_allow_html=True)
    f1, f2 = st.columns(2)

    with f1:
        with st.container(border=True):
            st.markdown("**Financial Overview**")
            st.caption("View total income, expenses and net cashflow in one dashboard.")

        with st.container(border=True):
            st.markdown("**Budgeting & Saving Goals**")
            st.caption(
                "Set category budgets, compare actual vs planned spending. Set monthly savings and emergency fund goals."
            )

        with st.container(border=True):
            st.markdown("**Unusual Transactions**")
            st.caption("Detects abnormal or large transactions for review.")

    with f2:
        with st.container(border=True):
            st.markdown("**AI Insights**")
            st.caption(
                "Optional AI-generated financial advice, budgeting tips, and answers to custom questions via a local or OpenAI-compatible model."
            )

        with st.container(border=True):
            st.markdown("**Subscription & Recurring Detection**")
            st.caption(
                "Automatically detects subscriptions and recurring bills. See upcoming payments at a glance."
            )

        with st.container(border=True):
            st.markdown("**Visualisations**")
            st.caption(
                "Visualise spending by category and compare income against expenses each month."
            )
