"""LAB v0 MicroPython player for trusted, unpacked Studio cartridges.

PocketPlayer renders a 160x160 RGB565 framebuffer. The board firmware supplies
the physical input map, display transport and LED output. No pins are assumed.
Copy this file, pocket_keys.py and pixel_font.py into the MicroPython module path.
"""
from framebuf import FrameBuffer, RGB565
from pixel_font import draw_text
from pocket_keys import expand_buttons


class PocketPlayer:
    def __init__(self, source, seed=1):
        self.pixels = bytearray(160 * 160 * 2)
        self.screen = FrameBuffer(self.pixels, 160, 160, RGB565)
        self.color_cache = {}
        self.lights = {}
        self.buttons = set()
        self.just_pressed = set()
        self.random_state = seed & 0xffffffff
        self.tick = 0
        self.state = {}
        self.namespace = {
            "state": self.state, "tick": 0,
            "held": lambda key: key in self.buttons,
            "pressed": lambda key: key in self.just_pressed,
            "rand": self.random, "led": self.led,
            "clear": self.clear, "rect": self.rect, "line": self.line,
            "pixel": self.pixel, "text": self.text,
        }
        self.clear("#101524")
        # Device-side execution is for the owner's trusted source.
        exec(source, self.namespace)
        self.namespace["init"]()
        self.namespace["draw"]()

    def color(self, value):
        cached = self.color_cache.get(value)
        if cached is not None:
            return cached
        rgb = value[1:]
        if len(rgb) == 3:
            rgb = "".join(ch + ch for ch in rgb)
        color = int(rgb, 16)
        packed = ((color >> 8) & 0xf800) | ((color >> 5) & 0x07e0) | ((color >> 3) & 0x001f)
        if len(self.color_cache) < 256:
            self.color_cache[value] = packed
        return packed

    def random(self, low, high):
        self.random_state = (1664525 * self.random_state + 1013904223) & 0xffffffff
        low, high = int(low), int(high)
        return low + self.random_state % (high - low + 1)

    def led(self, key, color):
        name = "key%02d" % key if isinstance(key, int) else key
        self.lights[name] = color

    def clear(self, color):
        self.screen.fill(self.color(color))

    def pixel(self, x, y, color):
        self.screen.pixel(int(x), int(y), self.color(color))

    def rect(self, x, y, width, height, color):
        if width > 0 and height > 0:
            self.screen.fill_rect(int(x), int(y), int(width), int(height), self.color(color))

    def line(self, x1, y1, x2, y2, color):
        self.screen.line(int(x1), int(y1), int(x2), int(y2), self.color(color))

    def text(self, x, y, value, color, scale=1):
        draw_text(self.screen.pixel, int(x), int(y), value, self.color(color), int(scale))

    def step(self, buttons=()):
        current = expand_buttons(buttons)
        self.just_pressed = current - self.buttons
        self.buttons = current
        self.tick += 1
        self.namespace["tick"] = self.tick
        self.namespace["update"]()
        self.namespace["draw"]()
