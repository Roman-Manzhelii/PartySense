import time

class PIRSensor:
    def __init__(self):
        self.mock_motion_detected = False

    def detect_motion(self):
        current_time = int(time.time())
        if current_time % 10 < 5:
            return True
        return False
