import os
import time
import threading
from pathlib import Path 

from pymongo import MongoClient
from dotenv import load_dotenv

from sensors.led import LEDRing
from sensors.speaker import Speaker
from sensors.pir import PIRSensor
from player.player import Player
from pubnub_pi.listeners import CommandListener
from pubnub_pi.subscriber import PubNubSubscriber
from pubnub_pi.publisher import PubNubPublisher

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


GOOGLE_ID = os.getenv("GOOGLE_ID")
MONGODB_URI = os.getenv("MONGODB_URI")

def fetch_channel_data_from_db(google_id):
    try:
        client = MongoClient(MONGODB_URI)
        db = client["party_sense_db"]
        user = db["users"].find_one({"google_id": google_id})

        if not user:
            print(f"[main] User with Google ID {google_id} not found in MongoDB.")
            return None

        return {
            "channel_name_commands": user.get("channel_name_commands"),
            "channel_token_commands": user.get("channel_token_commands"),
            "channel_name_status": user.get("channel_name_status"),
            "channel_token_status": user.get("channel_token_status"),
            "preferences": user.get("preferences"),
        }
    except Exception as e:
        print(f"[main] Error fetching channel data from MongoDB: {e}")
        return None

def main():
    # Ініціалізуємо компоненти
    led_ring = LEDRing()
    speaker = Speaker()
    pir_sensor = PIRSensor()  # Заглушка, не використовується в даний момент
    player = Player()

    # Отримуємо дані з MongoDB
    channel_data = fetch_channel_data_from_db(GOOGLE_ID)
    if not channel_data:
        print("[main] Failed to retrieve channel data. Exiting.")
        return

    channel_name_commands = channel_data.get("channel_name_commands")
    channel_token_commands = channel_data.get("channel_token_commands")
    channel_name_status = channel_data.get("channel_name_status")
    channel_token_status = channel_data.get("channel_token_status")

    if not all([channel_name_commands, channel_token_commands, channel_name_status, channel_token_status]):
        print("[main] Incomplete channel data retrieved from MongoDB. Exiting.")
        return

    # Створюємо Publisher для статусу
    status_publisher = PubNubPublisher(channel_name_status)

    # Callback для публікації статусу
    def publish_status():
        song_state = player.get_current_state()
        message = {
            "user_id": GOOGLE_ID,
            "current_song": {
                "video_id": song_state.get("video_id", "unknown"),
                "title": song_state.get("title", "Unknown Title"),
                "thumbnail_url": song_state.get("thumbnail_url", ""),
                "duration": song_state.get("duration", 0),
                "position": song_state.get("position", 0),
                "state": song_state.get("state", "paused"),
                "mode": song_state.get("mode", "default"),
                "motion_detected": song_state.get("motion_detected", True),
                "updated_at": song_state.get("updated_at", time.time())
            }
        }
        status_publisher.publish_message(message)

    # Передаємо callback у Player
    player.on_update_callback = publish_status

    # Створюємо Listener для команд
    command_listener = CommandListener(player, led_ring)

    # Створюємо і запускаємо PubNub Subscriber для команд
    subscriber = PubNubSubscriber(channel_name_commands, command_listener)
    subscriber.start_listening()

    # Запускаємо фоновий Player
    player.start_background()

    try:
        print("[main] Raspberry Pi simulation is running. Press Ctrl+C to exit.")
        while True:
            # Тут можна додати додаткову логіку або моніторинг сенсорів
            time.sleep(1)
    except KeyboardInterrupt:
        print("[main] Stopping Raspberry Pi simulation...")
    finally:
        # Зупиняємо всі компоненти
        player.stop_background()
        subscriber.stop_listening()
        pir_sensor.cleanup()
        led_ring.turn_off()
        print("[main] Shutdown complete.")

if __name__ == "__main__":
    main()
