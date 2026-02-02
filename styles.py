"""Global CSS injection for 75 Hard Challenge tracker."""

import streamlit as st

# Theme colors
PRIMARY = "#10b981"
SECONDARY_BG = "#1e293b"
BG = "#0f172a"
TEXT = "#f1f5f9"
ACCENT_2 = "#6366f1"
HIGHLIGHT = "#fbbf24"
BORDER = "#334155"


def inject_custom_css():
    """Inject global custom CSS for rounded containers, metric cards, sidebar polish, and cleaner look."""
    st.markdown(
        f"""
        <style>
        /* Main app background */
        .stApp {{
            background: {BG};
        }}
        /* Rounded containers with subtle borders */
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }}
        div[data-testid="stVerticalBlock"] > div {{
            border-radius: 8px;
        }}
        /* Metric cards - gradient border feel */
        [data-testid="stMetric"] {{
            background: {SECONDARY_BG};
            padding: 1rem 1.25rem;
            border-radius: 8px;
            border: 1px solid {BORDER};
            transition: box-shadow 0.2s ease;
        }}
        [data-testid="stMetric"]:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        /* Sidebar polish */
        [data-testid="stSidebar"] {{
            background: {SECONDARY_BG};
            border-right: 1px solid {BORDER};
        }}
        [data-testid="stSidebar"] .stMarkdown {{
            color: {TEXT};
        }}
        /* Buttons - primary color */
        .stButton > button {{
            background: {PRIMARY};
            color: white;
            border: none;
            border-radius: 6px;
            transition: opacity 0.2s ease, transform 0.1s ease;
        }}
        .stButton > button:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
        /* Hide Streamlit footer and hamburger for cleaner look */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header {{ visibility: hidden; }}
        /* Dataframe styling - alternating rows */
        .stDataFrame {{
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid {BORDER};
        }}
        .stDataFrame tbody tr:nth-child(even) {{
            background: rgba(30, 41, 59, 0.5);
        }}
        /* Radio / segmented control styling */
        .stRadio > div {{
            background: {SECONDARY_BG};
            padding: 0.5rem;
            border-radius: 8px;
            border: 1px solid {BORDER};
        }}
        /* Progress bar in theme */
        .stProgress > div > div > div {{
            background: {PRIMARY};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
