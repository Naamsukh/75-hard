"""UI components for gamification: XP bar, badges, streak flame, radial progress, comparison charts."""

import streamlit as st
import plotly.graph_objects as go

from styles import PRIMARY, SECONDARY_BG, BORDER, TEXT


def render_xp_bar(current_xp: int, xp_in_level: int, xp_for_next: int, level: int, title: str):
    """Render XP progress bar within current level."""
    pct = min(100, (xp_in_level / xp_for_next * 100)) if xp_for_next else 0
    st.markdown(
        f"""
        <div style="
            background: {SECONDARY_BG};
            border-radius: 8px;
            padding: 0.75rem 1rem;
            border: 1px solid {BORDER};
            margin-bottom: 0.5rem;
        ">
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.35rem;">
                <span>Level {level} — {title}</span>
                <span>{xp_in_level} / {xp_for_next} XP</span>
            </div>
            <div style="background: #334155; border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, {PRIMARY}, #6366f1); height: 100%; width: {pct}%; border-radius: 6px; transition: width 0.5s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badge_shelf(badges: list[dict], columns: int = 4):
    """Render a grid of earned badges (list of dicts with badge_type, earned_at)."""
    from gamification import get_badge_info
    if not badges:
        st.markdown(
            f'<div style="background: {SECONDARY_BG}; border-radius: 8px; padding: 1rem; border: 1px solid {BORDER}; color: #94a3b8; font-size: 0.9rem;">No badges yet. Log days and hit milestones to earn them!</div>',
            unsafe_allow_html=True,
        )
        return
    items = []
    for b in badges:
        bt = b.get("badge_type", "")
        name, desc, icon = get_badge_info(bt)
        items.append(f"""
            <div style="
                background: {SECONDARY_BG};
                border-radius: 8px;
                padding: 0.75rem;
                border: 1px solid {BORDER};
                text-align: center;
            ">
                <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{icon}</div>
                <div style="font-size: 0.8rem; font-weight: 600; color: {TEXT};">{name}</div>
                <div style="font-size: 0.7rem; color: #94a3b8;">{desc}</div>
            </div>
        """)
    # Simple row of badges
    st.markdown(
        f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def render_streak_flame(days: int) -> str:
    """Return emoji/size for streak (for use in headers)."""
    if days <= 0:
        return ""
    if days >= 30:
        return "🔥🔥🔥"
    if days >= 7:
        return "🔥🔥"
    return "🔥"


def render_radial_progress(value: float, max_val: float, label: str, color: str = PRIMARY):
    """Render a donut chart as radial progress. max_val must be > 0."""
    if max_val <= 0:
        pct = 0
    else:
        pct = min(100, 100 * value / max_val)
    fig = go.Figure(
        data=[
            go.Pie(
                values=[pct, 100 - pct],
                hole=0.7,
                marker=dict(colors=[color, "#334155"]),
                textinfo="none",
                hoverinfo="none",
                direction="clockwise",
                rotation=90,
            )
        ]
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=120,
        annotations=[
            dict(
                text=f"<b>{int(value)}</b><br>{label}",
                x=0.5,
                y=0.5,
                font=dict(size=12, color=TEXT),
                showarrow=False,
            )
        ],
    )
    return fig


def render_comparison_chart(
    dates_a: list,
    values_a: list,
    dates_b: list,
    values_b: list,
    name_a: str,
    name_b: str,
    title: str,
    y_label: str,
):
    """Side-by-side or overlaid line chart comparing two users."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates_a,
            y=values_a,
            name=name_a,
            line=dict(color=PRIMARY, width=2),
            fill="tozeroy",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=dates_b,
            y=values_b,
            name=name_b,
            line=dict(color="#6366f1", width=2),
            fill="tozeroy",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_label,
        paper_bgcolor="#0f172a",
        plot_bgcolor=SECONDARY_BG,
        font=dict(color=TEXT),
        margin=dict(t=40, b=40, l=40, r=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(gridcolor=BORDER),
        yaxis=dict(gridcolor=BORDER),
        height=200,
    )
    return fig
