# ErgoVisionAI

## Intelligent Workplace Ergonomics and Wellness Assistant

ErgoVisionAI is a computer vision application that monitors workplace ergonomics in real time using a standard webcam. The system analyzes sitting posture, tracks blink rate and yawning frequency, calculates an overall wellness score, and generates session reports with visual analytics.

The project was developed to demonstrate how AI and computer vision can be applied to improve workplace health and reduce ergonomic risks through continuous monitoring and actionable feedback.

---

## Features

- Real-time posture detection using MediaPipe Pose
- Live posture classification and ergonomic risk assessment
- Blink detection for eye strain monitoring
- Yawn detection for fatigue analysis
- Wellness score calculation based on multiple health indicators
- Voice and visual posture alerts
- SQLite database for session storage
- CSV session logging
- Interactive analytics dashboard
- Automatic PDF health report generation
- Support for both live webcam and recorded video input

---

## Demo

The application provides:

- Live webcam monitoring
- Skeleton visualization
- Posture angle measurement
- Blink and yawn tracking
- Wellness dashboard
- Session analytics
- Exportable PDF reports

Screenshots and demo videos can be found inside the **assets/** directory.

---

# Project Structure

```text
ErgoVisionAI/
│
├── assets/
├── models/
│
├── app.py
├── pose_detection.py
├── posture.py
├── blink_detector.py
├── yawn_detector.py
├── alerts.py
├── database.py
├── dashboard.py
├── report_generator.py
├── wellness_calculator.py
├── utils.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Technology Stack

| Category | Technologies |
|----------|--------------|
| Programming Language | Python |
| Computer Vision | OpenCV |
| Pose Estimation | MediaPipe |
| Numerical Computing | NumPy |
| Data Processing | Pandas |
| Database | SQLite |
| Dashboard | Streamlit |
| Report Generation | Matplotlib, ReportLab |
| Voice Alerts | pyttsx3 |

---

# Installation

Clone the repository

```bash
git clone https://github.com/sreyaslinith/Posture-Classification-and-Ergonomic-Risk-Assessment-using-Computer-Vision.git
```

Move into the project directory

```bash
cd Posture-Classification-and-Ergonomic-Risk-Assessment-using-Computer-Vision
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

### Webcam Mode

```bash
python app.py
```

or

```bash
python app.py --mode webcam
```

### Video Mode

```bash
python app.py --mode video --file sample.mp4
```

---

# Dashboard

Launch the analytics dashboard using Streamlit.

```bash
streamlit run dashboard.py
```

The dashboard provides

- Posture statistics
- Session duration
- Wellness score
- Interactive charts
- Historical analysis

---

# Posture Classification

The application measures the angle formed between the ear, shoulder, and hip landmarks.

| Angle | Classification |
|-------|----------------|
| Greater than 165° | Good |
| 150° – 165° | Moderate |
| Less than 150° | Poor |

If poor posture is detected continuously, the application generates visual and voice reminders.

---

# Reports

After each monitoring session, the system can generate

- Session summary
- Wellness score
- Blink statistics
- Fatigue analysis
- Posture statistics
- Graphical visualizations
- PDF report

---

# Output Files

During execution, the application generates

```text
posture.db
session_data.csv
graphs/
reports/
```

These files are created automatically after a monitoring session.

---

# Future Improvements

Future versions of the project may include

- Multi-person posture monitoring
- Deep learning posture classification
- Cloud database integration
- Mobile application support
- Real-time team analytics
- Personalized ergonomic recommendations

---

# Contributors

This project is actively maintained by

**Sreyas Linith**

Contributions, suggestions, and improvements are welcome through Issues and Pull Requests.

---

# License

This project is intended for educational, research, and portfolio purposes.
