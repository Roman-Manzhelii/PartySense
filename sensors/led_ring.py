class LEDRing:
    def __init__(self):
        self.current_color = (0, 0, 0)

    def set_color(self, color_tuple):
        self.current_color = color_tuple
        print(f"LED Ring color set to: {self.current_color}")

    def turn_off(self):
        self.set_color((0, 0, 0))
