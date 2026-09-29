import time

class PassengerTracker:
    def __init__(self):
        # Dictionary to store passenger data
        # { track_id: { "bbox": (x1,y1,x2,y2), "feet": (x,y), "zone": "SAFE", "danger_enter_time": None, "danger_duration": 0.0, "risk_level": "LOW", "conf": 0.0 } }
        self.passengers = {}

    def update(self, detected_persons, check_zone_func):
        """
        Updates the tracker with current frame detections.
        """
        current_ids = set()
        
        current_time = time.time()

        for person in detected_persons:
            track_id = person["track_id"]
            if track_id == -1:
                continue
                
            current_ids.add(track_id)
            x1, y1, x2, y2 = person["bbox"]
            conf = person["conf"]
            
            # Calculate feet point
            feet = (int((x1 + x2) / 2), y2)
            
            # Check zone (0 = SAFE, 1 = DANGER)
            # We assume check_zone_func returns 0 for safe, 1 for danger
            in_danger = check_zone_func(feet) == 1
            current_zone = "DANGER_ZONE" if in_danger else "SAFE_ZONE"

            if track_id not in self.passengers:
                self.passengers[track_id] = {
                    "bbox": (x1, y1, x2, y2),
                    "feet": feet,
                    "zone": current_zone,
                    "danger_enter_time": current_time if in_danger else None,
                    "danger_duration": 0.0,
                    "risk_level": "LOW",
                    "conf": conf
                }
            else:
                p_data = self.passengers[track_id]
                p_data["bbox"] = (x1, y1, x2, y2)
                p_data["feet"] = feet
                p_data["conf"] = conf
                
                prev_zone = p_data["zone"]
                p_data["zone"] = current_zone

                if current_zone == "DANGER_ZONE":
                    if prev_zone != "DANGER_ZONE" or p_data["danger_enter_time"] is None:
                        p_data["danger_enter_time"] = current_time
                        p_data["danger_duration"] = 0.0
                    else:
                        p_data["danger_duration"] = current_time - p_data["danger_enter_time"]
                else:
                    p_data["danger_enter_time"] = None
                    p_data["danger_duration"] = 0.0

        # Remove passengers that are no longer tracked
        # In a real app we might want to keep history, but for memory we clear them if not seen.
        # Alternatively, we could keep them for a few frames.
        lost_ids = set(self.passengers.keys()) - current_ids
        for lost_id in lost_ids:
            del self.passengers[lost_id]
            
        return self.passengers
