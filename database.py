"""
SQLite database layer for posture session records.
Stores timestamp, angle, and posture label automatically.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional

import pandas as pd

from utils import DB_PATH, current_timestamp, export_to_csv


class PostureDatabase:
    """Manages posture.db read/write operations."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connect(self):
        """Context manager for safe SQLite connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create the posture_records table if it does not exist."""
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS posture_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        time TEXT NOT NULL,
                        angle REAL NOT NULL,
                        posture TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as exc:
            print(f"[database] Init error: {exc}")

    def insert_record(
        self,
        angle: float,
        posture: str,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Insert a posture reading and mirror it to CSV.

        Args:
            angle: Measured posture angle in degrees.
            posture: Posture label (Good / Okay / Bad).
            timestamp: Optional ISO timestamp; defaults to now.
        """
        ts = timestamp or current_timestamp()
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO posture_records (time, angle, posture) VALUES (?, ?, ?)",
                    (ts, round(angle, 2), posture),
                )
            export_to_csv(ts, angle, posture)
        except sqlite3.Error as exc:
            print(f"[database] Insert error: {exc}")

    def get_all_records(self) -> pd.DataFrame:
        """Return all posture records as a pandas DataFrame."""
        try:
            with self._connect() as conn:
                df = pd.read_sql_query(
                    "SELECT time, angle, posture FROM posture_records ORDER BY time",
                    conn,
                )
            return df
        except Exception as exc:
            print(f"[database] Query error: {exc}")
            return pd.DataFrame(columns=["time", "angle", "posture"])

    def get_summary_stats(self) -> dict:
        """Compute aggregate statistics for the dashboard."""
        df = self.get_all_records()
        if df.empty:
            return {
                "total_records": 0,
                "good_count": 0,
                "okay_count": 0,
                "bad_count": 0,
                "good_percentage": 0.0,
                "average_angle": 0.0,
                "total_sitting_time_sec": 0,
                "bad_posture_events": 0,
            }

        total = len(df)
        good_count = int((df["posture"] == "Good").sum())
        okay_count = int((df["posture"] == "Okay").sum())
        bad_count = int((df["posture"] == "Bad").sum())

        # Estimate sitting time: one record per processed frame (~1 sec intervals in app)
        sitting_sec = total

        # Count bad-posture streak starts (transition into Bad)
        bad_events = 0
        prev = None
        for p in df["posture"]:
            if p == "Bad" and prev != "Bad":
                bad_events += 1
            prev = p

        return {
            "total_records": total,
            "good_count": good_count,
            "okay_count": okay_count,
            "bad_count": bad_count,
            "good_percentage": round((good_count / total) * 100, 1) if total else 0.0,
            "average_angle": round(float(df["angle"].mean()), 1),
            "total_sitting_time_sec": sitting_sec,
            "bad_posture_events": bad_events,
        }

    def get_latest_record(self) -> Optional[dict]:
        """Return the most recent posture record."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT time, angle, posture FROM posture_records "
                    "ORDER BY id DESC LIMIT 1"
                ).fetchone()
            if row:
                return {"time": row[0], "angle": row[1], "posture": row[2]}
        except sqlite3.Error as exc:
            print(f"[database] Latest record error: {exc}")
        return None
