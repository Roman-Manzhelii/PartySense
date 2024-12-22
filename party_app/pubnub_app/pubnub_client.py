from pubnub.pubnub import PubNub
from pubnub.models.consumer.v3.channel import Channel
from pubnub.exceptions import PubNubException
import jwt
from datetime import datetime, timezone
from pubnub_app.pubnub_config import get_pubnub_config

class PubNubClient:
    def __init__(self):
        self.config = get_pubnub_config()
        self.pubnub = PubNub(self.config)

    def generate_token(self, channels, ttl=60):
        try:
            channels_list = [Channel.id(channel).read().write() for channel in channels]
            envelope = self.pubnub.grant_token().channels(channels_list).ttl(ttl).sync()
            return envelope.result.token
        except PubNubException as e:
            print(f"Error generating token: {e}")
            return None

    def is_token_expired(self, token):
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")
            if not exp:
                return True
            now_utc = datetime.now(timezone.utc).timestamp()
            return exp < now_utc
        except Exception as e:
            print(f"Error decoding token: {e}")
            return True

    def publish_message(self, channel, message):
        try:
            envelope = self.pubnub.publish().channel(channel).message(message).sync()
            if envelope.status.is_error():
                print(f"Error publishing to {channel}: {envelope.status.error_data}")
            else:
                print(f"Message published to {channel}: {message}")
        except PubNubException as e:
            print(f"Error publishing message: {e}")
