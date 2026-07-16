import streamlit as st


def render():
    st.markdown(
        """
        <div class="main-header">
            <div class="main-header__eyebrow">Secure local finance workspace</div>
            <div class="main-header__title">MoneyFlow</div>
            <div class="main-header__subtitle">
                Sign in to analyse statements, manage budgets, and review AI-assisted financial insights.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")

        with st.form("login_form"):
            username = st.text_input(
                "Username", key="login_username", placeholder="Enter your username"
            )
            password = st.text_input(
                "Password", type="password", key="login_password", placeholder="Enter your password"
            )
            submit = st.form_submit_button("Login", type="primary", width="stretch")

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, message = st.session_state.auth_handler.authenticate_user(
                        username, password
                    )
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tab2:
        st.subheader("Create account")

        st.info("""
        **Username Requirements:**
        - At least 3 characters long
        - No spaces (use underscores instead)
        - Letters, numbers, and underscores only
        - Must not start with a number

        **Password Requirements:**
        - At least 6 characters long
        - Must contain uppercase letter (A-Z)
        - Must contain lowercase letter (a-z)
        - Must contain at least one number (0-9)
        """)

        with st.form("register_form"):
            new_username = st.text_input(
                "Username",
                key="register_username",
                placeholder="e.g., john_doe123",
                help="No spaces allowed - use underscores (_) to separate words",
            )
            new_email = st.text_input(
                "Email (optional)", key="register_email", placeholder="your.email@example.com"
            )
            new_password = st.text_input(
                "Password",
                type="password",
                key="register_password",
                placeholder="At least 6 characters with upper, lower, and number",
                help="Mix of uppercase, lowercase, and numbers for security",
            )
            new_password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                key="register_password_confirm",
                placeholder="Re-type your password",
            )
            employment_status = st.selectbox(
                "Employment Status",
                options=[
                    "",
                    "Student",
                    "Full-time Employed",
                    "Part-time Employed",
                    "Self-employed",
                    "Business Owner",
                    "Unemployed",
                    "Retired",
                ],
                key="register_employment_status",
                help="This helps us tailor financial insights to your situation",
            )
            submit = st.form_submit_button("Register", type="primary", width="stretch")

            if submit:
                if not new_username or not new_password:
                    st.error("Username and password are required")
                elif new_password != new_password_confirm:
                    st.error("Passwords do not match")
                else:
                    success, message = st.session_state.auth_handler.register_user(
                        new_username, new_password, new_email, employment_status
                    )
                    if success:
                        st.success(message)
                        st.info("Please switch to the Login tab to sign in")
                    else:
                        st.error(message)

    st.markdown(
        """
        <div class="empty-state">
            <h3>Privacy model</h3>
            <p>Authentication protects local sessions, statement data stays on this machine, and AI analysis is optional and, when enabled, runs through your configured local or OpenAI-compatible model.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
