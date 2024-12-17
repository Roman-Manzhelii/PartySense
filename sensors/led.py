import time
from rpi_ws281x import PixelStrip, Color

class LEDRing:
    def __init__(self, num_leds=12, pin=18, freq_hz=800000, dma=10, brightness=255, invert=False, channel=0):
        self.num_leds = num_leds
        self.strip = PixelStrip(num_leds, pin, freq_hz, dma, invert, brightness, channel)
        self.strip.begin()
    
    def set_color(self, r, g, b):
        color = Color(r, g, b)
        for i in range(self.num_leds):
            self.strip.setPixelColor(i, color)
        self.strip.show()
    
    def turn_off(self):
        self.set_color(0, 0, 0)
    
    def show_motion_active(self):
        self.set_color(0, 255, 0)
    
    def show_idle(self):
        self.turn_off()
    
    def show_party_mode(self):
        for i in range(3):
            self.set_color(255, 0, 0)
            time.sleep(0.5)
            self.set_color(0, 0, 255)
            time.sleep(0.5)
        self.turn_off()
