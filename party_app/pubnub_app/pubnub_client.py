from pubnub_app.pubnub_config import get_pubnub_config
from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from datetime import datetime, timezone, timedelta
from pubnub.models.consumer.v3.channel import Channel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PubNubClient:
    def __init__(self):
        self.config = get_pubnub_config()
        self.pubnub = PubNub(self.config)
        logger.info("PubNubClient initialized.")

    def generate_token(self, channels, ttl=60):
        try:
            channels_list = [Channel(channel).read().write() for channel in channels]
            envelope = self.pubnub.grant_token().channels(channels_list).ttl(ttl).sync()
            token = envelope.result.token
            expiration_time = datetime.now(timezone.utc) + timedelta(seconds=ttl)

            for c in channels_list:
                logger.info(f"Channel object: {c}, c.id: {c.id}, type(c.id): {type(c.id)}")

            channel_ids = [c.id for c in channels_list]
            logger.info(f"Token generated for channels: {channel_ids}")
            return token, expiration_time
        except PubNubException as e:
            logger.error(f"PubNubException during token generation: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error during token generation: {e}")
            return None, None

    def is_token_expired(self, expiration_time):
        now_utc = datetime.now(timezone.utc)
        if expiration_time.tzinfo is None:
            expiration_time = expiration_time.replace(tzinfo=timezone.utc)
            logger.debug("Converted expiration_time to offset-aware with UTC timezone.")
        else:
            logger.debug("expiration_time is already offset-aware.")

        is_expired = now_utc >= expiration_time
        logger.debug(f"Comparing now_utc: {now_utc} >= expiration_time: {expiration_time} = {is_expired}")
        return is_expired

    def publish_message(self, channel, message):
        try:
            envelope = self.pubnub.publish().channel(channel).message(message).sync()
            if envelope.status.is_error():
                logger.error(f"Error publishing to {channel}: {envelope.status.error_data}")
                return False
            return True
        except PubNubException as e:
            logger.error(f"PubNubException during publish: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during publish: {e}")
            return False

    def subscribe_to_status_channel(self, user_id, callback):
        try:
            channel = f"user_{user_id}_status"
            self.pubnub.add_listener(StatusListener(callback))
            self.pubnub.subscribe().channels([channel]).execute()
            logger.info(f"Subscribed to status channel: {channel}")
        except Exception as e:
            logger.error(f"Error subscribing to status channel {channel}: {e}")

class StatusListener:
    def __init__(self, callback):
        self.callback = callback

    def status(self, pubnub, status):
        pass  # Якщо необхідно, обробляти статус-події PubNub

    def message(self, pubnub, message):
        self.callback(message.message)
