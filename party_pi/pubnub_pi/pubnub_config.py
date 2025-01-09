import os
from dotenv import load_dotenv
from pubnub.pnconfiguration import PNConfiguration

load_dotenv()

def get_pubnub_config():
    config = PNConfiguration()
    config.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY")
    config.publish_key = os.getenv("PUBNUB_PUBLISH_KEY")
    config.secret_key = os.getenv("PUBNUB_SECRET_KEY")
    config.uuid = os.getenv("PUBNUB_UUID", "RaspberryPi")
    config.ssl = True
    return config
