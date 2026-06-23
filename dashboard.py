"""
ErgoVisionAI — Streamlit analytics dashboard.

Run with:
    streamlit run dashboard.py
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure local modules are importable when launched via streamlit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import PostureDatabase
from utils import format_duration, posture_score, DB_PATH, CSV_PATH

# ---------------------------------------------------------------------------
# Page config — dark professional theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ErgoVisionAI Dashboard",
    page_icon="🧍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark cards
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 8px;
    }
    .metric-card h3 {
        color: #a0aec0;
        font-size: 0.85rem;
        margin: 0 0 8px 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card p {
        color: #f7fafc;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .good  { color: #48bb78 !important; }
    .okay  { color: #ecc94b !important; }
    .bad   { color: #fc8181 !important; }
  </style>
    """,
    unsafe_allow_html=True,
)


def metric_card(label: str, value: str, css_class: str = "") -> None:
    """Render a styled metric card."""
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>{label}</h3>
            <p class="{css_class}">{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=5)
def load_data() -> pd.DataFrame:
    """Load posture records from SQLite (cached, refreshes every 5 s)."""
    db = PostureDatabase()
    return db.get_all_records()


def main() -> None:
    """Render the full dashboard."""
    # --- Sidebar ---
    st.sidebar.title("ErgoVisionAI")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Posture Analytics Dashboard**")
    st.sidebar.markdown(
        "Run `python app.py` to start collecting posture data, "
        "then refresh this page to see live updates."
    )
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5 s)", value=True)
    if st.sidebar.button("Refresh Now"):
        st.cache_data.clear()

    if auto_refresh:
        st.markdown(
            '<meta http-equiv="refresh" content="5">',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Database: `{DB_PATH}`")
    st.sidebar.caption(f"CSV: `{CSV_PATH}`")

    # --- Header ---
    st.title("ErgoVisionAI Dashboard")
    st.markdown(
        "Real-time posture classification and ergonomic risk assessment"
    )
    st.markdown("---")

    db = PostureDatabase()
    stats = db.get_summary_stats()
    df = load_data()
    latest = db.get_latest_record()

    if df.empty:
        st.warning(
            "No posture data found. "
            "Start a session with `python app.py` to begin recording."
        )
        return

    # --- Live metrics row ---
    live_posture = latest["posture"] if latest else "N/A"
    live_angle = f"{latest['angle']:.1f}°" if latest else "N/A"
    live_score = posture_score(latest["posture"]) if latest else 0
    posture_css = live_posture.lower() if latest else ""

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("Live Posture Score", f"{live_score}/100")
    with col2:
        metric_card("Current Posture", live_posture, posture_css)
    with col3:
        metric_card("Current Angle", live_angle)
    with col4:
        metric_card(
            "Good Posture %",
            f"{stats['good_percentage']}%",
            "good",
        )
    with col5:
        metric_card(
            "Bad Posture Count",
            str(stats["bad_count"]),
            "bad",
        )

    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        metric_card(
            "Average Angle",
            f"{stats['average_angle']}°",
        )
    with col_b:
        metric_card(
            "Total Sitting Time",
            format_duration(stats["total_sitting_time_sec"]),
        )

    st.markdown("---")

    # --- Charts ---
    chart_col1, chart_col2 = st.columns(2)

    # Pie chart — posture distribution
    with chart_col1:
        st.subheader("Posture Distribution")
        pie_df = pd.DataFrame(
            {
                "Posture": ["Good", "Okay", "Bad"],
                "Count": [
                    stats["good_count"],
                    stats["okay_count"],
                    stats["bad_count"],
                ],
            }
        )
        pie_df = pie_df[pie_df["Count"] > 0]
        if not pie_df.empty:
            fig_pie = px.pie(
                pie_df,
                names="Posture",
                values="Count",
                color="Posture",
                color_discrete_map={
                    "Good": "#48bb78",
                    "Okay": "#ecc94b",
                    "Bad": "#fc8181",
                },
                hole=0.4,
            )
            fig_pie.update_layout(
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                font_color="#f7fafc",
                showlegend=True,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data for pie chart yet.")

    # Bar chart — bad posture events
    with chart_col2:
        st.subheader("Bad Posture Events")
        events = stats["bad_posture_events"]
        fig_bar = go.Figure(
            go.Bar(
                x=["Bad Posture Events"],
                y=[events],
                marker_color="#fc8181",
                text=[str(events)],
                textposition="auto",
            )
        )
        fig_bar.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1a1f2e",
            font_color="#f7fafc",
            yaxis_title="Count",
            height=400,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Line chart — angle vs time (full width)
    st.subheader("Angle vs Time")
    if not df.empty:
        df_plot = df.copy()
        df_plot["time"] = pd.to_datetime(df_plot["time"])
        fig_line = px.line(
            df_plot,
            x="time",
            y="angle",
            title="Posture Angle Over Time",
            labels={"time": "Time", "angle": "Angle (degrees)"},
        )
        # Reference threshold lines
        fig_line.add_hline(
            y=165, line_dash="dash", line_color="#48bb78",
            annotation_text="Good (165°)",
        )
        fig_line.add_hline(
            y=150, line_dash="dash", line_color="#ecc94b",
            annotation_text="Okay (150°)",
        )
        fig_line.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1a1f2e",
            font_color="#f7fafc",
            height=420,
        )
        fig_line.update_traces(line_color="#63b3ed")
        st.plotly_chart(fig_line, use_container_width=True)

    # --- Raw data table ---
    st.markdown("---")
    with st.expander("View Raw Posture History"):
        st.dataframe(df, use_container_width=True)

        if os.path.isfile(CSV_PATH):
            with open(CSV_PATH, "rb") as f:
                st.download_button(
                    label="Download CSV",
                    data=f,
                    file_name="posture_history.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
