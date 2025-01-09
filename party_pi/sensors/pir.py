import RPi.GPIO as GPIO
import time

class PIRSensor:
    def __init__(self, pin=11):
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN)

    def is_triggered(self):
        return GPIO.input(self.pin) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup()

def monitor_pir(pir_sensor, callback_on_motion=None, callback_on_no_motion=None, no_motion_timeout=5):
    last_motion_time = time.time()
    motion_detected_last = False

    while True:
        motion = pir_sensor.is_triggered()
        if motion:
            last_motion_time = time.time()
            if not motion_detected_last and callback_on_motion:
                callback_on_motion()
            motion_detected_last = True
        else:
            if motion_detected_last and (time.time() - last_motion_time > no_motion_timeout):
                motion_detected_last = False
                if callback_on_no_motion:
                    callback_on_no_motion()
        time.sleep(0.1)
