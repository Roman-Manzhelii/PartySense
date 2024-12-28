import os
import time
import threading

from pymongo import MongoClient
from dotenv import load_dotenv

from sensors.led import LEDRing
from sensors.speaker import Speaker
from sensors.pir import PIRSensor
from player.player import Player
from pubnub_pi.listeners import CommandListener
from pubnub_pi.subscriber import PubNubSubscriber
from pubnub_pi.status_publisher import StatusPublisher

load_dotenv()

# Зчитуємо змінні середовища
GOOGLE_ID = os.getenv("GOOGLE_ID")  # "114379767835747196870"
MONGO_URI = os.getenv("MONGO_URI")

def fetch_channel_data_from_db(google_id):
    try:
        client = MongoClient(MONGO_URI)
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

    # Створюємо Listener для команд
    command_listener = CommandListener(player, led_ring)

    # Створюємо і запускаємо PubNub Subscriber для команд
    subscriber = PubNubSubscriber(channel_name_commands, command_listener)
    subscriber.start_listening()

    # Створюємо і запускаємо Status Publisher для статусу
    status_publisher = StatusPublisher(channel_name_status, player, GOOGLE_ID)
    status_publisher.start()

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
        status_publisher.stop()
        pir_sensor.cleanup()
        led_ring.turn_off()
        print("[main] Shutdown complete.")

if __name__ == "__main__":
    main()
