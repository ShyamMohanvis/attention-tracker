# 👁 Attention Tracker

> **Pause video when you look away. Resume when you look back.**

[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078d4.svg)](https://www.microsoft.com/windows)
[![Tests](https://img.shields.io/badge/tests-26%20passed-success.svg)](tests/)
[![CI & Build](https://github.com/ShyamMohanvis/attention-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/ShyamMohanvis/attention-tracker/actions/workflows/ci.yml)
[![Pages Deployment](https://github.com/ShyamMohanvis/attention-tracker/actions/workflows/pages.yml/badge.svg)](https://shyammohanvis.github.io/attention-tracker/)

Attention Tracker uses your webcam to watch your eyes and automatically controls media playback based on which monitor you're looking at. Built with MediaPipe, OpenCV, and PySide6.

---

## 📥 Download for Windows (x64)

[![Download for Windows](https://img.shields.io/badge/Download-AttentionTracker--Windows.zip-0078d4?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/ShyamMohanvis/attention-tracker/releases/latest/download/AttentionTracker-Windows.zip)
[![Latest Release](https://img.shields.io/github/v/release/ShyamMohanvis/attention-tracker?style=for-the-badge&color=success)](https://github.com/ShyamMohanvis/attention-tracker/releases/latest)

- **Latest Release**: `v1.0.0`
- **Supported Operating Systems**: Windows 10 (Build 1903+) or Windows 11 (64-bit)
- **Direct Download**: [**AttentionTracker-Windows.zip**](https://github.com/ShyamMohanvis/attention-tracker/releases/latest/download/AttentionTracker-Windows.zip) *(Public download — no GitHub account required)*
- **Browse All Releases & Notes**: [GitHub Releases History](https://github.com/ShyamMohanvis/attention-tracker/releases)

### 🚀 First-Run & Installation Instructions:
1. **Extract All Files**: Download `AttentionTracker-Windows.zip`, right-click it, and choose **Extract All...** to a folder on your drive (e.g. `C:\Users\<You>\AttentionTracker`).
   > [!IMPORTANT]
   > Do **not** run `AttentionTracker.exe` directly from inside the ZIP file! It must be extracted completely so its `_internal` DLL dependencies can be accessed.
2. **Launch Application**: Open the extracted folder and double-click **`AttentionTracker.exe`**.
3. **Windows SmartScreen Note**:
   Attention Tracker is a free, open-source project and is not signed with an enterprise commercial certificate. If Windows SmartScreen displays *"Windows protected your PC"*:
   - Click **More info**.
   - Click **Run anyway**.
4. **Grant Webcam Access**: Ensure Windows Camera privacy settings permit desktop applications to access your webcam.
5. **Calibrate Gaze**: Run the 3-second calibration wizard for both displays, and click Start Tracking!

### 🔧 Troubleshooting:
- **Camera Device Busy**: Make sure video calling software (Zoom, Teams, Google Meet, OBS) is not actively locking your webcam.
- **Media Playback Not Responding**: Ensure your browser or desktop media player (Chrome, Spotify, VLC) allows background media transport control.

---

## Live Showcase & Architecture

- **Project Web Portal / Simulator**: Hosted on GitHub Pages: [https://shyammohanvis.github.io/attention-tracker/](https://shyammohanvis.github.io/attention-tracker/)
- **Interactive Gaze Demo**: Visual demonstration of iris vector estimation, sliding smoothing window, and playback state machine transitions.

---

## How It Works

```
Webcam → MediaPipe FaceMesh (468 landmarks) → Iris Localization (indices 468-477)
       → Head Pose (solvePnP) → Gaze Direction (gaze_x ∈ [-1, 1])
       → 20-frame Sliding Window Smoother
       → Nearest-Centroid Monitor Classifier
       → State Machine (PLAYING ↔ PAUSED, with dwell delays)
       → Windows Media Session API (or media key fallback)
```

---

## Features

- 🎯 **Calibration Wizard** — point at each monitor for 3 seconds; the app learns your setup
- 🖥️ **Selectable Video Monitor** — radio buttons let you pick which monitor hosts the media
- 📹 **Auto-detect Camera** — lists all webcams by name; saves your choice
- 🔊 **Smart Media Control** — uses the Windows Media Session API (works regardless of window focus)
- ⏱️ **Configurable Delays** — tune pause/resume delays and confidence thresholds live
- 🪄 **System Tray** — runs silently in the background; double-click to show the panel
- 🏗️ **Extensible Controllers** — add new media players by implementing `MediaController`

---

## Technology Stack

- **GUI Framework**: PySide6 (Qt 6 for Python)
- **Computer Vision**: OpenCV (`opencv-python`), MediaPipe FaceMesh & Iris Landmarks
- **Math / Numerics**: NumPy, solvePnP perspective-n-point projection
- **Windows Integration**: `pywin32` (monitor enumeration, window focus), `winsdk` (System Media Transport Controls / SMTC)
- **Packaging**: PyInstaller
- **Testing**: pytest, pytest-cov

---

## Prerequisites

- **OS**: Windows 10 Build 1903+ or Windows 11 (for Windows Media Session API)
- **Python**: 3.12+ (tested through 3.14)
- **Hardware**: Any standard USB or integrated webcam
- **RAM**: ~200 MB during active tracking

---

## Quick Start & Local Setup

### 1. Clone & create virtual environment

```powershell
git clone https://github.com/ShyamMohanvis/attention-tracker.git
cd attention-tracker
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run application

```powershell
python src/app.py
```

### 4. Calibrate

1. Click **🎯 Calibrate** in the UI.
2. Look at your **video monitor** for 3 seconds.
3. Look at your **other monitor** for 3 seconds.
4. Done — the app records your centroid thresholds.

### 5. Start Tracking

Click **▶ Start** — tracking begins at 30 FPS in the background.

---

## Running Tests

```powershell
pytest tests/ -v
```

All 26 test cases covering classifier centroid calculations, sliding window smoother, and state machine transitions will execute.

---

## Building Standalone Windows Executable

```powershell
# PowerShell (recommended)
.\build.ps1

# Or with cmd.exe
build.bat

# Clean rebuild
.\build.ps1 -Clean
```

The compiled standalone executable will be generated at:
`dist\AttentionTracker\AttentionTracker.exe`

---

## Configuration (`src/settings.json`)

Attention Tracker persists configuration locally in `src/settings.json`. It does not require any third-party API keys, tokens, or external cloud services:

| Key | Type | Default | Description |
|---|---|---|---|
| `video_monitor` | int | `1` | 1-based index of the monitor hosting video |
| `pause_delay` | float | `1.0` | Dwell duration (seconds) required before pausing |
| `resume_delay` | float | `0.3` | Lookback duration (seconds) required before resuming |
| `confidence` | float | `0.85` | Fraction of window frames that must agree |
| `fps` | int | `30` | Target camera acquisition FPS |
| `smoothing_window` | int | `20` | Circular buffer frame size for gaze smoothing |
| `camera_index` | int | `0` | Default webcam hardware index |
| `calibrated` | bool | `false` | Calibration status flag |

---

## Deployment & CI/CD

Because Attention Tracker is a Windows desktop application interacting directly with physical webcams and Windows audio/video APIs, deployment consists of two independent pipelines:

1. **Automated Binary Release (GitHub Actions)**:
   - Configured in [.github/workflows/ci.yml](.github/workflows/ci.yml) &bull; [View CI Workflow Runs](https://github.com/ShyamMohanvis/attention-tracker/actions/workflows/ci.yml)
   - Runs on `windows-latest`.
   - Executes the full `pytest` suite.
   - Compiles the self-contained `AttentionTracker.exe` via PyInstaller.
   - Packages and uploads `AttentionTracker-Windows.zip` as a workflow artifact.

2. **Web Portal & Documentation (GitHub Pages)**:
   - Configured in [.github/workflows/pages.yml](.github/workflows/pages.yml) &bull; [Live Website](https://shyammohanvis.github.io/attention-tracker/)
   - Automatically builds and publishes the interactive web showcase from `docs/index.html`.

---

## Project Structure

```
attention-tracker/
│
├── .github/
│   └── workflows/
│       ├── ci.yml               ← CI test & PyInstaller binary build
│       └── pages.yml            ← GitHub Pages documentation deployment
│
├── docs/
│   └── index.html               ← Web showcase & interactive simulator
│
├── src/
│   ├── app.py                   ← Entry point + QThread worker
│   ├── config.py                ← Settings singleton + face model constants
│   ├── settings.json            ← Persisted user settings
│   │
│   ├── assets/
│   │   └── face_landmarker.task ← MediaPipe model bundle
│   │
│   ├── camera/
│   │   ├── camera.py            ← OpenCV webcam capture + auto-detect
│   │   ├── calibration.py       ← Gaze sample collector for wizard
│   │   └── fps.py               ← Rolling FPS counter
│   │
│   ├── gaze/
│   │   ├── face_mesh.py         ← MediaPipe FaceMesh wrapper
│   │   ├── iris.py              ← Iris landmark extraction
│   │   ├── estimator.py         ← Head-pose + iris → gaze_x [-1, 1]
│   │   ├── smoothing.py         ← 20-frame sliding window
│   │   └── classifier.py       ← Nearest-centroid monitor classifier
│   │
│   ├── monitor/
│   │   ├── monitor_detector.py  ← win32api monitor enumeration
│   │   ├── geometry.py          ← MonitorGeometry dataclass
│   │   └── mapper.py            ← Gaze label → physical monitor
│   │
│   ├── controller/
│   │   ├── base.py              ← MediaController ABC + CompositeController
│   │   ├── media_session.py     ← Windows Media Session API (Priority 1)
│   │   ├── keyboard.py          ← Media key + focused window (Priority 2/3)
│   │   ├── chrome.py            ← Chrome/Edge specific
│   │   ├── vlc.py               ← VLC specific
│   │   └── spotify.py           ← Spotify specific
│   │
│   ├── ui/
│   │   ├── main_window.py       ← Dark-themed control panel
│   │   ├── calibration_window.py← Step-by-step wizard dialog
│   │   ├── tray.py              ← System tray icon + menu
│   │   └── icons/               ← App icon assets
│   │
│   └── utils/
│       ├── logger.py            ← Rotating file + coloured console logger
│       ├── timer.py             ← Monotonic dwell-time timer
│       └── state_machine.py     ← PLAYING ↔ PAUSED FSM
│
├── tests/
│   ├── test_state_machine.py
│   ├── test_smoothing.py
│   └── test_classifier.py
│
├── attention.spec               ← PyInstaller build spec
├── build.ps1                    ← PowerShell build script
├── build.bat                    ← Batch build script
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE).
