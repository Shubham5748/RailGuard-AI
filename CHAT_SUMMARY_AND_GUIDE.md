# RailGuard AI — Complete Project & Chat Reference Guide

**Project Title:** RAILGUARD AI: Intelligent Railway Platform Safety Monitoring System  
**Institution:** ABES Institute of Technology, Ghaziabad  
**Department:** Computer Science & Engineering (AI), AKTU  
**Session:** 2026–27  
**GitHub Repository:** [https://github.com/Shubham5748/RailGuard-AI](https://github.com/Shubham5748/RailGuard-AI)

---

## 1. Project Overview & Methodology

RailGuard AI is an automated railway safety surveillance system that monitors platform edges and alerts operators when passengers remain in high-risk zones while trains are approaching.

### Core Processing Pipeline:
1. **Video Acquisition:** CCTV camera stream or uploaded video file.
2. **Train State Detection:** Determines train motion status (`APPROACHING`, `STOPPED`, `DEPARTING`) across consecutive frames.
3. **Passenger Detection & Tracking:** YOLOv8 detection + object tracking (BoT-SORT / ByteTrack) using foot-level ground contact points.
4. **Virtual Danger Zone Analysis:** Vector cross-product intersection calculation based on configurable platform line coordinates:
   - Default Start Point: `(215, 800)`
   - Default End Point: `(275, 171)`
   - Config file: `ai_engine/danger_zone/zone_config.json`
5. **Context-Aware 3-Second Risk Engine:**
   - Evaluates danger zone dwell time.
   - Dwell time < 3.0s: LOW risk.
   - Dwell time ≥ 3.0s + Train `STOPPED`: HIGH warning.
   - Dwell time ≥ 3.0s + Train `APPROACHING`: **CRITICAL ALERT** (Triggers safety response & database logging).
6. **Alert & Database Storage:** Logs incident telemetry, timestamps, passenger IDs, and risk levels to SQLite/PostgreSQL.
7. **Frontend Dashboard:** Real-time dark-mode control room built with React, Vite, and Tailwind CSS.

---

## 2. Project Architecture & Directory Layout

```text
RailGuard-AI/
├── README.md                           # Documentation & references
├── ARCHITECTURE.md                     # Data-flow diagrams (Mermaid)
├── requirements.txt                    # Python dependencies
├── yolov8n.pt                          # YOLOv8 object detection weights
├── railguard.db                        # SQLite database
│
├── ai_engine/
│   ├── torch_patch.py                  # PyTorch 2.14 weights_only patch
│   ├── detection/
│   │   └── yolo_detector.py            # YOLOv8 Person/Train detector
│   ├── tracking/
│   │   └── passenger_tracker.py        # Foot-point & danger dwell tracker
│   ├── danger_zone/
│   │   ├── virtual_line.py             # Cross-product geometry calculation
│   │   └── zone_config.json            # Dynamic line coordinates
│   ├── train_detection/
│   │   └── train_state.py              # Temporal train movement analysis
│   ├── decision_engine/
│   │   └── risk_engine.py              # 3-second context-aware risk rules
│   └── video_processing/
│       └── processor.py                # Main orchestrator & overlay drawing
│
├── backend/
│   └── app/
│       └── main.py                     # Starlette server, WebSocket, REST APIs
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     # Dashboard UI, WSS/HTTP fallback
│   │   ├── index.css                   # Tailwind styles
│   │   └── main.jsx                    # Root React entrypoint
│   └── dist/                           # Compiled production build
│
├── database/
│   └── schema.sql                      # PostgreSQL DDL schema
│
└── tests/
    └── test_logic.py                   # Risk engine unit tests
```

---

## 3. How to Run the Project Locally

### Step 1: Open PowerShell
```powershell
cd C:\Users\user\.gemini\antigravity\scratch\RailGuard-AI
```

### Step 2: Start the Backend (API + AI Engine)
```powershell
$env:KMP_DUPLICATE_LIB_OK="TRUE"
$env:PYTHONPATH="."
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Access the Dashboard
- **Local URL:** [http://localhost:8000](http://localhost:8000) (Serves both the React frontend and backend APIs)
- Or run the Vite dev server separately:
  ```powershell
  cd frontend
  npm run dev
  ```
  Visit [http://localhost:5173](http://localhost:5173).

---

## 4. Key Engineering Fixes Applied During Development

1. **Python 3.14 Compatibility:**
   - Standard FastAPI/Pydantic v2 failed to build on Windows due to Rust C++ compilation requirements (`pydantic-core`).
   - Resolved by implementing a clean, pure-Python **Starlette** application layer that runs natively without C++ compiler tools.

2. **PyTorch 2.14 YOLO Loading:**
   - PyTorch 2.14 introduced strict `weights_only=True` restrictions on `torch.load`.
   - Created `ai_engine/torch_patch.py` to allow Ultralytics model weights to load reliably.

3. **HTTPS / WebSocket Tunnel Compatibility:**
   - Fixed mixed-content browser security blocks when tunneling over HTTPS by automatically selecting `wss://` vs `ws://`.
   - Added an automatic HTTP polling stream fallback (`/api/monitor/frame`) so the live video feed continues running even if WebSockets are blocked by proxies.

4. **React Error Boundary:**
   - Wrapped `App.jsx` in an `ErrorBoundary` with defensive null checks across telemetry data to prevent blank screen errors.

---

## 5. Academic References (Preserved from PPT)

1. **Oh, C., et al. (2007):** "Development of an Automated Railway Platform Safety Monitoring System using Computer Vision," *ICCAS 2007*, IEEE.
2. **Oh, C., et al. (2007):** "Platform Safety Monitoring System for Railway Stations based on Video Analysis," *ITST 2007*, IEEE.
3. **Redmon, J., et al. (2016):** "You Only Look Once: Unified, Real-Time Object Detection," *CVPR 2016*, IEEE.
