"""
Generate session analytics graphs and PDF health reports.
"""

import os
from datetime import datetime
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHS_DIR = os.path.join(BASE_DIR, "graphs")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CSV_PATH = os.path.join(BASE_DIR, "session_data.csv")

# Dark theme colours for matplotlib
DARK_BG = "#1a1f2e"
ACCENT = "#63b3ed"
GREEN = "#48bb78"
RED = "#fc8181"
YELLOW = "#ecc94b"


def _ensure_dirs():
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _style_ax(ax):
    """Apply dark theme to a matplotlib axis."""
    ax.set_facecolor(DARK_BG)
    ax.figure.patch.set_facecolor(DARK_BG)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_color("#444")


def load_session_data(csv_path: str = CSV_PATH) -> pd.DataFrame:
    """Load session CSV or return empty DataFrame."""
    if not os.path.isfile(csv_path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_path)
        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        return df
    except Exception:
        return pd.DataFrame()


def generate_graphs(df: pd.DataFrame, session_id: str = "") -> dict:
    """
    Generate all session graphs and save to graphs/ folder.

    Returns dict of file paths.
    """
    _ensure_dirs()
    if df.empty:
        return {}

    ts = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = {}

    # Elapsed minutes from start for x-axis
    if "Timestamp" in df.columns:
        t0 = df["Timestamp"].iloc[0]
        df = df.copy()
        df["Minutes"] = (df["Timestamp"] - t0).dt.total_seconds() / 60.0
        x_col = "Minutes"
        x_label = "Time (minutes)"
    else:
        x_col = df.index
        x_label = "Sample"

    # 1. Posture score vs time
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df[x_col], df["Posture Score"], color=GREEN, linewidth=2)
    ax.set_title("Posture Score vs Time")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Posture Score")
    ax.set_ylim(0, 105)
    _style_ax(ax)
    p1 = os.path.join(GRAPHS_DIR, f"posture_{ts}.png")
    fig.tight_layout()
    fig.savefig(p1, dpi=120, facecolor=DARK_BG)
    plt.close(fig)
    paths["posture"] = p1

    # 2. Blink rate vs time
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df[x_col], df["Blink Rate"], color=ACCENT, linewidth=2)
    ax.axhline(y=10, color=YELLOW, linestyle="--", alpha=0.7, label="Min healthy")
    ax.axhline(y=20, color=GREEN, linestyle="--", alpha=0.7, label="Max healthy")
    ax.set_title("Blink Rate vs Time")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Blinks / min")
    ax.legend(facecolor=DARK_BG, labelcolor="white")
    _style_ax(ax)
    p2 = os.path.join(GRAPHS_DIR, f"blink_{ts}.png")
    fig.tight_layout()
    fig.savefig(p2, dpi=120, facecolor=DARK_BG)
    plt.close(fig)
    paths["blink"] = p2

    # 3. Wellness score vs time
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df[x_col], df["Wellness Score"], color=YELLOW, linewidth=2)
    ax.set_title("Wellness Score vs Time")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Wellness Score")
    ax.set_ylim(0, 105)
    _style_ax(ax)
    p3 = os.path.join(GRAPHS_DIR, f"wellness_{ts}.png")
    fig.tight_layout()
    fig.savefig(p3, dpi=120, facecolor=DARK_BG)
    plt.close(fig)
    paths["wellness"] = p3

    # 4. Bar chart — total blinks & yawns
    total_blinks = int(df["Blink Count"].iloc[-1]) if "Blink Count" in df.columns else 0
    total_yawns = int(df["Yawn Count"].iloc[-1]) if "Yawn Count" in df.columns else 0
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(["Total Blinks", "Total Yawns"], [total_blinks, total_yawns],
                  color=[ACCENT, RED], width=0.5)
    ax.set_title("Session Totals")
    ax.set_ylabel("Count")
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(int(bar.get_height())), ha="center", color="white")
    _style_ax(ax)
    p4 = os.path.join(GRAPHS_DIR, f"totals_{ts}.png")
    fig.tight_layout()
    fig.savefig(p4, dpi=120, facecolor=DARK_BG)
    plt.close(fig)
    paths["totals"] = p4

    return paths


def generate_pdf_report(
    summary: dict,
    graph_paths: dict,
    user_name: str = "User",
    output_path: Optional[str] = None,
) -> str:
    """
    Generate health_report PDF with graphs and recommendations.

    Returns path to saved PDF.
    """
    _ensure_dirs()
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(REPORTS_DIR, f"health_report_{ts}.pdf")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        fontSize=20, textColor=colors.HexColor("#2b6cb0"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=11, leading=16, spaceAfter=6,
    )
    rec_style = ParagraphStyle(
        "Rec", parent=styles["Normal"],
        fontSize=10, leading=14, leftIndent=20,
        bulletIndent=10, spaceAfter=4,
    )

    story = []
    story.append(Paragraph(
        "Intelligent Workplace Ergonomics & Wellness Report", title_style
    ))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"<b>User:</b> {user_name}", body_style))
    story.append(Paragraph(
        f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style
    ))
    story.append(Spacer(1, 0.3 * inch))

    # Summary table
    data = [
        ["Metric", "Value"],
        ["Session Duration", f"{summary.get('duration_min', 0):.1f} min"],
        ["Average Posture Score", f"{summary.get('avg_posture', 0):.1f}%"],
        ["Total Blinks", str(summary.get("total_blinks", 0))],
        ["Blink Rate", f"{summary.get('avg_blink_rate', 0):.1f}/min"],
        ["Total Yawns", str(summary.get("total_yawns", 0))],
        ["Wellness Score", f"{summary.get('wellness_score', 0):.1f}/100"],
        ["Health Status", summary.get("health_status", "N/A")],
    ]
    table = Table(data, colWidths=[3 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#edf2f7")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.4 * inch))

    # Embed graphs
    for key, label in [
        ("posture", "Posture Score Over Time"),
        ("blink", "Blink Rate Over Time"),
        ("wellness", "Wellness Score Over Time"),
        ("totals", "Session Totals"),
    ]:
        path = graph_paths.get(key)
        if path and os.path.isfile(path):
            story.append(Paragraph(f"<b>{label}</b>", body_style))
            story.append(Spacer(1, 0.1 * inch))
            img = Image(path, width=6 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 0.3 * inch))

    # Recommendations
    story.append(Paragraph("<b>Recommendations</b>", body_style))
    story.append(Spacer(1, 0.1 * inch))
    for rec in summary.get("recommendations", []):
        story.append(Paragraph(f"• {rec}", rec_style))

    doc.build(story)
    return output_path


def build_session_summary(df: pd.DataFrame, wellness: dict, duration_min: float) -> dict:
    """Build summary dict from session DataFrame."""
    if df.empty:
        return {
            "duration_min": duration_min,
            "avg_posture": 0,
            "total_blinks": 0,
            "avg_blink_rate": 0,
            "total_yawns": 0,
            "wellness_score": wellness.get("wellness_score", 0),
            "health_status": wellness.get("label", "N/A"),
            "recommendations": wellness.get("recommendations", []),
        }
    return {
        "duration_min": duration_min,
        "avg_posture": round(df["Posture Score"].mean(), 1),
        "total_blinks": int(df["Blink Count"].iloc[-1]),
        "avg_blink_rate": round(df["Blink Rate"].mean(), 1),
        "total_yawns": int(df["Yawn Count"].iloc[-1]),
        "wellness_score": wellness.get("wellness_score", 0),
        "health_status": wellness.get("label", "N/A"),
        "recommendations": wellness.get("recommendations", []),
    }
