import cv2
import numpy as np

def create_dummy_video():
    out = cv2.VideoWriter('data/input/demo.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
    for i in range(90):  # 3 seconds at 30 fps
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw a moving box (simulate train)
        tx = max(0, 600 - i * 5)
        cv2.rectangle(frame, (tx, 100), (tx+100, 200), (255, 255, 255), -1)
        
        # Draw a moving box (simulate person moving into danger zone)
        px = 250
        py = min(400, 150 + i * 3) # moves down towards danger line
        cv2.rectangle(frame, (px, py), (px+30, py+50), (255, 255, 255), -1)
        
        out.write(frame)
    out.release()

if __name__ == "__main__":
    create_dummy_video()
