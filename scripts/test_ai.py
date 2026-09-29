import sys, os
sys.path.insert(0, '.')
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Test 1: torch patch + YOLO load
from ai_engine.detection.yolo_detector import YOLODetector
det = YOLODetector('yolov8n.pt')
print('TEST 1 PASS: YOLO loaded')

# Test 2: run detection on a dummy frame
import numpy as np
import cv2
frame = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.rectangle(frame, (100, 100), (200, 300), (255, 255, 255), -1)
persons, trains = det.detect_and_track(frame)
print("TEST 2 PASS: Detection ran. persons=%d, trains=%d" % (len(persons), len(trains)))

# Test 3: full processor
from ai_engine.video_processing.processor import VideoProcessor
proc = VideoProcessor(model_path='yolov8n.pt')
out_frame, telemetry = proc.process_frame(frame)
ts = telemetry["train_state"]
print("TEST 3 PASS: Processor ran. train_state=%s" % ts)

print()
print("=== ALL AI TESTS PASSED ===")
