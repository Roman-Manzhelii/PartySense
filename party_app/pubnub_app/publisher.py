from pubnub.pubnub import PubNub
from pubnub_app.pubnub_config import get_pubnub_config

class PubNubPublisher:
    def __init__(self, channel: str):
        self._channel = channel
        self._pubnub = PubNub(get_pubnub_config())

    def publish(self, message: dict) -> bool:
        try:
            envelope = self._pubnub.publish().channel(self._channel).message(message).sync()
            if envelope.status.is_error():
                print(f"[PubNubPublisher] Failed to publish message: {envelope.status.error_data}")
                return False
            else:
                print(f"[PubNubPublisher] Message published to '{self._channel}': {message}")
                return True
        except Exception as e:
            print(f"[PubNubPublisher] Unexpected error during publish: {e}")
            return False
