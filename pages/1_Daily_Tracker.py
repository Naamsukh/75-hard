"""Daily Tracker page - log meals, workouts, water, reading, notes."""

from datetime import date, timedelta

import streamlit as st

from database import get_log, upsert_log
from styles import inject_custom_css


def ensure_logged_in():
    if not st.session_state.get("user_id"):
        st.warning("Please log in from the home page first.")
        st.stop()


def main():
    st.set_page_config(
        page_title="Daily Tracker | 75 Hard",
        page_icon="♠",
        layout="wide",
    )
    inject_custom_css()
    ensure_logged_in()

    with st.sidebar:
        st.markdown(f"**{st.session_state.display_name}**")
        if st.button("Log out", key="logout_tracker"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.display_name = None
            st.rerun()

    user_id = st.session_state.user_id
    display_name = st.session_state.display_name

    st.title("Daily Tracker")
    st.caption(f"Logged in as **{display_name}**")

    # Date picker
    log_date = st.date_input(
        "Date",
        value=date.today(),
        min_value=date.today() - timedelta(days=365),
        max_value=date.today(),
        key="daily_tracker_date",
    )
    log_date_str = log_date.isoformat()

    # Load existing log
    existing = get_log(user_id, log_date_str)

    with st.form("daily_log_form"):
        st.subheader("Meals")
        breakfast = st.text_input(
            "Breakfast",
            value=existing.get("breakfast") or "" if existing else "",
            placeholder="What did you have for breakfast?",
        )
        lunch = st.text_input(
            "Lunch",
            value=existing.get("lunch") or "" if existing else "",
            placeholder="What did you have for lunch?",
        )
        dinner = st.text_input(
            "Dinner",
            value=existing.get("dinner") or "" if existing else "",
            placeholder="What did you have for dinner?",
        )

        st.subheader("Workouts")
        col1, col2 = st.columns(2)
        with col1:
            workout_1 = st.text_input(
                "Workout 1",
                value=existing.get("workout_1") or "" if existing else "",
                placeholder="e.g. Running, Gym",
            )
            workout_1_duration = st.number_input(
                "Duration (minutes)",
                min_value=0,
                max_value=300,
                value=int(existing.get("workout_1_duration") or 0) if existing else 0,
                key="w1_dur",
            )
        with col2:
            workout_2 = st.text_input(
                "Workout 2",
                value=existing.get("workout_2") or "" if existing else "",
                placeholder="e.g. Yoga, Walk",
            )
            workout_2_duration = st.number_input(
                "Duration (minutes)",
                min_value=0,
                max_value=300,
                value=int(existing.get("workout_2_duration") or 0) if existing else 0,
                key="w2_dur",
            )

        st.subheader("Water & Reading")
        col_water, col_reading = st.columns(2)
        with col_water:
            water_intake = st.number_input(
                "Water intake (liters)",
                min_value=0.0,
                max_value=10.0,
                value=float(existing.get("water_intake") or 0) if existing else 0.0,
                step=0.5,
                format="%.1f",
                key="water",
            )
        with col_reading:
            reading_time = st.number_input(
                "Reading time (minutes)",
                min_value=0,
                max_value=240,
                value=int(existing.get("reading_time") or 0) if existing else 0,
                key="reading",
            )

        st.subheader("Notes")
        notes = st.text_area(
            "Daily notes",
            value=existing.get("notes") or "" if existing else "",
            placeholder="Reflections, mood, or anything else...",
            height=100,
        )

        submitted = st.form_submit_button("Save")
        if submitted:
            try:
                upsert_log(
                    user_id=user_id,
                    log_date=log_date_str,
                    breakfast=breakfast.strip() or None,
                    lunch=lunch.strip() or None,
                    dinner=dinner.strip() or None,
                    workout_1=workout_1.strip() or None,
                    workout_1_duration=workout_1_duration if workout_1_duration else None,
                    workout_2=workout_2.strip() or None,
                    workout_2_duration=workout_2_duration if workout_2_duration else None,
                    water_intake=water_intake if water_intake else None,
                    reading_time=reading_time if reading_time else None,
                    notes=notes.strip() or None,
                )
                st.success("Daily log saved.")
            except Exception as e:
                st.error(f"Could not save: {e}")


if __name__ == "__main__":
    main()
