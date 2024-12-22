import requests
from sensors.led import LEDRing
from sensors.speaker import Speaker
from subscriber import PubNubSubscriber, SettingsListener

# Припустимо, Pi знає свій google_id
GOOGLE_ID = "114379767835747196870"
SERVER_URL = "http://localhost:5000"

def fetch_channel_data(google_id):
    try:
        url = f"{SERVER_URL}/api/get_token?google_id={google_id}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"[fetch_channel_data] Error: {r.status_code} {r.text}")
            return None
    except Exception as e:
        print(f"[fetch_channel_data] Exception: {e}")
        return None

def main():
    channel_info = fetch_channel_data(GOOGLE_ID)
    if not channel_info:
        print("Could not retrieve channel info from server, exiting.")
        return

    channel_name = channel_info["channel_name"]
    channel_token = channel_info["channel_token"]

    led_ring = LEDRing()
    speaker = Speaker()
    listener = SettingsListener(led_ring, speaker)

    subscriber = PubNubSubscriber(channel_name, channel_token)
    subscriber.set_listener(listener)
    subscriber.start_listening()

    try:
        print("PubNub Subscriber is running. Press Ctrl+C to stop.")
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopping PubNub Subscriber...")
        subscriber.stop_listening()

if __name__ == "__main__":
    main()
