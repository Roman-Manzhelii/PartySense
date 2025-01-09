# main.py

import time

from pubnub.pubnub import PubNub
from pubnub_pi.pubnub_config import get_pubnub_config
from pubnub_pi.listeners import CommandListener

from player.youtube_player import YouTubePlayer
from player.player import Player


def main():
    # Ініціалізація PubNub
    pnconfig = get_pubnub_config()
    pubnub = PubNub(pnconfig)

    # Створюємо інстанси Player та YouTubePlayer
    player = Player()
    youtube_player = YouTubePlayer()

    led_ring = None

    # Створюємо CommandListener
    command_listener = CommandListener(player, youtube_player, led_ring)

    # Додаємо listener до PubNub
    pubnub.add_listener(command_listener)

    # Підписуємося на канал команд (змініть назву на ваш)
    command_channel = "user_114379767835747196870_commands"
    print(f"[main] Subscribing to '{command_channel}'...")
    pubnub.subscribe().channels(command_channel).execute()

    # Запускаємо фоновий цикл Player (для імітації збільшення position)
    player.start_background()

    try:
        print("[main] Running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[main] Exiting...")
    finally:
        # Зупиняємо фоновий цикл
        player.stop_background()
        # Відписуємося від каналу
        pubnub.unsubscribe().channels(command_channel).execute()
        # Зупиняємо YouTubePlayer
        youtube_player.stop()
        print("[main] Shutdown complete.")

if __name__ == "__main__":
    main()
