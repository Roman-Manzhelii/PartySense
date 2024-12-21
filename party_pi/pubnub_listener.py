from sensors.led import LEDRing
from sensors.speaker import Speaker
from subscriber import PubNubSubscriber, SettingsListener

def main():
    led_ring = LEDRing()
    speaker = Speaker()
    listener = SettingsListener(led_ring, speaker)

    subscriber = PubNubSubscriber(channel="settings_channel", listener=listener)
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
