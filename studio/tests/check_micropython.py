"""Compare a cartridge's game state and RGB565 image on Studio and Unix MicroPython."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDIO))
from engine import Game

BUTTONS = (("key09",), (), ("right",), (), ("down",), (), ("a",), (), ("left",), ())
TICKS = 40

DEVICE_SCRIPT = """
from pocket_player import PocketPlayer
import json, sys
with open(sys.argv[1]) as f:
    player = PocketPlayer(f.read(), seed=7)
for tick in range(TICKS):
    player.step(BUTTONS[tick % len(BUTTONS)])
with open(sys.argv[2], 'wb') as f:
    f.write(player.pixels)
print(json.dumps([player.tick, player.state.get('score', 0), player.state.get('status', 'running'), player.lights]))
"""


def check(binary, source, tmp):
    game = Game(source.read_text(), seed=7)
    for frame in range(TICKS):
        game.step(BUTTONS[frame % len(BUTTONS)])
    values = game.inspect()
    rgb = game.image().convert("RGB")
    # Canonical little-endian RGB565, the native buffer layout in the Unix test port.
    pixels = bytearray()
    red, green, blue = (band.tobytes() for band in rgb.split())
    for r, g, b in zip(red, green, blue):
        pixels.extend((((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)).to_bytes(2, 'little'))
    device = tmp / "device.py"
    device.write_text(f'TICKS = {TICKS}\nBUTTONS = {BUTTONS!r}\n' + DEVICE_SCRIPT)
    raw = tmp / "frame.rgb565"
    p = subprocess.run([binary, device, source, raw], check=True, capture_output=True,
                       text=True, env={**os.environ, 'MICROPYPATH': str(STUDIO)}, timeout=20)
    observed = json.loads(p.stdout)
    expected = [values['tick'], values['score'], values['status'], values['keys']]
    if observed != expected:
        raise RuntimeError(f'{source}: desktop {expected}, MicroPython {observed}')
    if pixels != raw.read_bytes():
        raise RuntimeError(f'{source}: framebuffer mismatch')
    print(f'{source.parent.name}: {TICKS} ticks, score {values["score"]}, matching frame {hashlib.sha256(pixels).hexdigest()[:12]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('micropython', help='Unix MicroPython executable with framebuf and json')
    parser.add_argument('sources', nargs='*', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        for source in args.sources or sorted((STUDIO / 'samples').glob('*/main.py')):
            check(args.micropython, source.resolve(), Path(tmp))


if __name__ == "__main__":
    main()
