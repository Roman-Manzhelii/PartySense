# player/player.py
import threading
import time

class Player:
    """
    Імітує відтворення треку:
    - зберігає поточний state (playing/paused) та position,
    - у фоні збільшує position кожну секунду, поки state == "playing".
    """
    def __init__(self, on_update_callback=None):
        self.state = "paused"
        self.duration = 0
        self.position = 0
        self.video_id = "unknown"
        self.title = "Unknown Title"
        self.thumbnail_url = ""
        self.mode = "default"
        self.motion_detected = True
        self.updated_at = time.time()
        self.lock = threading.Lock()
        self.thread = None
        self.stop_flag = False
        self.on_update_callback = on_update_callback

    def load_track(self, duration: float, video_id: str = "unknown", title: str = "Unknown Title", thumbnail_url: str = ""):
        with self.lock:
            self.duration = duration
            self.position = 0
            self.state = "paused"
            self.video_id = video_id
            self.title = title
            self.thumbnail_url = thumbnail_url
            self.updated_at = time.time()
        self._notify_update()

    def play(self):
        with self.lock:
            self.state = "playing"
            self.updated_at = time.time()
        self._notify_update()

    def pause(self):
        with self.lock:
            self.state = "paused"
            self.updated_at = time.time()
        self._notify_update()

    def resume(self):
        with self.lock:
            if self.state != "playing":
                self.state = "playing"
                self.updated_at = time.time()
        self._notify_update()

    def seek(self, new_position: float):
        with self.lock:
            self.position = min(max(new_position, 0), self.duration)
            self.updated_at = time.time()
        self._notify_update()

    def stop(self):
        with self.lock:
            self.state = "paused"
            self.position = 0
            self.updated_at = time.time()
        self._notify_update()

    def set_motion_detected(self, detected: bool):
        with self.lock:
            self.motion_detected = detected
            self.updated_at = time.time()
        self._notify_update()

    def set_mode(self, mode: str):
        with self.lock:
            self.mode = mode
            self.updated_at = time.time()
        self._notify_update()

    def start_background(self):
        self.stop_flag = False
        self.thread = threading.Thread(target=self._loop)
        self.thread.start()

    def stop_background(self):
        self.stop_flag = True
        if self.thread:
            self.thread.join()

    def _loop(self):
        while not self.stop_flag:
            with self.lock:
                if self.state == "playing":
                    self.position += 1
                    if self.position >= self.duration:
                        self.position = self.duration
                        self.state = "paused"
                        self.updated_at = time.time()
                        self._notify_update()
            time.sleep(1)

    def get_current_state(self):
        with self.lock:
            return {
                "state": self.state,
                "position": self.position,
                "duration": self.duration,
                "video_id": self.video_id,
                "title": self.title,
                "thumbnail_url": self.thumbnail_url,
                "mode": self.mode,
                "motion_detected": self.motion_detected,
                "updated_at": self.updated_at
            }

    def _notify_update(self):
        if self.on_update_callback:
            self.on_update_callback()
