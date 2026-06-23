<<<<<<< HEAD
# ErgoVisionAI

**Posture Classification and Ergonomic Risk Assessment using Computer Vision**

ErgoVisionAI uses MediaPipe Pose estimation to monitor sitting posture in real time, classify ergonomic risk, store session history, and visualize analytics through a Streamlit dashboard.

---

## Features

- **Live Webcam** — real-time pose detection with skeleton overlay and FPS display
- **Video Upload** — process mp4 / avi / mov files frame by frame
- **Posture Angle** — ear → shoulder → hip angle with Good / Okay / Bad classification
- **Voice Alerts** — pyttsx3 warning after 10 seconds of bad posture (repeats every 10 s)
- **SQLite Database** — automatic logging to `posture.db`
- **CSV Export** — session history saved to `posture_history.csv`
- **Streamlit Dashboard** — live metrics and Plotly charts (pie, line, bar)
- **Dark Theme UI** — professional OpenCV overlay and dashboard styling

---

## Folder Structure

```
ErgoVisionAI/
├── app.py              # Main application (webcam & video modes)
├── pose_detection.py   # MediaPipe pose estimation & skeleton drawing
├── posture.py          # Angle calculation & posture classification
├── alerts.py           # Bad posture timer & voice alerts
├── database.py         # SQLite storage layer
├── dashboard.py        # Streamlit analytics dashboard
├── utils.py            # Shared helpers, constants, CSV export
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── posture.db          # Auto-created SQLite database
├── posture_history.csv # Auto-created CSV export
└── assets/             # Static assets (screenshots, etc.)
```

---

## Installation

### 1. Prerequisites

- Python 3.9 or higher
- Webcam (for live mode)
- Windows / macOS / Linux

### 2. Clone or download the project

```bash
cd ErgoVisionAI
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running Webcam Mode

Start the application with your default webcam:

```bash
python app.py
```

Or explicitly:

```bash
python app.py --mode webcam
```

Use a different camera index if needed:

```bash
python app.py --camera 1
```

**Controls:**
- Press `q` to quit and save session data

---

## Running Video Mode

Process a pre-recorded video file:

```bash
python app.py --mode video --file path/to/your_video.mp4
```

Supported formats: **mp4**, **avi**, **mov**

If you omit `--file`, the app will prompt you for a path interactively.

---

## Running Dashboard

Open the Streamlit analytics dashboard in a **separate terminal** (while or after a session):

```bash
python -m streamlit run dashboard.py
```

The dashboard will open in your browser (default: `http://localhost:8501`).

**Dashboard shows:**
| Metric | Description |
|---|---|
| Live Posture Score | Current score out of 100 |
| Current Posture | Good / Okay / Bad |
| Current Angle | Latest measured angle |
| Good Posture % | Percentage of Good readings |
| Bad Posture Count | Total Bad posture frames |
| Average Angle | Mean angle across session |
| Total Sitting Time | Estimated session duration |

**Charts:**
- **Pie Chart** — Good / Okay / Bad distribution
- **Line Chart** — Angle vs Time with threshold lines
- **Bar Chart** — Bad posture event count

Enable **Auto-refresh** in the sidebar for live updates during an active session.

---

## Posture Classification Rules

The system measures the angle formed at the **shoulder** between the **ear** and **hip**:

| Angle | Classification |
|---|---|
| > 165° | **Good Posture** |
| 150° – 165° | **Okay Posture** |
| < 150° | **Bad Posture** |

When bad posture persists for more than **10 seconds**, a visual warning and voice alert are triggered. Alerts repeat every **10 seconds** while bad posture continues.

---

## Screenshots

> Place your screenshots in the `assets/` folder.

| Screenshot | Description |
|---|---|
| `assets/webcam_mode.png` | Live webcam with skeleton overlay |
| `assets/posture_alert.png` | Bad posture warning banner |
| `assets/dashboard.png` | Streamlit analytics dashboard |

---

## Output Files

| File | Description |
|---|---|
| `posture.db` | SQLite database with all posture records |
| `posture_history.csv` | CSV export (`timestamp`, `angle`, `posture`) |

Both files are created automatically on first run and updated during each session.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Webcam not opening | Try `--camera 1` or check camera permissions |
| No pose detected | Ensure upper body is visible; improve lighting |
| Voice alert silent | Install pyttsx3; check system audio / TTS voices |
| Dashboard shows no data | Run `python app.py` first to collect records |
| MediaPipe install fails | Use Python 3.9–3.11; upgrade pip: `pip install --upgrade pip` |

---

## Tech Stack

- **OpenCV** — video capture and UI rendering
- **MediaPipe** — pose landmark detection
- **NumPy** — angle mathematics
- **SQLite** — local data storage
- **Pandas** — data analysis
- **Plotly** — interactive charts
- **Streamlit** — web dashboard
- **pyttsx3** — text-to-speech alerts

---

## License

Educational / academic use — IIIT Project.
=======
# Posture-Classification-and-Ergonomic-Risk-Assessment-using-Computer-Vision
>>>>>>> a62bade2a129374b809fea6946f98505de91d17a
