"""Real stdio protocol plus two-client transaction and cartridge checks."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from PIL import Image

STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDIO))
from studio_store import RevisionConflict, Store

SOURCE = '''def init():
    state["score"] = 0

def update():
    if held("a"):
        state["score"] = state["score"] + 1

def draw():
    clear("#182d29")
    rect(10, 10, 10 + state["score"], 6, "#ff8844")
'''


class BridgeTests(unittest.TestCase):
    def test_concurrent_clients_and_durable_export(self):
        with tempfile.TemporaryDirectory() as home:
            with ThreadPoolExecutor(max_workers=4) as pool:
                clients = list(pool.map(lambda _: Store(home), range(4)))
            a, b, *_ = clients
            self.assertEqual(len(a.list_projects()), 3)
            item = a.create_project("Moth at the Lamp", "snake")
            self.assertEqual(b.get_active(), item["id"])
            before = b.get_project(item["id"])
            saved = a.update_project(item["id"], SOURCE, expected_revision=1)
            with self.assertRaises(RevisionConflict):
                b.update_project(item["id"], before["source"], expected_revision=1)
            with self.assertRaises(ValueError):
                b.update_project(item["id"], "def broken(", expected_revision=2)
            self.assertEqual(Store(home).get_project(item["id"]), saved)
            duplicate = b.duplicate_project(item["id"], "Lamp Remix")
            self.assertEqual(duplicate["source"], SOURCE)
            self.assertEqual(b.get_active(), duplicate["id"])
            archive = b.export_project(item["id"])
            self.assertEqual(archive.read_bytes(), a.export_project(item["id"]).read_bytes())
            with ZipFile(archive) as cart:
                self.assertEqual(cart.namelist(), ["manifest.json", "main.py"])
                manifest = json.loads(cart.read("manifest.json"))
                self.assertEqual(manifest["revision"], 2)
                self.assertEqual(manifest["sha256"], hashlib.sha256(cart.read("main.py")).hexdigest())

    def test_import_copy_and_invalid_archives(self):
        with tempfile.TemporaryDirectory() as home:
            store = Store(home)
            original = store.create_project("Coil", "snake")
            archive = store.export_project(original["id"])
            loaded = store.import_project(archive)
            self.assertNotEqual(loaded["id"], original["id"])
            self.assertEqual(loaded["source"], original["source"])
            self.assertEqual(loaded["title"], original["title"])
            self.assertEqual(loaded["revision"], 1)
            self.assertEqual(store.get_active(), loaded["id"])
            with ZipFile(archive) as cart:
                manifest = json.loads(cart.read("manifest.json"))
            for name, entries in [
                ("tampered", {"manifest.json": json.dumps(manifest), "main.py": original["source"] + "\n# edit"}),
                ("extra", {"manifest.json": json.dumps(manifest), "main.py": SOURCE, "extras": "1"}),
                ("wrong-path", {"manifest.json": json.dumps(manifest), "../main.py": SOURCE}),
                ("oversize", {"manifest.json": json.dumps(manifest), "main.py": "x"*50000}),
            ]:
                with self.subTest(name=name):
                    path = Path(home) / (name + ".lab")
                    with ZipFile(path, "w") as cart:
                        for entry, data in entries.items():
                            cart.writestr(entry, data)
                    with self.assertRaises(ValueError):
                        store.import_project(path)
                    self.assertEqual(store.get_active(), loaded["id"])

    def test_stdio_authoring_and_replay(self):
        with tempfile.TemporaryDirectory() as home:
            cmd = [sys.executable, str(STUDIO / "lab_mcp.py")]
            env = dict(os.environ, LAB_STUDIO_HOME=home)
            with subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, env=env) as process:
                def send(request):
                    process.stdin.write(json.dumps(request) + "\n")
                    process.stdin.flush()

                def call(method, params):
                    send({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
                    reply = json.loads(process.stdout.readline())
                    self.assertEqual(reply["id"], 1)
                    self.assertNotIn("error", reply)
                    return reply["result"]

                def tool(name, **args):
                    return call("tools/call", {"name": name, "arguments": args})

                try:
                    hello = call("initialize", {"protocolVersion": "2025-11-25",
                                 "capabilities": {}, "clientInfo": {"name": "qa", "version": "1"}})
                    self.assertEqual(hello["protocolVersion"], "2025-11-25")
                    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
                    names = {t["name"] for t in call("tools/list", {})["tools"]}
                    self.assertIn("lab_info", names)
                    self.assertIn("lab_playtest", names)
                    new_game = tool("lab_create_project", title="Tape Test", template="falling-blocks")
                    project = json.loads(new_game["content"][0]["text"])
                    key = project["id"]
                    self.assertEqual(Store(home).get_active(), key)
                    drop = tool("lab_playtest", project_id=key, steps=[{"frames": 1, "buttons": ["b"]}])
                    block_state = json.loads(drop["content"][0]["text"])["state"]
                    self.assertEqual(block_state["metrics"]["lines"], 1)
                    self.assertGreater(block_state["score"], 0)
                    update = tool("lab_update_project", project_id=key, source=SOURCE, expected_revision=1)
                    self.assertEqual(json.loads(update["content"][0]["text"])["revision"], 2)
                    stale = tool("lab_update_project", project_id=key, source=SOURCE, expected_revision=1)
                    self.assertTrue(stale["isError"])
                    invalid = tool("lab_playtest", project_id=key, steps=[{"frames": 601}])
                    self.assertTrue(invalid["isError"])
                    replay = tool("lab_playtest", project_id=key,
                                  steps=[{"frames": 8, "buttons": ["a"]}, {"frames": 3}])
                    data, frame = replay["content"]
                    result = json.loads(data["text"])
                    self.assertEqual(result["state"]["score"], 8)
                    self.assertEqual(result["frames"], 11)
                    with Image.open(BytesIO(base64.b64decode(frame["data"]))) as png:
                        self.assertEqual(png.size, (160, 160))
                    exported = tool("lab_export_project", project_id=key)
                    self.assertTrue(Path(json.loads(exported["content"][0]["text"])["path"]).is_file())

                    db = Store(home)
                    before = db.list_projects()
                    inputs = [{"frames": 4, "buttons": ["a"]}]
                    draft = tool("lab_playtest", source=SOURCE, steps=inputs)
                    draft_state = json.loads(draft["content"][0]["text"])
                    self.assertIsNone(draft_state["project_id"])
                    self.assertIsNone(draft_state["revision"])
                    self.assertEqual(draft_state["state"]["score"], 4)
                    self.assertTrue(tool("lab_playtest", project_id=key, source=SOURCE)["isError"])
                    self.assertTrue(tool("lab_playtest")["isError"])
                    self.assertTrue(tool("lab_create_project", title="Broken", source="def broken(")["isError"])
                    self.assertEqual(db.list_projects(), before)
                    self.assertEqual(db.get_active(), key)

                    authored = tool("lab_create_project", title="Tide", source=SOURCE, controls={"a": "Score"})
                    saved = db.get_project(json.loads(authored["content"][0]["text"])["id"])
                    self.assertEqual(saved["revision"], 1)
                    self.assertEqual(saved["source"], SOURCE)
                    self.assertEqual(saved["controls"], {"a": "Score"})
                    self.assertEqual(db.get_active(), saved["id"])
                    self.assertNotEqual(db.get_project("falling-blocks")["source"], SOURCE)
                    played = tool("lab_playtest", project_id=saved["id"], steps=inputs)
                    self.assertEqual(draft_state["state"], json.loads(played["content"][0]["text"])["state"])
                    self.assertEqual(draft["content"][1], played["content"][1])
                finally:
                    process.stdin.close()
                    process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
