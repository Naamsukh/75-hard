"""Dashboard page - gamified progress: hero, XP, badges, 75-day calendar, personal records."""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import get_logs_for_user, list_users, get_achievements_for_user, update_user_xp_level, insert_achievement
from styles import inject_custom_css
from utils import completion_score, compute_streak
from gamification import (
    calculate_xp,
    get_level,
    xp_progress_in_level,
    get_metrics_for_badges,
    check_achievements,
    get_personal_records,
)
from animations import render_xp_bar, render_badge_shelf, render_streak_flame

# Theme colors for charts
PRIMARY = "#10b981"
BG = "#0f172a"
SECONDARY_BG = "#1e293b"
GRID = "#334155"


def ensure_logged_in():
    if not st.session_state.get("user_id"):
        st.warning("Please log in from the home page first.")
        st.stop()


def metric_card(icon: str, value: str, label: str, sub: str = "", border_color: str = PRIMARY):
    """Render a custom metric card with icon, value, label, and optional sub (e.g. Best: 12)."""
    sub_html = f'<div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div style="
            background: {SECONDARY_BG};
            border-radius: 8px;
            padding: 1.25rem;
            border: 1px solid #334155;
            border-top: 4px solid {border_color};
            transition: box-shadow 0.2s ease;
        ">
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{icon}</div>
            <div style="font-size: 1.75rem; font-weight: 700; color: #f1f5f9;">{value}</div>
            <div style="font-size: 0.85rem; color: #94a3b8;">{label}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_theme(fig, primary_color: str = PRIMARY):
    """Apply dark theme and emerald accent to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=SECONDARY_BG,
        font=dict(color="#f1f5f9"),
        xaxis=dict(gridcolor=GRID, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, linecolor=GRID),
        margin=dict(t=40, b=40, l=40, r=40),
    )
    fig.update_traces(marker_color=primary_color)
    return fig


def render_75_calendar(log_dates: set, full_dates: set, start: date, end: date):
    """Render a GitHub-style calendar grid: green if logged, darker if full completion."""
    days = []
    current = start
    while current <= end:
        logged = current in log_dates
        full = current in full_dates
        color = "#10b981" if full else ("#334155" if logged else "#1e293b")
        days.append((current, color))
        current += timedelta(days=1)
    # 7 columns (weeks)
    rows = []
    for i in range(0, len(days), 7):
        chunk = days[i : i + 7]
        row_html = "".join(
            f'<div style="width: 14px; height: 14px; background: {c}; border-radius: 2px; margin: 1px;" title="{d}"></div>'
            for d, c in chunk
        )
        rows.append(f'<div style="display: flex; gap: 2px;">{row_html}</div>')
    st.markdown(
        f"""
        <div style="
            background: {SECONDARY_BG};
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid #334155;
        ">
            <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem;">75-Day style calendar (green = full day, gray = logged)</div>
            <div style="display: flex; flex-direction: column; gap: 2px;">{"".join(rows)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="Dashboard | 75 Hard",
        page_icon="♠",
        layout="wide",
    )
    inject_custom_css()
    ensure_logged_in()

    with st.sidebar:
        st.markdown(f"**{st.session_state.display_name}**")
        if st.button("Log out", key="logout_dashboard"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.display_name = None
            st.rerun()

    user_id = st.session_state.user_id
    display_name = st.session_state.display_name

    st.title("Dashboard")
    st.caption(f"Your progress — **{display_name}**")

    # Load logs (last 365 days)
    to_date = date.today().isoformat()
    from_date = (date.today() - timedelta(days=365)).isoformat()
    logs = get_logs_for_user(user_id, from_date=from_date, to_date=to_date, limit=400)

    if not logs:
        st.info("No logs yet. Start logging on the Daily Tracker.")
        st.stop()

    df = pd.DataFrame(logs)
    df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
    log_dates_list = df["log_date"].tolist()
    log_dates_set = set(log_dates_list)
    full_completion = df.apply(completion_score, axis=1)
    full_dates_set = set(df.loc[full_completion].log_date.tolist())
    complete_days = full_completion.sum()
    streak = compute_streak(log_dates_list)
    total_days = len(df)
    completion_pct = round(100 * complete_days / total_days, 1) if total_days else 0

    # XP and level
    total_xp = calculate_xp(logs, int(complete_days))
    level_num, level_title = get_level(total_xp)
    xp_in_level, xp_for_next, _ = xp_progress_in_level(total_xp)
    try:
        update_user_xp_level(user_id, total_xp, level_num)
    except Exception:
        pass  # columns may not exist yet
    xp_bar_placeholder = st.empty()
    with xp_bar_placeholder.container():
        render_xp_bar(total_xp, xp_in_level, xp_for_next, level_num, level_title)

    # Achievements: check and insert new badges
    metrics_for_badges = get_metrics_for_badges(logs)
    try:
        earned = get_achievements_for_user(user_id)
    except Exception:
        earned = []
    already_earned = {e["badge_type"] for e in earned}
    newly = check_achievements(metrics_for_badges, already_earned)
    for bt in newly:
        try:
            insert_achievement(user_id, bt)
            earned.append({"badge_type": bt})
        except Exception:
            pass

    # Hero row: Level, Streak, Rank, Badges
    users = list_users()
    other_xp = 0
    for u in users:
        if u["id"] != user_id:
            other_xp = u.get("xp") or 0
            break
    rank = "#1" if total_xp >= other_xp else "#2"
    streak_emoji = render_streak_flame(streak)
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {SECONDARY_BG} 0%, #334155 100%);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border: 1px solid #334155;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        ">
            <div>
                <div style="font-size: 1.1rem; color: #94a3b8;">Level {level_num} {level_title}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f1f5f9;">{display_name}</div>
            </div>
            <div style="display: flex; gap: 1.5rem; font-size: 0.95rem;">
                <span>{streak_emoji} <strong>{streak}</strong> day streak</span>
                <span>Rank <strong>{rank}</strong> vs partner</span>
                <span>🏆 <strong>{len(earned)}</strong> badges</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stat cards with personality (best streak, +this week)
    pr = get_personal_records(logs)
    week_ago = date.today() - timedelta(days=7)
    days_this_week = sum(1 for d in log_dates_list if d >= week_ago)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            render_streak_flame(streak) or "🔥",
            f"{streak} days",
            "Current streak",
            sub=f"Best: {pr['best_streak']} days",
            border_color=PRIMARY,
        )
    with col2:
        metric_card("📅", str(total_days), "Total days logged", sub=f"+{days_this_week} this week", border_color="#6366f1")
    with col3:
        metric_card("✓", str(int(complete_days)), "Full days (2 workouts + water + reading)", sub=f"PR: {pr['full_completion_days']}", border_color="#fbbf24")
    with col4:
        metric_card("%", f"{completion_pct}%", "Completion rate", border_color=PRIMARY)

    st.markdown("---")

    # Badge shelf
    st.subheader("Badges")
    render_badge_shelf(earned)
    st.markdown("---")

    # 75-day calendar and personal records
    col_cal, col_pr = st.columns([1, 1])
    with col_cal:
        st.subheader("Activity calendar")
        end = date.today()
        start = end - timedelta(days=83)
        render_75_calendar(log_dates_set, full_dates_set, start, end)
    with col_pr:
        st.subheader("Personal records")
        st.markdown(
            f"""
            <div style="background: {SECONDARY_BG}; border-radius: 8px; padding: 1rem; border: 1px solid #334155;">
                <div style="color: #94a3b8; font-size: 0.9rem;">Best streak: <strong style="color: #f1f5f9;">{pr['best_streak']} days</strong></div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Max water in a day: <strong style="color: #f1f5f9;">{pr['max_water_L']:.1f} L</strong></div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Max workout in a day: <strong style="color: #f1f5f9;">{pr['max_workout_min']} min</strong></div>
                <div style="color: #94a3b8; font-size: 0.9rem;">Max reading in a day: <strong style="color: #f1f5f9;">{pr['max_reading_min']} min</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("---")

    # Charts
    df_sorted = df.sort_values("log_date").reset_index(drop=True)
    df_sorted["water_intake"] = pd.to_numeric(df_sorted["water_intake"], errors="coerce").fillna(0)
    df_sorted["reading_time"] = pd.to_numeric(df_sorted["reading_time"], errors="coerce").fillna(0)
    w1_dur = pd.to_numeric(df_sorted["workout_1_duration"], errors="coerce").fillna(0)
    w2_dur = pd.to_numeric(df_sorted["workout_2_duration"], errors="coerce").fillna(0)
    df_sorted["total_workout_min"] = w1_dur + w2_dur

    col_a, col_b = st.columns(2)
    with col_a:
        fig_water = px.line(df_sorted, x="log_date", y="water_intake", title="Water intake (L)", labels={"log_date": "Date", "water_intake": "Liters"})
        fig_water.update_traces(fill="tozeroy", line=dict(color=PRIMARY))
        apply_chart_theme(fig_water)
        st.plotly_chart(fig_water, use_container_width=True)
    with col_b:
        fig_reading = px.line(df_sorted, x="log_date", y="reading_time", title="Reading time (minutes)", labels={"log_date": "Date", "reading_time": "Minutes"})
        fig_reading.update_traces(fill="tozeroy", line=dict(color=PRIMARY))
        apply_chart_theme(fig_reading)
        st.plotly_chart(fig_reading, use_container_width=True)

    fig_workout = go.Figure(
        data=[go.Bar(x=df_sorted["log_date"], y=df_sorted["total_workout_min"], name="Total workout (min)", marker_color=PRIMARY, marker_line_width=0)]
    )
    fig_workout.update_layout(title="Workout duration (minutes per day)", xaxis_title="Date", yaxis_title="Minutes", showlegend=False)
    apply_chart_theme(fig_workout)
    st.plotly_chart(fig_workout, use_container_width=True)

    # Recent logs table
    st.subheader("Last 7 days")
    recent = df_sorted.tail(7).iloc[::-1].copy()
    recent["status"] = recent.apply(completion_score, axis=1)
    recent["status"] = recent["status"].map({True: "✓", False: "—"})
    display_cols = ["log_date", "status", "breakfast", "lunch", "dinner", "workout_1", "workout_2", "water_intake", "reading_time"]
    available = [c for c in display_cols if c in recent.columns]
    st.dataframe(recent[available], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
