import numpy as np

class TrainStateDetector:
    def __init__(self):
        self.previous_trains = {}  # track_id -> bounding_box_center_x
        self.train_status = "STOPPED"
        self.movement_threshold = 2.0  # minimum pixels to consider moving
        
    def update(self, detected_trains):
        """
        Updates train state based on train detections across frames.
        detected_trains: list of dicts with bbox and track_id
        """
        if not detected_trains:
            # If no train is detected, default to STOPPED or maintain previous state.
            # Here we maintain the previous state for a few frames, but for simplicity:
            return "STOPPED", 0.0

        # We'll just look at the first/largest train for simplicity
        train = detected_trains[0]
        track_id = train["track_id"]
        x1, y1, x2, y2 = train["bbox"]
        conf = train["conf"]
        
        current_center_x = (x1 + x2) / 2
        
        if track_id not in self.previous_trains:
            self.previous_trains[track_id] = current_center_x
            return "STOPPED", conf
            
        prev_center_x = self.previous_trains[track_id]
        
        diff = current_center_x - prev_center_x
        
        if abs(diff) > self.movement_threshold:
            # Depending on camera angle, train moving left/right means approaching or departing
            # Let's assume negative diff is APPROACHING (moving left), positive is DEPARTING (moving right)
            # This is highly dependent on camera perspective, but serves as a generic logic.
            if diff < 0:
                self.train_status = "APPROACHING"
            else:
                self.train_status = "DEPARTING"
        else:
            self.train_status = "STOPPED"
            
        self.previous_trains[track_id] = current_center_x
        
        return self.train_status, conf
