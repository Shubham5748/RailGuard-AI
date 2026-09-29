class RiskEngine:
    def __init__(self, danger_duration_threshold=3.0):
        self.danger_duration_threshold = danger_duration_threshold

    def evaluate_risk(self, train_state, in_danger_zone, danger_duration):
        """
        Evaluates risk based on context.
        """
        if not in_danger_zone:
            return "LOW", False, "Safe zone."
            
        if danger_duration < self.danger_duration_threshold:
            return "MEDIUM", False, f"In danger zone, but duration ({danger_duration:.1f}s) < threshold."
            
        # Danger duration >= threshold
        if train_state == "APPROACHING":
            return "CRITICAL", True, f"Passenger in danger zone for {danger_duration:.1f}s while train is APPROACHING."
            
        if train_state == "DEPARTING":
            return "HIGH", True, f"Passenger in danger zone for {danger_duration:.1f}s while train is DEPARTING."
            
        if train_state == "STOPPED":
            return "HIGH", False, f"Passenger in danger zone for {danger_duration:.1f}s while train is STOPPED."
            
        return "LOW", False, "Unknown state."
