"""Challenges page - weekly challenges and daily bonus goals."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database import get_logs_for_user
from styles import inject_custom_css, PRIMARY, SECONDARY_BG, BORDER
from utils import completion_score
from animations import render_radial_progress


def ensure_logged_in():
    if not st.session_state.get("user_id"):
        st.warning("Please log in from the home page first.")
        st.stop()


def main():
    st.set_page_config(
        page_title="Challenges | 75 Hard",
        page_icon="♠",
        layout="wide",
    )
    inject_custom_css()
    ensure_logged_in()

    with st.sidebar:
        st.markdown(f"**{st.session_state.display_name}**")
        if st.button("Log out", key="logout_challenges"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.display_name = None
            st.rerun()

    user_id = st.session_state.user_id
    st.title("Challenges")
    st.caption("Weekly challenges and daily bonus goals")

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    from_str = week_start.isoformat()
    to_str = today.isoformat()
    logs = get_logs_for_user(user_id, from_date=from_str, to_date=to_str, limit=10)

    if not logs:
        st.info("No logs this week yet. Start logging on the Daily Tracker to complete challenges.")
        st.stop()

    df = pd.DataFrame(logs)
    df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
    df["water_intake"] = pd.to_numeric(df["water_intake"], errors="coerce").fillna(0)
    w1 = pd.to_numeric(df["workout_1_duration"], errors="coerce").fillna(0)
    w2 = pd.to_numeric(df["workout_2_duration"], errors="coerce").fillna(0)
    df["workout_min"] = w1 + w2
    df["full"] = df.apply(completion_score, axis=1)

    total_water = float(df["water_intake"].sum())
    days_logged = len(df)
    # Consistency: need 7 days in a row; simplify to "days logged this week"
    consistency_days = days_logged
    total_workout = int(df["workout_min"].sum())
    full_days = int(df["full"].sum())

    # Weekly challenges
    st.subheader("This week's challenges")
    col1, col2, col3 = st.columns(3)

    with col1:
        target_water = 21
        progress_water = min(total_water, target_water)
        fig = render_radial_progress(progress_water, target_water, "Hydration", PRIMARY)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"""
            <div style="text-align: center; font-size: 0.9rem; color: #94a3b8;">
                <strong style="color: #f1f5f9;">Hydration Challenge</strong><br>
                Drink 21L this week<br>
                {total_water:.1f} / {target_water} L
            </div>
            """,
            unsafe_allow_html=True,
        )
        if total_water >= target_water:
            st.success("Done!")

    with col2:
        target_consistency = 7
        progress_consistency = min(consistency_days, target_consistency)
        fig = render_radial_progress(progress_consistency, target_consistency, "Consistency", "#6366f1")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"""
            <div style="text-align: center; font-size: 0.9rem; color: #94a3b8;">
                <strong style="color: #f1f5f9;">Consistency Challenge</strong><br>
                Log 7 days in a row<br>
                {consistency_days} / {target_consistency} days
            </div>
            """,
            unsafe_allow_html=True,
        )
        if consistency_days >= target_consistency:
            st.success("Done!")

    with col3:
        target_workout = 500
        progress_workout = min(total_workout, target_workout)
        fig = render_radial_progress(progress_workout, target_workout, "Intensity", "#fbbf24")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"""
            <div style="text-align: center; font-size: 0.9rem; color: #94a3b8;">
                <strong style="color: #f1f5f9;">Intensity Challenge</strong><br>
                500 min total workouts<br>
                {total_workout} / {target_workout} min
            </div>
            """,
            unsafe_allow_html=True,
        )
        if total_workout >= target_workout:
            st.success("Done!")

    st.markdown("---")
    st.subheader("Daily bonus goals")
    st.markdown(
        f"""
        <div style="background: {SECONDARY_BG}; border-radius: 8px; padding: 1rem; border: 1px solid {BORDER}; margin-bottom: 0.5rem;">
            <div style="font-weight: 600; color: #f1f5f9;">Morning Logger</div>
            <div style="font-size: 0.9rem; color: #94a3b8;">Log your day before 10 AM — +10 XP</div>
        </div>
        <div style="background: {SECONDARY_BG}; border-radius: 8px; padding: 1rem; border: 1px solid {BORDER};">
            <div style="font-weight: 600; color: #f1f5f9;">Overachiever</div>
            <div style="font-size: 0.9rem; color: #94a3b8;">2 workouts + 4L water + 30 min reading in one day — +30 XP</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Bonus XP is applied when you hit these goals on a logged day. Keep logging!")


if __name__ == "__main__":
    main()
