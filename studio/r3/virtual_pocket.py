"""Independent Pocket Link endpoint. Use --pty for an externally addressable serial fixture."""
import argparse
import io
import os
from pathlib import Path
import pty
import select
import sys
import time
import tty

STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDIO))
from engine import ACTIONS, FPS, Game, GameError
from r3.panels import PANELS, render_panel
from r3.pocket_bridge import PocketBridge


class VirtualBoard:
    def __init__(self, size):
        self.size = size
        sample = STUDIO / "samples/falling-blocks/main.py"
        self.load(sample.read_text(encoding="utf-8"), "Stackfall")
        self.control("play")

    def identity(self):
        return {"name": "Virtual Pocket", "model": "Desktop reference peer", "firmware": "Pocket Link v1",
                "width": self.size, "height": self.size, "logical_width": 160, "logical_height": 160,
                "capabilities": ["mirror", "control", "input", "load"]}

    def load(self, source, title):
        if not isinstance(title, str) or not 0 < len(title) <= 80:
            raise ValueError("Invalid cartridge title")
        fresh = Game(source, seed=1)
        self.game, self.source, self.title = fresh, source, title
        self.held = set()
        self.running = False
        self.last = time.monotonic()
        self.fault = None
        self.cached = None

    def control(self, cmd):
        if cmd == "reset":
            self.load(self.source, self.title)
        elif cmd == "pause":
            self.running = False
            self.held.clear()
        elif cmd == "play":
            if self.fault:
                raise ValueError("Reset after the runtime error.")
            self.last = time.monotonic()
            self.running = True

    def buttons(self, keys):
        if not isinstance(keys, list) or len(keys) > len(ACTIONS) or not set(keys) <= ACTIONS:
            raise ValueError("Unknown key")
        self.held = set(keys)

    def _step(self, keys):
        try:
            self.game.step(keys)
        except GameError as exc:
            self.running = False
            self.fault = str(exc)[:145]
            raise

    def tap(self, key):
        if key not in ACTIONS:
            raise ValueError("Unknown key")
        self._step(self.held | {key})
        self._step(self.held)

    def advance(self):
        if self.running:
            now = time.monotonic()
            frames = min(4, int((now - self.last)*FPS))
            if frames:
                self.last = max(self.last + frames/FPS, now - 1/FPS)
                try:
                    for _ in range(frames):
                        self._step(self.held)
                except GameError:
                    pass  # A stopped game and the error text are available in its next frame.

    def frame(self):
        state = self.game.inspect()
        if self.cached is None or self.cached[0] != state["tick"]:
            # The peer draws the entire panel. Studio displays only this received image.
            panel = render_panel(self.game.image(), self.size)
            out = io.BytesIO()
            panel.save(out, format="PNG", compress_level=1)
            self.cached = (state["tick"], out.getvalue())
        status = self.fault or str(state["status"]) or "Ready"
        telemetry = {"tick": state["tick"], "running": self.running, "title": self.title,
                     "score": state["score"], "keys": state["keys"], "status": status}
        return telemetry, "png", self.cached[1]


def run(reader, writer, size):
    board = VirtualBoard(size)
    bridge = PocketBridge(board)
    while True:
        board.advance()
        ready, _, _ = select.select([reader], [], [], 1/FPS if board.running else None)
        if ready and not bridge.serve_one(reader, writer):
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    m = parser.add_mutually_exclusive_group(required=True)
    m.add_argument("--stdio", action="store_true")
    m.add_argument("--pty", action="store_true", help="print a virtual serial port path and serve one session")
    parser.add_argument("--size", type=int, choices=PANELS, default=480)
    args = parser.parse_args()
    try:
        if args.pty:
            master, slave = pty.openpty()
            tty.setraw(slave)
            print(os.ttyname(slave), flush=True)
            # Keep slave open until the client actually connects (first command).
            reader = os.fdopen(master, "rb", buffering=0)
            writer = os.fdopen(os.dup(master), "wb", buffering=0)
            try:
                select.select([reader], [], [])
                os.close(slave)
                run(reader, writer, args.size)
            finally:
                reader.close()
                writer.close()
        else:
            with os.fdopen(os.dup(0), "rb", buffering=0) as reader, os.fdopen(os.dup(1), "wb", buffering=0) as writer:
                run(reader, writer, args.size)
    except (OSError, ValueError):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
