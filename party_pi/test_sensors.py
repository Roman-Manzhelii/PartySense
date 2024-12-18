from sensors.pir import PIRSensor
from sensors.led import LEDRing
import time

if __name__ == "__main__":
    pir = PIRSensor()
    led = LEDRing()

    print("Starting sensor test. Press Ctrl+C to stop.")
    try:
        while True:
            if pir.detect_motion():
                print("Motion detected!")
                led.set_color((0, 255, 0))  # Green
            else:
                led.turn_off()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Test stopped.")
