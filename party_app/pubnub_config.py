# pubnub_config.py
import os
import uuid
from dotenv import load_dotenv
from pubnub.pnconfiguration import PNConfiguration

load_dotenv()

def get_pubnub_config():
    config = PNConfiguration()
    config.publish_key = os.getenv("PUBNUB_PUBLISH_KEY")
    config.subscribe_key = os.getenv("PUBNUB_SUBSCRIBE_KEY")
    config.secret_key = os.getenv("PUBNUB_SECRET_KEY")
    config.ssl = True
    custom_uuid = os.getenv("PUBNUB_UUID", "").strip()
    if custom_uuid:
        config.uuid = custom_uuid
    else:
        config.uuid = f"PartySense-{uuid.uuid4()}"
    
    return config
