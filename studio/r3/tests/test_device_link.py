"""Host/peer integration over both local sockets and real Linux termios PTYs."""
import os
from pathlib import Path
import pty
import struct
import subprocess
import sys
import tempfile
import termios
import threading
import time
import unittest

from PIL import Image

R3 = Path(__file__).resolve().parents[1]
STUDIO = R3.parent
sys.path.insert(0, str(R3))
sys.path.insert(0, str(STUDIO))
from device_link import DeviceError, DeviceLink, Endpoint, discover
from engine import Game
from pocket_bridge import PocketBridge
from virtual_pocket import VirtualBoard


class DeviceLinkTests(unittest.TestCase):
    def test_discovery_prefers_stable_names_without_opening_ports(self):
        with tempfile.TemporaryDirectory() as d:
            dev = Path(d)
            (dev/"serial/by-id").mkdir(parents=True)
            port = dev/"ttyACM0"
            port.write_bytes(b"unchanged")
            stable = dev/"serial/by-id/usb-MyPocket"
            stable.symlink_to(port)
            (dev/"ttyUSB1").touch()
            found = discover(dev)
            self.assertEqual([e.id for e in found], ["virtual:480", "virtual:720", str(stable), str(dev/"ttyUSB1")])
            self.assertEqual(port.read_bytes(), b"unchanged")

    def test_peer_renders_both_physical_profiles_and_inputs(self):
        source = (STUDIO/"samples/falling-blocks/main.py").read_text()
        for endpoint in discover()[:2]:
            with self.subTest(endpoint=endpoint.id):
                link = DeviceLink.open(endpoint)
                self.addCleanup(link.close)
                link.control("reset")
                first = link.frame()
                n = int(endpoint.id.split(":")[1])
                self.assertEqual(first.image.size, (n, n))
                self.assertEqual((first.tick, first.running, first.score), (0, False, 0))
                expected = Game(source, seed=1)
                self.assertEqual(first.image.tobytes(), expected.image().resize((n,n), Image.Resampling.NEAREST).tobytes())
                link.tap("b")
                expected.step(["b"])
                expected.step([])
                second = link.frame()
                self.assertEqual((second.tick, second.score), (2, 136))
                self.assertEqual(second.image.tobytes(), expected.image().resize((n,n), Image.Resampling.NEAREST).tobytes())
                self.assertNotEqual(first.image.tobytes(), second.image.tobytes())
                link.close()
                link.close()
                with self.assertRaises(DeviceError):
                    link.frame()

    def test_load_play_pause_and_independent_sessions(self):
        ep = discover()[0]
        first, other = DeviceLink.open(ep), DeviceLink.open(ep)
        self.addCleanup(first.close)
        self.addCleanup(other.close)
        source = """def init():
    state['score'] = 10
def update():
    if held('a'):
        state['score'] += 1
def draw():
    clear('#103352')
"""
        first.load(source, "Blue")
        with self.assertRaises(DeviceError):
            first.load("def broken(", "Invalid")
        self.assertEqual(first.frame().title, "Blue")
        self.assertEqual(other.frame().title, "Stackfall")
        first.buttons(["a"])
        first.control("play")
        deadline = time.monotonic() + 2
        while first.frame().score < 12 and time.monotonic() < deadline:
            time.sleep(.025)
        first.control("pause")
        paused = first.frame()
        self.assertGreaterEqual(paused.score, 12)
        time.sleep(.06)
        self.assertEqual(first.frame().tick, paused.tick)
        first.control("reset")
        self.assertEqual((first.frame().score, first.frame().tick), (10, 0))

    def test_serial_tty_handshake_and_exclusive_port(self):
        with subprocess.Popen([sys.executable, "-B", str(R3/"virtual_pocket.py"), "--pty", "--size", "720"],
                              stdout=subprocess.PIPE, text=True) as peer:
            try:
                path = peer.stdout.readline().strip()
                self.assertTrue(path.startswith("/dev/pts/"))
                endpoint = Endpoint(path, "PTY fixture", "usb", path)
                link = DeviceLink.open(endpoint)
                try:
                    self.assertEqual(link.info["width"], 720)
                    with self.assertRaises(DeviceError):
                        DeviceLink.open(endpoint)
                    link.control("reset")
                    link.tap("b")
                    self.assertEqual(link.frame().score, 136)
                finally:
                    link.close()
            finally:
                peer.terminate()
                peer.wait(2)
                peer.stdout.close()

    def test_silent_serial_timeout_restores_tty_settings(self):
        master, slave = pty.openpty()
        try:
            path = os.ttyname(slave)
            old = termios.tcgetattr(slave)
            with self.assertRaisesRegex(DeviceError, "timed out"):
                DeviceLink.open(Endpoint(path, "Silent PTY", "usb", path), timeout=.08)
            self.assertEqual(termios.tcgetattr(slave), old)
        finally:
            os.close(master)
            os.close(slave)

    def test_board_bridge_rgb565_encodings_and_bad_frames(self):
        class Panel(VirtualBoard):
            def frame(self):
                meta = {"tick": 17, "title": "Panel probe", "running": True}
                return meta, self.encoding, self.payload
        n = 480
        red = b"\x00\xf8"
        blue = b"\x1f\x00"
        pixels = n*n
        board = Panel(n)
        raw = red*(pixels//2) + blue*(pixels//2)
        runs = b"".join(struct.pack("<H2s", count, color) for color in (red,blue)
                        for count in (65535, pixels//2-65535))
        for mode, payload, valid in (("rgb565le", raw, True), ("rle565le", runs, True),
                                     ("rle565le", b"\0\0\0\0", False), ("rgb565le", b"", False)):
            board.encoding, board.payload = mode, payload
            master, slave = pty.openpty()
            bridge = PocketBridge(board)
            def serve():
                with os.fdopen(os.dup(master), "r+b", buffering=0) as port:
                    for _ in range(2):
                        bridge.serve_one(port, port)
            thread = threading.Thread(target=serve)
            thread.start()
            path = os.ttyname(slave)
            link = DeviceLink.open(Endpoint(path, "Test panel", "usb", path))
            try:
                if valid:
                    frame = link.frame()
                    self.assertEqual(frame.image.getpixel((0,0)), (255,0,0))
                    self.assertEqual(frame.image.getpixel((0,n-1)), (0,0,255))
                else:
                    with self.assertRaises(DeviceError):
                        link.frame()
            finally:
                link.close()
                thread.join(2)
                os.close(master)
                os.close(slave)
                self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
