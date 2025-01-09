from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from pubnub_pi.pubnub_config import get_pubnub_config

class PubNubPublisher:
    """
    Клас для публікації повідомлень у PubNub-канали.
    """
    def __init__(self, channel: str):
        self.channel = channel
        self.pubnub = PubNub(get_pubnub_config())

    def publish_message(self, message: dict):
        try:
            envelope = self.pubnub.publish().channel(self.channel).message(message).sync()
            if envelope.status.is_error():
                print(f"[PubNubPublisher] Publish error: {envelope.status.error_data}")
            else:
                print(f"[PubNubPublisher] Published message to {self.channel}: {message}")
        except PubNubException as e:
            print(f"[PubNubPublisher] Publish exception: {e}")
