import asyncio
from sensors.pir import PIRSensor, monitor_pir
from sensors.led import LEDRing
from sensors.speaker import Speaker

NO_MOTION_TIMEOUT = 5

pir_sensor = PIRSensor()
led_ring = LEDRing()
speaker = Speaker()

is_audio_playing = False

def on_motion_detected():
    global is_audio_playing
    print("Motion detected: turn on the lights and play the sound!")
    led_ring.show_motion_active()
    if not is_audio_playing:
        is_audio_playing = True
        asyncio.run(speaker.play_audio("welcome_message"))

def on_no_motion_detected():
    global is_audio_playing
    print("No movement: turn off the lights.")
    led_ring.turn_off()
    is_audio_playing = False

def main():
    try:
        print("Expecting motion from the PIR sensor...")
        monitor_pir(
            pir_sensor=pir_sensor,
            callback_on_motion=on_motion_detected,
            callback_on_no_motion=on_no_motion_detected,
            no_motion_timeout=NO_MOTION_TIMEOUT
        )
    except KeyboardInterrupt:
        print("Ending program...")
    finally:
        print("Releasing GPIO resources...")
        pir_sensor.cleanup()
        led_ring.turn_off()

if __name__ == "__main__":
    main()
