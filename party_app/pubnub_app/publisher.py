# pubnub_app/publisher.py
from pubnub_app.pubnub_client import PubNubClient
import logging

logger = logging.getLogger(__name__)

class PubNubPublisher:
    def __init__(self, channel: str):
        self._channel = channel
        self._pubnub_client = PubNubClient()

    def publish(self, message: dict) -> bool:
        try:
            result = self._pubnub_client.publish_message(self._channel, message)
            return result
        except Exception as e:
            logger.error(f"[PubNubPublisher] Unexpected error during publish: {e}")
            return False
