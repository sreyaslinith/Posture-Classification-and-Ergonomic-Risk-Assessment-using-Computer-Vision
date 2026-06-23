# ErgoVisionAI

### AI-Powered Posture Classification & Ergonomic Risk Assessment using Computer Vision

> An intelligent workplace ergonomics assistant that monitors posture in real time, detects unhealthy sitting habits, provides instant feedback, and generates wellness analytics.

---

## Project Overview

ErgoVisionAI is a computer vision application that helps users maintain healthy sitting posture during long working hours.

Using AI-powered pose estimation, the system continuously analyzes body posture through a webcam or video input, classifies ergonomic risk, records posture history, provides real-time alerts, and generates wellness reports.

This project demonstrates practical applications of Computer Vision, Human Pose Estimation, Human-Computer Interaction, and AI-assisted workplace wellness.

---

## Key Features

### Real-Time Posture Detection

* Live webcam posture monitoring
* Video file analysis
* MediaPipe pose estimation
* Skeleton visualization

### Ergonomic Risk Assessment

* Neck and back angle calculation
* Good / Okay / Bad posture classification
* Posture score (0–100)
* Sitting duration tracking
* Bad posture counter

### Smart Alerts

* Visual posture warning
* Voice reminders
* Continuous bad posture monitoring

### Data Analytics

* SQLite database logging
* CSV session history
* Session analytics
* Interactive dashboard

### Professional UI

* Modern dark theme
* Real-time HUD
* FPS monitoring
* Clean OpenCV interface

---

## Tech Stack

| Category         | Technologies      |
| ---------------- | ----------------- |
| Programming      | Python            |
| Computer Vision  | OpenCV, MediaPipe |
| Machine Learning | Pose Estimation   |
| Data Processing  | NumPy, Pandas     |
| Database         | SQLite            |
| Dashboard        | Streamlit         |
| Visualization    | Plotly            |
| Alerts           | pyttsx3           |
| Version Control  | Git & GitHub      |

---

## Project Structure

```text
ErgoVisionAI/
│
├── app.py
├── pose_detection.py
├── posture.py
├── alerts.py
├── database.py
├── dashboard.py
├── utils.py
├── requirements.txt
├── README.md
│
├── assets/
│   ├── screenshots/
│   └── demo.gif
│
├── posture.db
└── posture_history.csv
```

---

## Installation

```bash
git clone https://github.com/sreyaslinith/Posture-Classification-and-Ergonomic-Risk-Assessment-using-Computer-Vision.git

cd Posture-Classification-and-Ergonomic-Risk-Assessment-using-Computer-Vision

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running the Project

### Webcam Mode

```bash
python app.py
```

### Video Mode

```bash
python app.py --mode video --file sample.mp4
```

### Dashboard

```bash
streamlit run dashboard.py
```

---

## System Workflow

```text
Webcam / Video
        │
        ▼
 MediaPipe Pose Detection
        │
        ▼
 Landmark Extraction
        │
        ▼
 Angle Calculation
        │
        ▼
 Posture Classification
        │
        ├── Good
        ├── Okay
        └── Bad
        │
        ▼
 Alert System
        │
        ▼
 Database Logging
        │
        ▼
 Analytics Dashboard
```

---

## Sample Output

* Real-time skeleton overlay
* Posture angle measurement
* Ergonomic posture score
* Sitting duration
* Bad posture alerts
* Session history
* Analytics dashboard

*(Add screenshots or GIFs inside the `assets/` folder.)*

---

## Future Improvements

* Blink detection
* Yawn detection
* Wellness score
* AI health recommendations
* PDF report generation
* Multi-user profiles
* Cloud database
* Mobile application
* Deep learning posture classifier

---

## Skills Demonstrated

* Computer Vision
* Human Pose Estimation
* Machine Learning
* Python Development
* OpenCV
* Data Analytics
* Software Engineering
* Human-Centered AI

---

## Contributors

* **Sreyas Linith** – Machine Learning, Computer Vision, System Development

Contributions from collaborators are welcome.

---

## License

This project is intended for educational, research, and portfolio purposes.
