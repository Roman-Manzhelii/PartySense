from pubnub.pubnub import PubNub
from pubnub.callbacks import SubscribeCallback
from pubnub_config import get_pubnub_config

class SettingsListener(SubscribeCallback):
    def __init__(self, led_ring, speaker):
        super().__init__()
        self.led_ring = led_ring
        self.speaker = speaker

    def message(self, pubnub, message):
        print(f"[SettingsListener] Received message: {message.message}")
        volume = message.message.get("volume")
        led_mode = message.message.get("led_mode")
        if volume is not None:
            self.speaker.set_volume(volume)
            print(f"[SettingsListener] Volume set to {volume}")
        if led_mode is not None:
            self.led_ring.set_mode(led_mode)
            print(f"[SettingsListener] LED mode set to {led_mode}")

class PubNubSubscriber:
    def __init__(self, channel: str, listener: SubscribeCallback):
        self._channel = channel
        self._pubnub = PubNub(get_pubnub_config())
        self._listener = listener

    def start_listening(self):
        """Subscribe to the given channel and add the provided listener."""
        print(f"[PubNubSubscriber] Subscribing to channel: {self._channel}")
        self._pubnub.add_listener(self._listener)
        self._pubnub.subscribe().channels(self._channel).execute()

    def stop_listening(self):
        """Unsubscribe from the channel."""
        print(f"[PubNubSubscriber] Unsubscribing from channel: {self._channel}")
        self._pubnub.unsubscribe().channels(self._channel).execute()