"""
RailGuard AI — Pure Starlette Backend
Works on Python 3.14 with no Rust/C++ compilation.
No Pydantic required.
"""

import os, sys, time, base64, json, asyncio, shutil, threading, sqlite3
from datetime import datetime
from typing import Optional

import cv2
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

# ──────────────────────────────────────────────
# SQLite — no extra driver needed
# ──────────────────────────────────────────────
DB_PATH = "railguard.db"

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT    DEFAULT (datetime('now')),
            camera_id     INTEGER DEFAULT 1,
            passenger_id  INTEGER,
            train_state   TEXT,
            danger_duration REAL,
            risk_level    TEXT,
            reason        TEXT,
            status        TEXT    DEFAULT 'OPEN'
        )
    """)
    conn.commit()
    conn.close()

_init_db()

# ──────────────────────────────────────────────
# Shared app state
# ──────────────────────────────────────────────
state = {
    "is_monitoring": False,
    "video_path": None,
    "frame_b64": None,
    "telemetry": {
        "train_state": "STOPPED",
        "safe_count": 0,
        "danger_count": 0,
        "alerts": [],
    },
}
ws_clients = []

# ──────────────────────────────────────────────
# Alert / incident save
# ──────────────────────────────────────────────
def save_incident(alert: dict):
    conn = _get_conn()
    conn.execute(
        """INSERT INTO incidents
           (passenger_id, train_state, danger_duration, risk_level, reason)
           VALUES (?, ?, ?, ?, ?)""",
        (
            alert.get("passenger_id", -1),
            alert.get("train_state", "UNKNOWN"),
            alert.get("danger_duration", 0.0),
            alert.get("risk_level", "CRITICAL"),
            alert.get("reason", ""),
        ),
    )
    conn.commit()
    conn.close()

# ──────────────────────────────────────────────
# Demo video generator
# ──────────────────────────────────────────────
def _make_demo_video(path: str):
    import numpy as np
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w, h = 640, 480
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 25, (w, h))
    for i in range(150):
        frame = np.full((h, w, 3), (30, 30, 50), dtype=np.uint8)
        tx = max(0, w - i * 3)
        cv2.rectangle(frame, (tx, 80), (tx + 200, 220), (200, 100, 50), -1)
        cv2.putText(frame, "TRAIN", (tx + 10, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        py = min(h - 70, 80 + i * 2)
        cv2.rectangle(frame, (290, py), (325, py + 65), (50, 200, 80), -1)
        cv2.putText(frame, "PERSON", (272, py - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 100), 1)
        out.write(frame)
    out.release()
    print(f"[DEMO] Video written to {path}")

# ──────────────────────────────────────────────
# Video processing thread
# ──────────────────────────────────────────────
def _processing_loop():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root not in sys.path:
        sys.path.insert(0, root)

    try:
        from ai_engine.video_processing.processor import VideoProcessor
        processor = VideoProcessor(
            model_path="yolov8n.pt",
            config_path="ai_engine/danger_zone/zone_config.json",
            on_alert_callback=save_incident,
        )
        using_ai = True
        print("[AI] VideoProcessor loaded.")
    except Exception as e:
        print(f"[WARNING] AI engine unavailable: {e}. Running in visual-only mode.")
        processor = None
        using_ai = False

    path = state["video_path"] or "data/input/demo.mp4"
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open: {path}")
        state["is_monitoring"] = False
        return

    print(f"[INFO] Processing: {path}")
    while state["is_monitoring"]:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        try:
            if using_ai and processor:
                processed, telemetry = processor.process_frame(frame)
                state["telemetry"] = {
                    "train_state": telemetry.get("train_state", "STOPPED"),
                    "safe_count":  telemetry.get("safe_count", 0),
                    "danger_count": telemetry.get("danger_count", 0),
                    "alerts":      telemetry.get("alerts", []),
                }
            else:
                processed = frame.copy()
                cv2.line(processed, (215, 480), (275, 0), (0, 255, 255), 3)
                cv2.putText(processed, "RAILGUARD AI - DEMO MODE",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
                cv2.putText(processed, f"Train: {state['telemetry']['train_state']}",
                            (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 50), 2)

            ok, buf = cv2.imencode(".jpg", processed, [cv2.IMWRITE_JPEG_QUALITY, 72])
            if ok:
                state["frame_b64"] = base64.b64encode(buf.tobytes()).decode()
        except Exception as e:
            print(f"[FRAME ERR] {e}")

        time.sleep(0.04)

    cap.release()
    print("[INFO] Processing stopped.")

# ──────────────────────────────────────────────
# REST handlers
# ──────────────────────────────────────────────
async def health(request: Request):
    return JSONResponse({"status": "ok", "time": datetime.utcnow().isoformat()})

async def get_status(request: Request):
    return JSONResponse({"is_monitoring": state["is_monitoring"]})

async def get_frame(request: Request):
    return JSONResponse({
        "is_monitoring": state["is_monitoring"],
        "telemetry": state["telemetry"],
        "frame": state["frame_b64"]
    })

async def start_monitor(request: Request):
    if state["is_monitoring"]:
        return JSONResponse({"message": "Already monitoring"})
    if not state["video_path"]:
        demo = "data/input/demo.mp4"
        if not os.path.exists(demo):
            _make_demo_video(demo)
        state["video_path"] = demo
    state["is_monitoring"] = True
    threading.Thread(target=_processing_loop, daemon=True).start()
    return JSONResponse({"message": "Started"})

async def stop_monitor(request: Request):
    state["is_monitoring"] = False
    return JSONResponse({"message": "Stopped"})

async def upload_video(request: Request):
    form  = await request.form()
    video = form.get("file")
    if video is None:
        return JSONResponse({"error": "No file"}, status_code=400)
    os.makedirs("data/input", exist_ok=True)
    dest = f"data/input/{video.filename}"
    content = await video.read()
    with open(dest, "wb") as f:
        f.write(content)
    state["video_path"] = dest
    return JSONResponse({"message": f"Uploaded {video.filename}"})

async def get_incidents(request: Request):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return JSONResponse([dict(r) for r in rows])

async def get_analytics(request: Request):
    conn = _get_conn()
    total    = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    critical = conn.execute("SELECT COUNT(*) FROM incidents WHERE risk_level='CRITICAL'").fetchone()[0]
    high     = conn.execute("SELECT COUNT(*) FROM incidents WHERE risk_level='HIGH'").fetchone()[0]
    conn.close()
    return JSONResponse({"total_incidents": total, "critical_alerts": critical, "high_alerts": high})

# ──────────────────────────────────────────────
# WebSocket
# ──────────────────────────────────────────────
async def ws_monitor(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        while True:
            if state["is_monitoring"] and state["frame_b64"]:
                payload = json.dumps({
                    "telemetry": state["telemetry"],
                    "frame":     state["frame_b64"],
                })
                await websocket.send_text(payload)
            await asyncio.sleep(0.08)
    except Exception:
        pass
    finally:
        if websocket in ws_clients:
            ws_clients.remove(websocket)

# ──────────────────────────────────────────────
# App routes
# CRITICAL: API and WebSocket routes FIRST, Mount LAST!
# ──────────────────────────────────────────────
frontend_dist = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "dist"
)

routes = [
    Route("/api/health",          health),
    Route("/api/status",          get_status),
    Route("/api/monitor/frame",   get_frame),
    Route("/api/monitor/start",   start_monitor, methods=["POST"]),
    Route("/api/monitor/stop",    stop_monitor,  methods=["POST"]),
    Route("/api/video/upload",    upload_video,  methods=["POST"]),
    Route("/api/incidents",       get_incidents),
    Route("/api/analytics",       get_analytics),
    WebSocketRoute("/ws/monitor", ws_monitor),
    Mount("/", app=StaticFiles(directory=frontend_dist, html=True), name="frontend"),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(routes=routes, middleware=middleware)
