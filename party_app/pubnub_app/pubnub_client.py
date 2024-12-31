# pubnub_client.py
import logging
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.models.consumer.v3.channel import Channel
from datetime import datetime, timezone, timedelta
from pubnub_app.pubnub_config import get_pubnub_config

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)  # Змінили на DEBUG для детальнішого логування
logger = logging.getLogger(__name__)

class PubNubClient:
    def __init__(self):
        self.config = get_pubnub_config()
        self.pubnub = PubNub(self.config)
        logger.info("PubNubClient initialized with configuration:")
        logger.debug(f"Subscribe Key: {self.config.subscribe_key}")
        logger.debug(f"Publish Key: {self.config.publish_key}")
        logger.debug(f"Secret Key: {self.config.secret_key}")
        logger.debug(f"UUID: {self.config.uuid}")

    def generate_token(self, channels, ttl=3600):
        try:
            channels_list = [Channel(ch).read().write() for ch in channels]
            logger.debug(f"Generating token for channels: {[c.id for c in channels_list]} with TTL: {ttl} seconds")
            envelope = self.pubnub.access_manager().grant_token().channels(channels_list).ttl(ttl).sync()
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

    def subscribe_to_status_channel(self, user_id, callback):
        channel = f"user_{user_id}_status"
        logger.info(f"Attempting to subscribe to status channel: {channel}")
        try:
            self.pubnub.add_listener(StatusListener(callback))
            self.pubnub.subscribe().channels([channel]).execute()
            logger.info(f"Successfully subscribed to status channel: {channel}")
        except PubNubException as e:
            logger.error(f"PubNubException during subscription to {channel}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during subscription to {channel}: {e}")

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

    def presence(self, pubnub, presence):
        # Необхідно реалізувати, якщо потрібно
        pass
