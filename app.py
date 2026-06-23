"""
Intelligent Workplace Ergonomics and Wellness Assistant
Main desktop application with Tkinter GUI.

Run: python app.py
"""

import csv
import os
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk

# Use explicit package imports from the `new` package to avoid editor/LS warnings
from typing import Dict, List, Optional

from blink_detector import BlinkDetector
from pose_detection import PoseDetector
from posture import PostureAnalyzer

from new.report_generator import (
    CSV_PATH,
    build_session_summary,
    generate_graphs,
    generate_pdf_report,
    load_session_data,
)
from new.wellness_calculator import calculate_wellness
from new.yawn_detector import YawnDetector

# ---------------------------------------------------------------------------
# Paths & theme colours
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG_DARK = "#0e1117"
BG_CARD = "#1a1f2e"
BG_CARD2 = "#2d3748"
ACCENT = "#63b3ed"
GREEN = "#48bb78"
RED = "#fc8181"
YELLOW = "#ecc94b"
TEXT = "#f7fafc"
TEXT_DIM = "#a0aec0"

LOG_INTERVAL = 1.0  # seconds between CSV rows


class WellnessApp:
    """Main Tkinter application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Intelligent Workplace Ergonomics & Wellness Assistant")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("1280x780")
        self.root.minsize(1100, 700)

        # Detectors
        self.pose_det: Optional[PoseDetector] = None
        self.posture_analyzer: Optional[PostureAnalyzer] = None
        self.blink_det: Optional[BlinkDetector] = None
        self.yawn_det: Optional[YawnDetector] = None

        # Camera state
        self.cap: Optional[cv2.VideoCapture] = None
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._session_start: Optional[float] = None
        self._last_log_time: float = 0.0
        self._session_records: List[Dict[str, object]] = []
        self._graph_paths: Dict[str, str] = {}
        self._last_summary: Dict[str, object] = {}
        self._last_wellness: Dict[str, object] = {}

        # User name for reports
        self.user_name = tk.StringVar(value="User")

        self._build_ui()
        self._setup_styles()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG_DARK)
        style.configure("TLabel", background=BG_DARK, foreground=TEXT)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("CardTitle.TLabel", background=BG_CARD, foreground=TEXT_DIM,
                        font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background=BG_CARD, foreground=TEXT,
                        font=("Segoe UI", 22, "bold"))
        style.configure("Header.TLabel", background=BG_DARK, foreground=ACCENT,
                        font=("Segoe UI", 16, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.map("Accent.TButton",
                  background=[("active", "#4299e1"), ("!disabled", ACCENT)],
                  foreground=[("!disabled", "white")])

    def _build_ui(self):
        # --- Top header ---
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=16, pady=(12, 4))
        ttk.Label(header, text="Workplace Ergonomics & Wellness Assistant",
                  style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header, text="Name:", background=BG_DARK, foreground=TEXT_DIM).pack(
            side=tk.RIGHT, padx=(0, 4))
        name_entry = tk.Entry(header, textvariable=self.user_name, width=16,
                              bg=BG_CARD2, fg=TEXT, insertbackground=TEXT,
                              relief=tk.FLAT, font=("Segoe UI", 10))
        name_entry.pack(side=tk.RIGHT)

        # --- Main body ---
        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        # Left panel — metric cards
        left = ttk.Frame(body, width=240)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left.pack_propagate(False)

        self.card_posture = self._make_card(left, "Posture Score", "--")
        self.card_blink = self._make_card(left, "Blink Rate", "-- /min")
        self.card_yawn = self._make_card(left, "Yawn Count", "--")
        self.card_wellness = self._make_card(left, "Wellness Score", "--")
        self.card_status = self._make_card(left, "Posture Status", "Idle")
        self.card_blink_health = self._make_card(left, "Blink Health", "--")
        self.card_yawn_health = self._make_card(left, "Yawn Health", "--")

        # Centre — webcam feed
        center = ttk.Frame(body)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(center, bg=BG_CARD, relief=tk.FLAT)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        self.warning_label = tk.Label(
            center, text="", bg=RED, fg="white",
            font=("Segoe UI", 12, "bold"), pady=6,
        )
        self.warning_label.pack(fill=tk.X, pady=(4, 0))

        # Right panel — controls & info
        right = ttk.Frame(body, width=220)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        right.pack_propagate(False)

        ctrl_frame = tk.Frame(right, bg=BG_CARD, padx=16, pady=16)
        ctrl_frame.pack(fill=tk.X, pady=(0, 12))

        self.btn_start = tk.Button(
            ctrl_frame, text="▶  Start Camera", command=self.start_camera,
            bg=GREEN, fg="white", font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, cursor="hand2", pady=10, width=18,
        )
        self.btn_start.pack(pady=(0, 8))

        self.btn_stop = tk.Button(
            ctrl_frame, text="⏹  Stop Camera", command=self.stop_camera,
            bg=RED, fg="white", font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, cursor="hand2", pady=10, width=18, state=tk.DISABLED,
        )
        self.btn_stop.pack(pady=(0, 8))

        self.btn_export = tk.Button(
            ctrl_frame, text="📄  Export Report", command=self.export_report,
            bg=ACCENT, fg="white", font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, cursor="hand2", pady=10, width=18, state=tk.DISABLED,
        )
        self.btn_export.pack()

        info = tk.Label(
            right, text="Press Start to begin monitoring.\n"
                        "Sit facing the webcam with\n"
                        "upper body visible.\n\n"
                        "Press Stop to view session\n"
                        "analytics and health report.",
            bg=BG_DARK, fg=TEXT_DIM, font=("Segoe UI", 9),
            justify=tk.LEFT, wraplength=200,
        )
        info.pack(pady=12, anchor=tk.W)

        self.session_label = tk.Label(
            right, text="Session: Not started",
            bg=BG_DARK, fg=TEXT_DIM, font=("Segoe UI", 9),
        )
        self.session_label.pack(anchor=tk.W)

    def _make_card(self, parent, title: str, value: str) -> tk.Label:
        """Create a dashboard metric card; returns the value label."""
        frame = tk.Frame(parent, bg=BG_CARD, padx=14, pady=12)
        frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(frame, text=title, bg=BG_CARD, fg=TEXT_DIM,
                 font=("Segoe UI", 9)).pack(anchor=tk.W)
        val = tk.Label(frame, text=value, bg=BG_CARD, fg=TEXT,
                       font=("Segoe UI", 20, "bold"))
        val.pack(anchor=tk.W)
        return val

    def _update_card(self, label: tk.Label, value: str, color: str = TEXT):
        label.config(text=value, fg=color)

    # ------------------------------------------------------------------
    # Camera control
    # ------------------------------------------------------------------
    def start_camera(self):
        if self.running:
            return
        try:
            self.pose_det = PoseDetector()
            self.posture_analyzer = PostureAnalyzer()
            self.blink_det = BlinkDetector()
            self.yawn_det = YawnDetector()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load AI models:\n{exc}")
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            return

        self.running = True
        self._session_start = time.time()
        self._last_log_time = 0.0
        self._session_records = []
        self._graph_paths = {}

        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.DISABLED)
        self.session_label.config(text="Session: Active ●")

        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop_camera(self):
        if not self.running:
            return
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()
            self.cap = None

        for det in [self.pose_det, self.blink_det, self.yawn_det]:
            if det:
                try:
                    if hasattr(det, "release"):
                        det.release()
                    elif hasattr(det, "close"):
                        det.close()
                except Exception:
                    pass

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_export.config(state=tk.NORMAL)
        self.session_label.config(text="Session: Ended")

        # Save CSV and generate analytics
        self._save_session_csv()
        df = load_session_data(CSV_PATH)
        duration_min = (time.time() - self._session_start) / 60.0 if self._session_start else 0

        wellness = self._last_wellness or calculate_wellness(0, 0, 0)
        summary = build_session_summary(df, wellness, duration_min)
        self._last_summary = summary

        try:
            self._graph_paths = generate_graphs(df)
        except Exception as exc:
            print(f"[app] Graph error: {exc}")
            self._graph_paths = {}

        self._show_health_report(summary, wellness)

    def _capture_loop(self):
        """Background thread: read frames and schedule UI updates."""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            self.root.after(0, self._process_frame, frame)
            time.sleep(0.03)
        self.root.after(0, self.stop_camera if self.running else lambda: None)

    def _process_frame(self, frame):
        """Process one frame through all detectors and update UI."""
        if not self.running:
            return

        h, w = frame.shape[:2]

        # Run pose detection
        pose_results = self.pose_det.process(frame.copy())
        points = self.pose_det.get_posture_points(pose_results, w, h)
        posture_analysis = self.posture_analyzer.analyze(points) if points else None
        
        # Build posture dict compatible with current code
        if posture_analysis:
            posture = {
                "score": posture_analysis["score"],
                "status": "Good Posture" if posture_analysis["posture"] == "good" else (
                    "Okay Posture" if posture_analysis["posture"] == "okay" else "Bad Posture"
                ),
                "warning": posture_analysis["posture"] == "bad",
                "warning_message": "Sit Upright!",
                "color": posture_analysis["color"],
            }
        else:
            posture = {
                "score": 0,
                "status": "Detecting...",
                "warning": False,
                "warning_message": "",
                "color": (100, 100, 100),
            }

        # Run other detectors
        blink = self.blink_det.process(frame)
        yawn = self.yawn_det.process(frame)

        # Draw skeleton on frame
        frame = self.pose_det.draw_skeleton(frame, pose_results)
        if points and posture_analysis:
            self.pose_det.draw_posture_line(frame, points, posture_analysis["color"])

        duration_min = (time.time() - self._session_start) / 60.0 if self._session_start else 0
        wellness = calculate_wellness(
            posture_score=posture["score"],
            blink_rate=blink["blink_rate"],
            yawns_per_hour=self.yawn_det.get_yawns_per_hour(),
            records_count=len(self._session_records),
            session_minutes=duration_min,
        )
        self._last_wellness = wellness

        # Draw overlays on frame
        self._draw_overlay(frame, posture, blink, yawn, wellness)

        # Update cards
        score_color = GREEN if posture["score"] >= 70 else (YELLOW if posture["score"] >= 50 else RED)
        self._update_card(self.card_posture, f"{posture['score']}", score_color)
        self._update_card(self.card_blink, f"{blink['blink_rate']} /min")
        self._update_card(self.card_yawn, str(yawn["yawn_count"]))
        w_color = GREEN if wellness["wellness_score"] >= 75 else (
            YELLOW if wellness["wellness_score"] >= 60 else RED)
        self._update_card(self.card_wellness, f"{wellness['wellness_score']:.0f}", w_color)
        self._update_card(self.card_status, posture["status"],
                          GREEN if posture["status"] == "Good Posture" else RED)
        self._update_card(self.card_blink_health, blink["health_status"])
        self._update_card(self.card_yawn_health, yawn["health_status"])

        # Warning banner
        if posture["warning"]:
            self.warning_label.config(text=f"⚠  {posture['warning_message']}")
        else:
            self.warning_label.config(text="")

        # Log to session buffer
        now = time.time()
        if now - self._last_log_time >= LOG_INTERVAL:
            record = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Posture Score": posture["score"],
                "Blink Count": blink["blink_count"],
                "Blink Rate": blink["blink_rate"],
                "Yawn Count": yawn["yawn_count"],
                "Wellness Score": wellness["wellness_score"],
            }
            self._session_records.append(record)
            self._last_log_time = now

        # Show frame in GUI
        self._show_frame(frame)

    def _draw_overlay(self, frame, posture, blink, yawn, wellness):
        """Draw HUD text on the video frame."""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (20, 20, 30), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        lines = [
            f"Posture: {posture['status']}  |  Score: {posture['score']}",
            f"Blinks: {blink['blink_count']}  ({blink['blink_rate']}/min)  |  "
            f"Yawns: {yawn['yawn_count']}  |  Wellness: {wellness['wellness_score']:.0f}",
        ]
        for i, line in enumerate(lines):
            cv2.putText(frame, line, (10, 28 + i * 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        if posture["warning"]:
            cv2.putText(frame, "SIT UPRIGHT!", (w // 2 - 100, h - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)

    def _show_frame(self, frame):
        """Convert OpenCV frame to Tkinter image and display."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        # Scale to fit label
        lw = max(self.video_label.winfo_width(), 640)
        lh = max(self.video_label.winfo_height(), 480)
        img.thumbnail((lw, lh), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=img)
        self.video_label.config(image=photo)
        self.video_label.image = photo

    def _save_session_csv(self):
        """Write session records to session_data.csv."""
        if not self._session_records:
            return
        file_exists = os.path.isfile(CSV_PATH)
        try:
            with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["Timestamp", "Posture Score", "Blink Count",
                                "Blink Rate", "Yawn Count", "Wellness Score"],
                )
                writer.writeheader()
                writer.writerows(self._session_records)
        except OSError as exc:
            print(f"[app] CSV save error: {exc}")

    # ------------------------------------------------------------------
    # Health report window
    # ------------------------------------------------------------------
    def _show_health_report(self, summary: dict, wellness: dict):
        """Show session health summary in a popup window."""
        win = tk.Toplevel(self.root)
        win.title("Session Health Report")
        win.configure(bg=BG_DARK)
        win.geometry("520x620")
        win.grab_set()

        tk.Label(win, text="SESSION HEALTH REPORT",
                 bg=BG_DARK, fg=ACCENT, font=("Segoe UI", 16, "bold")).pack(pady=(20, 10))
        tk.Frame(win, bg=ACCENT, height=2).pack(fill=tk.X, padx=40)

        lines = [
            ("Session Duration", f"{summary['duration_min']:.1f} min"),
            ("Average Posture Score", f"{summary['avg_posture']:.1f}%"),
            ("Total Blinks", str(summary["total_blinks"])),
            ("Blink Rate", f"{summary['avg_blink_rate']:.1f}/min"),
            ("Total Yawns", str(summary["total_yawns"])),
            ("Wellness Score", f"{summary['wellness_score']:.1f}/100"),
            ("Health Status", summary["health_status"]),
        ]

        body = tk.Frame(win, bg=BG_DARK, padx=40, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        for label, value in lines:
            row = tk.Frame(body, bg=BG_DARK)
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=label, bg=BG_DARK, fg=TEXT_DIM,
                     font=("Segoe UI", 10), width=24, anchor=tk.W).pack(side=tk.LEFT)
            color = GREEN if label == "Health Status" and value in ("Excellent", "Good") else TEXT
            if label == "Health Status" and value in ("Average", "Poor"):
                color = RED if value == "Poor" else YELLOW
            tk.Label(row, text=value, bg=BG_DARK, fg=color,
                     font=("Segoe UI", 11, "bold"), anchor=tk.W).pack(side=tk.LEFT)

        tk.Label(body, text="\nRecommendations:", bg=BG_DARK, fg=ACCENT,
                 font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(12, 4))
        for rec in wellness.get("recommendations", []):
            tk.Label(body, text=f"  • {rec}", bg=BG_DARK, fg=TEXT_DIM,
                     font=("Segoe UI", 9), wraplength=420, justify=tk.LEFT).pack(anchor=tk.W)

        tk.Label(body, text="\nGraphs saved to: graphs/",
                 bg=BG_DARK, fg=TEXT_DIM, font=("Segoe UI", 8)).pack(anchor=tk.W)

        tk.Button(win, text="Close", command=win.destroy,
                  bg=BG_CARD2, fg=TEXT, relief=tk.FLAT, padx=20, pady=6,
                  cursor="hand2").pack(pady=16)

    def export_report(self):
        """Generate and save PDF health report."""
        df = load_session_data(CSV_PATH)
        if df.empty and not self._last_summary:
            messagebox.showwarning("No Data", "No session data to export.")
            return

        duration_min = self._last_summary.get("duration_min", 0)
        wellness = self._last_wellness or calculate_wellness(0, 0, 0)
        summary = self._last_summary or build_session_summary(df, wellness, duration_min)

        if not self._graph_paths:
            try:
                self._graph_paths = generate_graphs(df)
            except Exception as exc:
                messagebox.showerror("Error", f"Could not generate graphs:\n{exc}")
                return

        try:
            path = generate_pdf_report(
                summary, self._graph_paths, user_name=self.user_name.get()
            )
            messagebox.showinfo("Report Exported", f"PDF saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"PDF export failed:\n{exc}")

    def on_close(self):
        if self.running:
            self.stop_camera()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = WellnessApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
