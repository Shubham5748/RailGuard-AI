"""
Video Processor – orchestrates YOLO, tracking, danger-zone, risk engine.
"""
import sys, os, time
import cv2

from ai_engine.detection.yolo_detector       import YOLODetector
from ai_engine.tracking.passenger_tracker    import PassengerTracker
from ai_engine.danger_zone.virtual_line      import VirtualDangerZone
from ai_engine.train_detection.train_state   import TrainStateDetector
from ai_engine.decision_engine.risk_engine   import RiskEngine


class VideoProcessor:
    def __init__(self, model_path="yolov8n.pt",
                 config_path="ai_engine/danger_zone/zone_config.json",
                 on_alert_callback=None):
        self.detector      = YOLODetector(model_path=model_path)
        self.tracker       = PassengerTracker()
        self.zone          = VirtualDangerZone(config_path=config_path)
        self.train_det     = TrainStateDetector()
        self.risk_engine   = RiskEngine(danger_duration_threshold=3.0)
        self.on_alert      = on_alert_callback

    # ── main entry ──────────────────────────────────────────────────────────
    def process_frame(self, frame):
        persons, trains = self.detector.detect_and_track(frame)

        train_state, _ = self.train_det.update(trains)
        passengers     = self.tracker.update(persons, self.zone.check_zone)

        safe_count, danger_count = 0, 0
        alerts = []

        for tid, p in passengers.items():
            in_danger = p["zone"] == "DANGER_ZONE"
            if in_danger:
                danger_count += 1
            else:
                safe_count += 1

            risk, alert_required, reason = self.risk_engine.evaluate_risk(
                train_state=train_state,
                in_danger_zone=in_danger,
                danger_duration=p["danger_duration"],
            )
            p["risk_level"] = risk

            if alert_required:
                info = dict(passenger_id=tid, train_state=train_state,
                            danger_duration=p["danger_duration"],
                            risk_level=risk, reason=reason)
                alerts.append(info)
                if self.on_alert:
                    self.on_alert(info)

        self._draw(frame, passengers, trains, train_state, safe_count, danger_count)

        return frame, dict(train_state=train_state,
                           safe_count=safe_count,
                           danger_count=danger_count,
                           passengers=passengers,
                           alerts=alerts)

    # ── drawing ─────────────────────────────────────────────────────────────
    def _draw(self, frame, passengers, trains, train_state, safe, danger):
        # Danger line
        cv2.line(frame, self.zone.line_start, self.zone.line_end, (0, 255, 255), 3)
        cv2.putText(frame, "DANGER LINE", (self.zone.line_start[0] + 5,
                    self.zone.line_start[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Trains
        for t in trains:
            x1, y1, x2, y2 = t["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)
            cv2.putText(frame, f"Train {t['track_id']} | {train_state}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 140, 0), 2)

        # Passengers
        COLORS = {"LOW": (0,220,80), "MEDIUM": (0,220,220),
                  "HIGH": (0,160,255), "CRITICAL": (0,0,255)}
        for tid, p in passengers.items():
            x1, y1, x2, y2 = p["bbox"]
            risk  = p.get("risk_level", "LOW")
            dur   = p.get("danger_duration", 0.0)
            color = COLORS.get(risk, (0, 220, 80))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            fx, fy = p["feet"]
            cv2.circle(frame, (fx, fy), 5, (255, 255, 255), -1)

            label = f"#{tid} | {risk}"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            if p["zone"] == "DANGER_ZONE":
                cv2.putText(frame, f"DANGER {dur:.1f}s",
                            (x1, y1 - 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # HUD
        cv2.putText(frame, f"SAFE: {safe}",
                    (12, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 80), 2)
        cv2.putText(frame, f"DANGER: {danger}",
                    (12, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"TRAIN: {train_state}",
                    (12, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 140, 0), 2)
        cv2.putText(frame, "RAILGUARD AI",
                    (frame.shape[1] - 200, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 200, 255), 2)
