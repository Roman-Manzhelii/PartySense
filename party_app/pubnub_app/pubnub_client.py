# pubnub_app/pubnub_client.py
import os
from dotenv import load_dotenv
from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from datetime import datetime, timezone, timedelta
from pubnub.models.consumer.v3.channel import Channel
from pubnub_app.pubnub_config import get_pubnub_config
import logging

load_dotenv()

# Налаштування логування
logging.basicConfig(level=logging.INFO)  # Рівень логування встановлено на INFO
logger = logging.getLogger(__name__)

class PubNubClient:
    def __init__(self):
        self.config = get_pubnub_config()
        self.pubnub = PubNub(self.config)
        logger.info("PubNubClient initialized.")

    def generate_token(self, channels, ttl=60):
        try:
            # Правильне створення об'єктів каналів
            channels_list = [Channel(channel).read().write() for channel in channels]
            envelope = self.pubnub.grant_token().channels(channels_list).ttl(ttl).sync()
            token = envelope.result.token
            expiration_time = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            
            # Додаткове логування для перевірки типу 'c.id'
            for c in channels_list:
                logger.info(f"Channel object: {c}, c.id: {c.id}, type(c.id): {type(c.id)}")
            
            # Переконайтеся, що 'id' є атрибутом, а не методом
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
        is_expired = now_utc >= expiration_time
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
