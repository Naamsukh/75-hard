"""75 Hard Challenge Tracker - Main entry point with login."""

import streamlit as st

from auth import verify_password
from database import get_user_by_username
from styles import inject_custom_css


def init_session_state():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "display_name" not in st.session_state:
        st.session_state.display_name = None


def login_form():
    st.markdown(
        """
        <style>
        .login-box {
            max-width: 420px;
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 12px;
            background: #1e293b;
            border: 1px solid #334155;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        .title {
            text-align: center;
            color: #10b981;
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            font-weight: 700;
        }
        </style>
        <div class="login-box">
            <h1 class="title">75 Hard Challenge Tracker</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Log in")
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
                return
            user = get_user_by_username(username.strip())
            if user and verify_password(password, user["password_hash"]):
                st.session_state.user = user
                st.session_state.user_id = user["id"]
                st.session_state.display_name = user["display_name"]
                st.rerun()
            else:
                st.error("Invalid username or password.")


def main():
    st.set_page_config(
        page_title="75 Hard Challenge Tracker",
        page_icon="♠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_custom_css()
    init_session_state()

    if st.session_state.user is None:
        login_form()
        return

    # Logged in: show user and logout in sidebar (Streamlit auto-adds page nav)
    with st.sidebar:
        st.markdown(f"**{st.session_state.display_name}**")
        if st.button("Log out"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.display_name = None
            st.rerun()

    st.title("75 Hard Challenge Tracker")
    st.markdown(f"Welcome, **{st.session_state.display_name}**.")
    st.markdown("Use the sidebar to open **Daily Tracker** to log your day or **Dashboard** to view progress.")


if __name__ == "__main__":
    main()
