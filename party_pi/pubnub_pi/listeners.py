# pubnub/listeners.py
from pubnub.callbacks import SubscribeCallback
from pubnub.models.consumer.pubsub import PNMessageResult

class CommandListener(SubscribeCallback):
    """
    Слухає PubNub-канал команд і виконує відповідні дії на Player та LED.
    """
    def __init__(self, player, led_ring):
        super().__init__()
        self.player = player
        self.led_ring = led_ring

    def message(self, pubnub, message: PNMessageResult):
        msg = message.message
        print(f"[CommandListener] Received command: {msg}")

        action = msg.get("action")
        if not action:
            return

        if action == "play":
            duration = msg.get("duration", 0)
            position = msg.get("position", 0)
            video_id = msg.get("video_id", "dummy_video_id")
            title = msg.get("title", "Unknown Title")
            # Завантажуємо трек
            self.player.load_track(duration)
            self.player.seek(position)
            self.player.play()
            print(f"[CommandListener] Playing '{title}' (Video ID: {video_id}) from position {position}s")

        elif action == "pause":
            position = msg.get("position", None)
            if position is not None:
                self.player.seek(position)
            self.player.pause()
            print(f"[CommandListener] Paused at position {position}s")

        elif action == "resume":
            position = msg.get("position", None)
            if position is not None:
                self.player.seek(position)
            self.player.resume()
            print(f"[CommandListener] Resumed at position {position}s")

        elif action == "seek":
            new_position = msg.get("position", 0)
            self.player.seek(new_position)
            print(f"[CommandListener] Seeked to position {new_position}s")

        elif action == "set_mode":
            mode = msg.get("mode", "default")
            self.led_ring.set_mode(mode)
            print(f"[CommandListener] LED mode set to '{mode}'")

        elif action in ["next", "previous"]:
            print(f"[CommandListener] Ignoring '{action}' as we have no real playlist logic.")

        else:
            print(f"[CommandListener] Unknown action '{action}'")
