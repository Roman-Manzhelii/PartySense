import vlc
import time
import threading

class YouTubePlayer:
    def __init__(self):
        self._instance = vlc.Instance([
            "--aout=alsa",
            "--network-caching=300",
            "--live-caching=300",
            "--file-caching=300",
            "--quiet"
        ])
        self._player = self._instance.media_player_new()
        self._lock = threading.Lock()
        self.current_stream_url = None

    def play_url(self, url: str, position: float = 0, volume: int = 50):
        with self._lock:
            if not url:
                print("[YouTubePlayer] No URL provided to play_url().")
                return

            media = self._instance.media_new(url)
            self._player.set_media(media)
            self._player.play()
            self.current_stream_url = url

            start_wait = time.time()
            while not self._player.is_playing():
                time.sleep(0.05)
                if (time.time() - start_wait) > 3.0:
                    break

            self._player.set_time(int(position * 1000))
            self._player.audio_set_volume(int(volume * 2))

    def pause(self):
        with self._lock:
            if self._player.is_playing():
                self._player.pause()

    def stop(self):
        with self._lock:
            self._player.stop()

    def seek(self, position: float):
        with self._lock:
            self._player.set_time(int(position * 1000))

    def set_volume(self, volume: int):
        with self._lock:
            self._player.audio_set_volume(int(volume * 2))
