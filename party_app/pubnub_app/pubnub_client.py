# pubnub_client.py
import logging
from pubnub.pubnub import PubNub
from pubnub.callbacks import SubscribeCallback
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.models.consumer.v3.channel import Channel
from datetime import datetime, timezone, timedelta
from pubnub_app.pubnub_config import get_pubnub_config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PubNubClient:
    def __init__(self, message_callback):
        self.config = get_pubnub_config()
        self.pubnub = PubNub(self.config)
        self.message_callback = message_callback
        self.listener = StatusListener(self.message_callback)
        self.pubnub.add_listener(self.listener)

    def generate_token(self, channels, ttl=3600):
        try:
            channels_list = [Channel(ch).read().write() for ch in channels]
            logger.debug(f"Generating token for channels: {[c.id for c in channels_list]} with TTL: {ttl} seconds")
            envelope = self.pubnub.grant_token().channels(channels_list).ttl(ttl).sync()
            token = envelope.result.token
            expiration_time = datetime.now(timezone.utc) + timedelta(seconds=ttl)

            for c in channels_list:
                logger.info(f"Channel object: {c}, c.id: {c.id}, type(c.id): {type(c.id)}")

            channel_ids = [c.id for c in channels_list]
            logger.info(f"Token generated for channels: {channel_ids}")
            logger.debug(f"Token: {token}")
            logger.debug(f"Expiration Time: {expiration_time.isoformat()}")
            return token, expiration_time
        except PubNubException as e:
            logger.error(f"PubNubException during token generation: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error during token generation: {e}")
            return None, None

    def is_token_expired(self, expiration_time):
        now_utc = datetime.now(timezone.utc)
        logger.debug(f"Current UTC Time: {now_utc.isoformat()}")
        if expiration_time.tzinfo is None:
            expiration_time = expiration_time.replace(tzinfo=timezone.utc)
            logger.debug("Converted expiration_time to offset-aware with UTC timezone.")

        is_expired = now_utc >= expiration_time
        logger.debug(f"Comparing now_utc: {now_utc.isoformat()} >= expiration_time: {expiration_time.isoformat()} = {is_expired}")
        return is_expired

    def publish_message(self, channel, message):
        logger.debug(f"Attempting to publish message to channel: {channel} | Message: {message}")
        try:
            envelope = self.pubnub.publish().channel(channel).message(message).sync()
            if envelope.status.is_error():
                logger.error(f"Error publishing to {channel}: {envelope.status.error_data}")
                return False
            logger.info(f"Successfully published message to {channel}")
            return True
        except PubNubException as e:
            logger.error(f"PubNubException during publish to {channel}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during publish to {channel}: {e}")
            return False

    def subscribe_to_channels(self, channels):
        channel_names = [f"user_{user_id}_status" for user_id in channels]
        logger.info(f"Subscribing to channels: {channel_names}")
        try:
            self.pubnub.subscribe().channels(channel_names).execute()
            logger.info(f"Successfully subscribed to channels: {channel_names}")
        except PubNubException as e:
            logger.error(f"PubNubException during subscription to channels {channel_names}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during subscription to channels {channel_names}: {e}")

class StatusListener(SubscribeCallback):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        logger.debug("StatusListener initialized.")

    def status(self, pubnub, status):
        logger.debug(f"Status event received: {status.category}")
        if status.is_error():
            logger.error(f"Status error: {status.error_data}")

    def message(self, pubnub, message: PNMessageResult):
        logger.info(f"Message received on channel {message.channel}: {message.message}")
        self.callback(message.message)
