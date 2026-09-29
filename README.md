# RAILGUARD AI
**Intelligent Railway Platform Safety Monitoring System**

## 1. Project Introduction
RailGuard AI is a computer vision-based safety system designed to monitor railway platforms. It detects passengers, tracks their movement relative to a virtual danger zone, and evaluates the risk in real-time based on the train's state (Approaching, Stopped, Departing). If a passenger remains in the danger zone for more than the allowed threshold (e.g., 3 seconds) while a train is approaching or departing, the system issues a critical alert and records the incident.

## 2. Features
- Real-time Train State Detection (Approaching, Stopped, Departing)
- Passenger Detection and Tracking (YOLOv8 + ByteTrack)
- Configurable Virtual Danger Zone
- 3-Second Rule Evaluation Engine
- Incident Logging (SQLite/PostgreSQL)
- Live React Dashboard with WebSocket Telemetry
- Demo/Simulation Mode

## 3. Architecture
The system consists of:
- **AI Engine (Python/OpenCV)**: Analyzes video frames, detects objects, manages tracking, and evaluates risk.
- **Backend API (FastAPI)**: Serves endpoints, manages WebSocket telemetry for the live feed, and records incidents via SQLAlchemy.
- **Frontend Dashboard (React/Vite)**: A dark-themed, professional dashboard for live monitoring and analytics.
- **Database**: SQLite (default for demo) or PostgreSQL.

See `ARCHITECTURE.md` for a full system diagram.

## 4. Technologies
- **Backend**: Python 3, FastAPI, SQLAlchemy, Uvicorn, SQLite/PostgreSQL
- **AI/CV**: OpenCV, Ultralytics YOLOv8, ByteTrack (lapx)
- **Frontend**: React, Vite, TailwindCSS, Lucide React, Axios

## 5. Installation
Ensure you have Python 3 and Node.js installed.

```bash
# Clone the repository
# Navigate to the project root
cd RailGuard-AI

# Create virtual environment
python -m venv venv
# Activate on Windows
.\venv\Scripts\activate
# Activate on Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 6. PostgreSQL Setup (Optional)
By default, the system uses SQLite for ease of demonstration. To use PostgreSQL:
1. Install PostgreSQL.
2. Create a database `railguard`.
3. In the project root, create a `.env` file and set the DB URL:
`DATABASE_URL=postgresql+psycopg://postgres:password@localhost/railguard`
4. Reinstall requirements with psycopg support (e.g., `pip install psycopg[binary]`).

## 7. Python Setup
Run `scripts/generate_dummy_video.py` to generate a demo video if you do not have a CCTV recording.
Download the YOLOv8 model: `curl -o yolov8n.pt -L https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt`

## 8. Frontend Setup
```bash
cd frontend
npm install
```

## 9. How to Run
Start the backend API and AI Engine:
```bash
# From project root
.\venv\Scripts\activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Start the React Frontend:
```bash
# In a new terminal
cd frontend
npm run dev
```

## 10. How to Upload Video
1. Open the frontend dashboard (http://localhost:5173).
2. Click "Upload Video" and select an MP4 file.
3. If no video is uploaded, the system will look for `data/input/demo.mp4`.

## 11. How to Use Dashboard
- Click **Start Monitoring** to begin AI processing.
- The **Live Platform Camera** view shows bounding boxes, danger line, and tracking IDs.
- The **Active Alerts** panel displays real-time warnings.
- The **Incident History** and **System Analytics** update automatically.

## 12. How AI Detection Works
1. `YOLODetector` infers bounding boxes for `person` and `train` classes.
2. `ByteTrack` assigns consistent tracking IDs.
3. The `TrainStateDetector` calculates frame-to-frame movement of the train bounding box to determine its state.

## 13. Danger Zone Logic
The virtual line is defined in `ai_engine/danger_zone/zone_config.json`.
The mathematical cross-product of the line coordinates and the passenger's feet `(x, y)` coordinate is calculated to determine if the passenger is on the safe or danger side.

## 14. 3-Second Decision Logic
When a passenger crosses into the danger zone, a timer starts (`danger_enter_time`). If the `danger_duration` reaches 3.0 seconds, the `RiskEngine` evaluates the train state. 
- Train Approaching + >=3s = CRITICAL
- Train Departing + >=3s = HIGH

## 15. Database Structure
Tables:
- `incidents`: ID, timestamp, camera_id, passenger_id, train_state, danger_duration, risk_level, reason, snapshot_path, status.
- `alerts`: Real-time system logs.

## 16. API Documentation
- `GET /api/status`: System state
- `POST /api/monitor/start`: Starts AI loop
- `POST /api/monitor/stop`: Stops AI loop
- `GET /api/incidents`: Fetch logs
- `WS /ws/monitor`: Stream JSON telemetry and base64 MJPEG frames.

## 17. Troubleshooting
- **No Video Feed**: Ensure `demo.mp4` exists or a video is uploaded.
- **WebSocket Disconnected**: Verify the FastAPI server is running on port 8000.
- **Model Missing**: Ensure `yolov8n.pt` is in the project root.

## 18. Demo Instructions
Run the frontend and backend. Upload a video (or let it fallback to demo.mp4). Click "Start Monitoring". Observe the bounding boxes and real-time alerts.

---
### References
1. Sehchan Oh, Sunghyuk Park, Changmu Lee, “A Platform Surveillance Monitoring System Using Image Processing for Passenger Safety in Railway Station,” Proceedings of the International Conference on Control, Automation and Systems (ICCAS 2007), Seoul, South Korea, pp. 394–398. https://ieeexplore.ieee.org/document/4406975
2. Sehchan Oh, Sunghyuk Park, Changmu Lee, “Vision Based Platform Monitoring System for Railway Station Safety,” Proceedings of the 7th International Conference on ITS Telecommunications (ITST 2007). https://ieeexplore.ieee.org/document/4295854
3. Joseph Redmon, Santosh Divvala, Ross Girshick, Ali Farhadi, “You Only Look Once: Unified, Real-Time Object Detection,” Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR 2016), pp. 779–788. https://openaccess.thecvf.com/content_cvpr_2016/papers/Redmon_You_Only_Look_CVPR_2016_paper.pdf
