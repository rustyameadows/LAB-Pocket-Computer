"""Deterministic acceptance cases for the desktop runtime and its sample cartridges."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import Game, GameError


def sample(slug):
    return Game((ROOT / "samples" / slug / "main.py").read_text())


def script(update="pass", draw='clear("#123")', init="pass"):
    return (f"def init():\n    {init}\n\ndef update():\n    {update}\n\n"
            f"def draw():\n    {draw}\n")


class EngineTests(unittest.TestCase):
    def test_display_and_physical_button_edges(self):
        g = Game(script('if pressed("key01"):\n        state["score"] += 1',
                        'clear("#123")\n    pixel(0,0,"#fff")', 'state["score"] = 0'))
        self.assertEqual(g.image().getpixel((0,0)), (255,255,255))
        self.assertEqual(g.image().getpixel((1,0)), (17,34,51))
        for buttons in [{"key01"}, {"key01"}, set(), {"key01"}]:
            g.step(buttons)
        self.assertEqual((g.inspect()["tick"], g.inspect()["score"]), (4,2))
        with self.assertRaises(GameError):
            g.step(["unknown"])
        self.assertEqual(g.inspect()["tick"], 4)

    def test_replay_is_deterministic(self):
        inputs = [["a"], ["left"], [], ["b"], [], ["left"], ["down"]]
        g, twin = sample("falling-blocks"), sample("falling-blocks")
        for keys in inputs:
            g.step(keys)
            twin.step(keys)
        self.assertEqual(g.inspect(), twin.inspect())
        self.assertEqual(g.image().tobytes(), twin.image().tobytes())
        json.dumps(g.inspect())

    def test_seven_shapes_and_real_line_clear(self):
        g = sample("falling-blocks")
        seen = [g.inspect()["metrics"]["piece"]]
        g.step(["b"])
        self.assertEqual(g.inspect()["metrics"]["lines"], 1)
        self.assertEqual(g.inspect()["score"], 136)
        self.assertEqual(g.inspect()["metrics"]["locks"], 1)
        # Key-edge semantics distinguish holding a hard drop from seven distinct drops.
        for i in range(6):
            seen.append(g.inspect()["metrics"]["piece"])
            g.step(["b"])
            self.assertEqual(g.inspect()["metrics"]["locks"], i+1)
            g.step([])
            g.step(["b"])
        self.assertEqual(set(seen), set(range(7)))

    def test_top_out_and_restart(self):
        g = sample("falling-blocks")
        for n in range(30):
            g.step(["b"])
            g.step([])
            if g.inspect()["status"] == "Game over":
                break
        self.assertEqual(g.inspect()["status"], "Game over")
        g.step(["start"])
        self.assertEqual(g.inspect()["status"], "Playing")
        self.assertEqual(g.inspect()["score"], 0)
        self.assertEqual(g.inspect()["metrics"]["locks"], 0)

    def test_snake_collection_loss_and_restart(self):
        g = sample("snake")
        for _ in range(70):
            g.step()
        self.assertEqual((g.inspect()["score"], g.inspect()["status"]), (1, "Game over"))
        g.step(["a"])
        self.assertEqual((g.inspect()["score"], g.inspect()["status"]), (0, "Playing"))
        g.step([])
        g.step(["up"])
        for _ in range(7):
            g.step()
        self.assertEqual(g.inspect()["metrics"]["dy"], -1)

    def test_breakout_launch_hit_loss_and_restart(self):
        g = sample("breakout")
        for round_num in range(3):
            g.step(["a"])
            for _ in range(220):
                g.step()
                if g.inspect()["status"] != "Playing":
                    break
            self.assertEqual(g.inspect()["metrics"]["lives"], 2-round_num)
        self.assertGreaterEqual(g.inspect()["score"], 10)
        self.assertEqual(g.inspect()["status"], "Game over")
        g.step(["start"])
        self.assertEqual((g.inspect()["status"], g.inspect()["metrics"]["lives"]), ("Ready",3))

    def test_bounded_interpreter_and_helpful_errors(self):
        with self.assertRaisesRegex(GameError, "main.py:"):
            Game("import os\n" + script())
        with self.assertRaisesRegex(GameError, "unsupported method"):
            Game(script(draw="state.clear()"))
        with self.assertRaisesRegex(GameError, "dictionary unpacking"):
            Game(script(init='state["a"] = {**state}'))
        g = Game(script(update="while True:\n        pass"))
        with self.assertRaisesRegex(GameError, "tick budget exceeded"):
            g.step()
        with self.assertRaisesRegex(GameError, "tick budget exceeded"):
            g.step()

    def test_state_cannot_grow_recursive_containers(self):
        with self.assertRaisesRegex(GameError, "cyclic"):
            Game(script(init='state["alias"] = state'))
        with self.assertRaisesRegex(GameError, "range exceeds"):
            Game(script(init='state["alias"] = range(10000)'))

    def test_cartridge_manifests_and_images(self):
        for folder in (ROOT / "samples").iterdir():
            if not folder.is_dir():
                continue
            manifest = json.loads((folder / "manifest.json").read_text())
            self.assertTrue(manifest["title"] and manifest["controls"])
            frame = sample(folder.name).image()
            self.assertEqual((frame.size, frame.mode), ((160, 160), "RGB"))
            self.assertGreater(len(frame.getcolors(256)), 5)


if __name__ == "__main__":
    unittest.main()
