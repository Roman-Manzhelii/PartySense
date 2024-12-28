# pubnub/status_publisher.py
from pubnub_pi.publisher import PubNubPublisher
from threading import Thread
import time

class StatusPublisher:
    def __init__(self, channel_name_status, player, google_id):
        self.channel_name_status = channel_name_status
        self.pubnub_publisher = PubNubPublisher(channel_name_status)
        self.player = player
        self.google_id = google_id
        self.stop_flag = False
        self.thread = None

    def start(self):
        self.stop_flag = False
        self.thread = Thread(target=self._loop)
        self.thread.start()

    def stop(self):
        self.stop_flag = True
        if self.thread:
            self.thread.join()

    def _loop(self):
        while not self.stop_flag:
            self.publish_status()
            time.sleep(2)  # Публікуємо кожні 2 секунди

    def publish_status(self):
        song_state = self.player.get_current_state()
        message = {
            "user_id": self.google_id,
            "current_song": {
                "video_id": "dummy_video_id",  # Замініть на реальний video_id, якщо доступний
                "title": "Dummy Title",         # Замініть на реальний title, якщо доступний
                "state": song_state["state"],
                "position": song_state["position"],
                "duration": song_state["duration"]
            }
        }
        self.pubnub_publisher.publish_message(message)
