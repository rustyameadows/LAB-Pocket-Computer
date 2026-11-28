import json
from pathlib import Path
import sys
import unittest

from PIL import Image

STUDIO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO))
from engine import Game
from r3.playtest_tools import InputTape, MAX_TICKS, render_panel


class PanelAndReplayTests(unittest.TestCase):
    def test_native_pixel_distribution(self):
        canvas = Image.new("L", (160, 160))
        ramp = bytes(range(160)) * 160
        canvas.frombytes(ramp)
        for size, widths in ((480, {3}), (720, {4, 5})):
            frame = render_panel(canvas, size)
            self.assertEqual(frame.size, (size, size))
            row = list(frame.crop((0, 0, size, 1)).tobytes())
            self.assertEqual(row, sorted(row))
            self.assertEqual(set(row), set(range(160)))
            self.assertEqual({row.count(shade) for shade in range(160)}, widths)
        with self.assertRaises(ValueError):
            render_panel(canvas, 640)
        with self.assertRaises(ValueError):
            render_panel(Image.new("RGB", (32, 32)), 480)

    def test_record_export_replay_matches_state_and_pixels(self):
        source = (STUDIO / "samples/falling-blocks/main.py").read_text()
        active = Game(source, seed=17)
        tape = InputTape(source, seed=17)
        for keys in (["b"], [], ["key06"], ["left"], [], ["a"], [], ["right"], [], ["key09"]):
            active.step(keys)
            tape.append(keys)
        recorded = InputTape.loads(source, tape.dumps())
        self.assertEqual(recorded.length, 10)
        replay = Game(source, seed=recorded.seed)
        for keys in recorded.frames():
            replay.step(keys)
        self.assertEqual(active.inspect(), replay.inspect())
        self.assertEqual(active.image().tobytes(), replay.image().tobytes())

    def test_reject_mismatched_source_and_unbounded_input(self):
        tape = InputTape("game")
        tape.append(["up"])
        with self.assertRaises(ValueError):
            InputTape.loads("other", tape.dumps())
        valid = json.loads(tape.dumps())
        for runs in ([], [[1, MAX_TICKS + 1]], [[1 << 20, 1]], [[2, True]], [[1, 0]], [1]):
            with self.subTest(runs=runs), self.assertRaises(ValueError):
                InputTape.loads("game", json.dumps(dict(valid, runs=runs)))
        tape = InputTape.loads("game", json.dumps(dict(valid, runs=[[0, MAX_TICKS]])))
        with self.assertRaises(ValueError):
            tape.append([])


if __name__ == "__main__":
    unittest.main()
