"""Leaderboard page - battle score, radial progress, comparison charts, battle mode."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database import get_logs_for_user, list_users
from styles import PRIMARY, SECONDARY_BG, BORDER, HIGHLIGHT, inject_custom_css
from utils import completion_score, compute_streak, longest_streak_in_range
from gamification import calculate_points
from animations import render_radial_progress, render_comparison_chart


def ensure_logged_in():
    if not st.session_state.get("user_id"):
        st.warning("Please log in from the home page first.")
        st.stop()


def compute_metrics(logs: list, from_date: date, to_date: date, use_current_streak: bool):
    """Compute leaderboard metrics for one user in a date range."""
    if not logs:
        return {
            "days_logged": 0,
            "streak": 0,
            "full_completion_days": 0,
            "total_workout_min": 0,
            "total_water_L": 0.0,
            "total_reading_min": 0,
        }
    df = pd.DataFrame(logs)
    df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
    log_dates = df["log_date"].tolist()

    if use_current_streak:
        streak = compute_streak(log_dates)
    else:
        streak = longest_streak_in_range(log_dates, from_date, to_date)

    full_completion = df.apply(completion_score, axis=1).sum()
    w1 = pd.to_numeric(df["workout_1_duration"], errors="coerce").fillna(0)
    w2 = pd.to_numeric(df["workout_2_duration"], errors="coerce").fillna(0)
    total_workout_min = int((w1 + w2).sum())
    total_water_L = float(pd.to_numeric(df["water_intake"], errors="coerce").fillna(0).sum())
    total_reading_min = int(pd.to_numeric(df["reading_time"], errors="coerce").fillna(0).sum())

    return {
        "days_logged": len(df),
        "streak": streak,
        "full_completion_days": int(full_completion),
        "total_workout_min": total_workout_min,
        "total_water_L": total_water_L,
        "total_reading_min": total_reading_min,
    }


def who_wins(val_a, val_b):
    if val_a > val_b:
        return "a"
    if val_b > val_a:
        return "b"
    return "tie"


def render_head_to_head(
    metric_label: str,
    name_a: str,
    value_a,
    name_b: str,
    value_b,
    unit: str = "",
    format_val=None,
    show_radial: bool = False,
):
    """Head-to-head with optional radial progress."""
    if format_val is None:
        def format_val(x):
            return str(x)
    max_val = max(value_a, value_b, 1)
    pct_a = value_a / max_val
    pct_b = value_b / max_val
    winner = who_wins(value_a, value_b)

    st.markdown(f"**{metric_label}**")
    col1, col2 = st.columns(2)

    with col1:
        is_leader = winner == "a"
        is_tie = winner == "tie"
        badge = "LEADING" if is_leader else ("TIE" if is_tie else "")
        border_color = PRIMARY if is_leader else (BORDER if not is_tie else HIGHLIGHT)
        st.markdown(
            f"""
            <div style="
                background: {SECONDARY_BG};
                border-radius: 8px;
                padding: 1rem;
                border: 1px solid {BORDER};
                border-left: 4px solid {border_color};
                margin-bottom: 0.5rem;
            ">
                <div style="font-size: 0.8rem; color: #94a3b8;">{name_a}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f1f5f9;">{format_val(value_a)}{unit}</div>
                <div style="font-size: 0.75rem; color: {PRIMARY if is_leader else '#64748b'}; font-weight: 600;">{badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if show_radial:
            fig_a = render_radial_progress(value_a, max_val, name_a[:8], PRIMARY)
            st.plotly_chart(fig_a, use_container_width=True, config={"displayModeBar": False})
        else:
            st.progress(float(pct_a))

    with col2:
        is_leader = winner == "b"
        is_tie = winner == "tie"
        badge = "LEADING" if is_leader else ("TIE" if is_tie else "")
        border_color = PRIMARY if is_leader else (BORDER if not is_tie else HIGHLIGHT)
        st.markdown(
            f"""
            <div style="
                background: {SECONDARY_BG};
                border-radius: 8px;
                padding: 1rem;
                border: 1px solid {BORDER};
                border-left: 4px solid {border_color};
                margin-bottom: 0.5rem;
            ">
                <div style="font-size: 0.8rem; color: #94a3b8;">{name_b}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f1f5f9;">{format_val(value_b)}{unit}</div>
                <div style="font-size: 0.75rem; color: {PRIMARY if is_leader else '#64748b'}; font-weight: 600;">{badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if show_radial:
            fig_b = render_radial_progress(value_b, max_val, name_b[:8], "#6366f1")
            st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})
        else:
            st.progress(float(pct_b))

    st.markdown("---")


def main():
    st.set_page_config(
        page_title="Leaderboard | 75 Hard",
        page_icon="♠",
        layout="wide",
    )
    inject_custom_css()
    ensure_logged_in()

    with st.sidebar:
        st.markdown(f"**{st.session_state.display_name}**")
        if st.button("Log out", key="logout_leaderboard"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.display_name = None
            st.rerun()

    st.title("Leaderboard")
    st.caption("Who is winning — last 7 days, last 30 days, or overall")

    users = list_users()
    if len(users) < 2:
        st.info("Leaderboard needs at least two users.")
        st.stop()

    time_range = st.radio(
        "Time range",
        options=["Last 7 days", "Last 30 days", "Overall"],
        horizontal=True,
        key="leaderboard_range",
    )

    today = date.today()
    if time_range == "Last 7 days":
        from_date = today - timedelta(days=6)
        to_date = today
        use_current_streak = False
    elif time_range == "Last 30 days":
        from_date = today - timedelta(days=29)
        to_date = today
        use_current_streak = False
    else:
        from_date = today - timedelta(days=365)
        to_date = today
        use_current_streak = True

    from_str = from_date.isoformat()
    to_str = to_date.isoformat()

    logs_a = get_logs_for_user(users[0]["id"], from_date=from_str, to_date=to_str, limit=400)
    logs_b = get_logs_for_user(users[1]["id"], from_date=from_str, to_date=to_str, limit=400)
    metrics_a = compute_metrics(logs_a, from_date, to_date, use_current_streak)
    metrics_b = compute_metrics(logs_b, from_date, to_date, use_current_streak)

    name_a = users[0]["display_name"]
    name_b = users[1]["display_name"]
    pts_a = calculate_points(metrics_a)
    pts_b = calculate_points(metrics_b)
    winner_pts = "a" if pts_a >= pts_b else "b"
    advantage = abs(pts_a - pts_b)
    my_id = st.session_state.user_id
    i_am_a = users[0]["id"] == my_id
    i_win = (winner_pts == "a" and i_am_a) or (winner_pts == "b" and not i_am_a)

    # Battle score hero
    crown_a = " 👑" if winner_pts == "a" else ""
    crown_b = " 👑" if winner_pts == "b" else ""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {SECONDARY_BG} 0%, #334155 100%);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border: 1px solid {BORDER};
        ">
            <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 0.5rem;">BATTLE SCORE</div>
            <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <span style="color: #f1f5f9; font-size: 1.2rem;"><strong>{name_a}</strong>{crown_a}: {pts_a} pts</span>
                <span style="color: #64748b;">|</span>
                <span style="color: #f1f5f9; font-size: 1.2rem;"><strong>{name_b}</strong>{crown_b}: {pts_b} pts</span>
            </div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem; color: {PRIMARY};">+{advantage} pts advantage</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Trash talk / motivational message
    if i_win and advantage > 0:
        st.success(f"You're ahead by {advantage} points! Keep it up!")
    elif not i_win and advantage > 0:
        st.warning(f"You're behind by {advantage} points. Time to push harder!")
    else:
        st.info("You're tied! Every log counts.")

    st.markdown("---")

    # Comparison chart: water or workout over time
    if logs_a and logs_b:
        df_a = pd.DataFrame(logs_a).sort_values("log_date")
        df_b = pd.DataFrame(logs_b).sort_values("log_date")
        df_a["log_date"] = pd.to_datetime(df_a["log_date"])
        df_b["log_date"] = pd.to_datetime(df_b["log_date"])
        df_a["water"] = pd.to_numeric(df_a["water_intake"], errors="coerce").fillna(0)
        df_b["water"] = pd.to_numeric(df_b["water_intake"], errors="coerce").fillna(0)
        fig = render_comparison_chart(
            df_a["log_date"].tolist(),
            df_a["water"].tolist(),
            df_b["log_date"].tolist(),
            df_b["water"].tolist(),
            name_a,
            name_b,
            "Water intake (L) — comparison",
            "Liters",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("---")

    # Wins tally
    wins_a = sum(
        [
            1 if metrics_a["days_logged"] > metrics_b["days_logged"] else 0,
            1 if metrics_a["streak"] > metrics_b["streak"] else 0,
            1 if metrics_a["full_completion_days"] > metrics_b["full_completion_days"] else 0,
            1 if metrics_a["total_workout_min"] > metrics_b["total_workout_min"] else 0,
            1 if metrics_a["total_water_L"] > metrics_b["total_water_L"] else 0,
            1 if metrics_a["total_reading_min"] > metrics_b["total_reading_min"] else 0,
        ]
    )
    wins_b = sum(
        [
            1 if metrics_b["days_logged"] > metrics_a["days_logged"] else 0,
            1 if metrics_b["streak"] > metrics_a["streak"] else 0,
            1 if metrics_b["full_completion_days"] > metrics_a["full_completion_days"] else 0,
            1 if metrics_b["total_workout_min"] > metrics_a["total_workout_min"] else 0,
            1 if metrics_b["total_water_L"] > metrics_a["total_water_L"] else 0,
            1 if metrics_b["total_reading_min"] > metrics_a["total_reading_min"] else 0,
        ]
    )
    st.markdown(
        f"""
        <div style="
            background: {SECONDARY_BG};
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
            border: 1px solid {BORDER};
            display: flex;
            justify-content: space-around;
            text-align: center;
        ">
            <span style="color: #f1f5f9;"><strong>{name_a}</strong>: {wins_a} wins</span>
            <span style="color: #64748b;">|</span>
            <span style="color: #f1f5f9;"><strong>{name_b}</strong>: {wins_b} wins</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Head-to-head with radial for streak
    render_head_to_head("Days logged", name_a, metrics_a["days_logged"], name_b, metrics_b["days_logged"], " days")
    render_head_to_head("Streak", name_a, metrics_a["streak"], name_b, metrics_b["streak"], " days", show_radial=True)
    render_head_to_head(
        "Full completion days",
        name_a,
        metrics_a["full_completion_days"],
        name_b,
        metrics_b["full_completion_days"],
        " days",
    )
    render_head_to_head(
        "Total workout (min)",
        name_a,
        metrics_a["total_workout_min"],
        name_b,
        metrics_b["total_workout_min"],
        " min",
    )
    render_head_to_head(
        "Total water (L)",
        name_a,
        metrics_a["total_water_L"],
        name_b,
        metrics_b["total_water_L"],
        " L",
        format_val=lambda x: f"{x:.1f}",
    )
    render_head_to_head(
        "Total reading (min)",
        name_a,
        metrics_a["total_reading_min"],
        name_b,
        metrics_b["total_reading_min"],
        " min",
    )


if __name__ == "__main__":
    main()
