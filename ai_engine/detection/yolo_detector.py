"""
YOLO Detector – Person + Train detection with BoT-SORT tracking.
"""
import ai_engine.torch_patch  # MUST be first – patches torch.load before YOLO import

import cv2
from ultralytics import YOLO


class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf_thresh: float = 0.40):
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh
        print(f"[YOLO] Model loaded: {model_path}")

    def detect_and_track(self, frame):
        """
        Run inference + BoT-SORT tracking on one frame.
        Returns (persons, trains) – each a list of detection dicts.
        """
        results = self.model.track(
            frame,
            persist=True,
            conf=self.conf_thresh,
            tracker="botsort.yaml",
            verbose=False,
        )

        persons, trains = [], []

        if results and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf     = float(box.conf[0]) if box.conf  is not None else 0.0
                cls_id   = int(box.cls[0])    if box.cls   is not None else -1
                track_id = int(box.id[0])     if box.id    is not None else -1

                det = dict(bbox=(x1, y1, x2, y2), conf=conf,
                           class_id=cls_id, track_id=track_id)

                if cls_id == 0:    # COCO: person
                    persons.append(det)
                elif cls_id == 6:  # COCO: train
                    trains.append(det)

        return persons, trains
