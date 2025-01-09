# pubnub_pi/listeners.py

from pubnub.callbacks import SubscribeCallback
from pubnub.models.consumer.pubsub import PNMessageResult

class CommandListener(SubscribeCallback):
    def __init__(self, player, youtube_player, led_ring=None):
        super().__init__()
        self.player = player
        self.youtube_player = youtube_player
        self.led_ring = led_ring

    def message(self, pubnub, message: PNMessageResult):
        msg = message.message
        print(f"[CommandListener] Received command: {msg}")

        action = msg.get("action")
        if not action:
            return

        if action == "play_direct":
            duration = msg.get("duration", 0)
            position = msg.get("position", 0)
            # The direct audio/video stream URL:
            stream_url = msg.get("stream_url", "")
            volume = msg.get("volume", 50)  # or handle from preferences

            # Start playback with direct URL
            self.youtube_player.play_url(
                url=stream_url,
                position=position,
                volume=volume
            )

            # Update our local "virtual" Player
            self.player.load_track(duration, video_id="(direct)")  # or keep the real video_id somewhere
            self.player.seek(position)
            self.player.play()

            print(f"[CommandListener] Playing direct stream {stream_url} at position={position}, volume={volume}")
            return

        elif action == "pause":
            position = msg.get("position", None)
            if position is not None:
                self.player.seek(position)
                self.youtube_player.seek(position)  # реальне переміщення в плеєрі

            self.player.pause()
            self.youtube_player.pause()
            print(f"[CommandListener] Paused at position {position}")

        elif action == "seek":
            new_position = msg.get("position", 0)
            self.player.seek(new_position)
            self.youtube_player.seek(new_position)
            print(f"[CommandListener] Seeked to position {new_position}s")

        elif action == "set_volume":
            new_volume = msg.get("volume", 50)
            self.youtube_player.set_volume(new_volume)
            print(f"[CommandListener] Volume set to {new_volume}")

        elif action == "stop":
            self.player.stop()
            self.youtube_player.stop()
            print(f"[CommandListener] Stopped playback")

        elif action == "set_mode":
            mode = msg.get("mode", "default")
            if self.led_ring:
                self.led_ring.set_mode(mode)
            print(f"[CommandListener] LED mode set to '{mode}'")

        else:
            print(f"[CommandListener] Unknown or unimplemented action '{action}'")
