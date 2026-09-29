import json
import os

class VirtualDangerZone:
    def __init__(self, config_path="ai_engine/danger_zone/zone_config.json"):
        self.config_path = config_path
        self.line_start = (215, 800)
        self.line_end = (275, 171)
        self.danger_side = 1
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                self.line_start = tuple(config.get("line_start", (215, 800)))
                self.line_end = tuple(config.get("line_end", (275, 171)))
                self.danger_side = config.get("danger_side", 1)
            except Exception as e:
                print(f"Error loading zone config: {e}")

    def update_config(self, line_start, line_end, danger_side=1):
        self.line_start = tuple(line_start)
        self.line_end = tuple(line_end)
        self.danger_side = danger_side
        
        # Save to file
        try:
            with open(self.config_path, "w") as f:
                json.dump({
                    "line_start": list(self.line_start),
                    "line_end": list(self.line_end),
                    "danger_side": self.danger_side
                }, f, indent=4)
        except Exception as e:
            print(f"Error saving zone config: {e}")

    def check_zone(self, point):
        """
        Returns 1 if the point is on the danger side of the line, else 0.
        Uses cross product to determine side.
        """
        x, y = point
        x1, y1 = self.line_start
        x2, y2 = self.line_end
        
        # Cross product
        cross_product = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        
        # Assuming < 0 is side 0 (Safe) and >= 0 is side 1 (Danger)
        side = 0 if cross_product < 0 else 1
        
        return 1 if side == self.danger_side else 0
