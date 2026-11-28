"""Public r3 stdio contract and the native, shared-library editor workflow."""
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk
from PIL import Image

STUDIO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO))
from r3.main import ReleaseApp, Workbench


class ReleaseTests(unittest.TestCase):
    def test_mcp_panel_previews_and_default(self):
        with tempfile.TemporaryDirectory() as library:
            requests = [("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "qa","version":"1"}}),
                        ("tools/list", {}), ("tools/call", {"name":"lab_info","arguments":{}})]
            args = {"project_id": "falling-blocks", "steps": [{"buttons": ["b"], "frames": 1}]}
            for panel in (None, 480, 720, 160):
                requests.append(("tools/call", {"name": "lab_playtest", "arguments": args if panel is None else {**args,"panel":panel}}))
            lines = [json.dumps({"jsonrpc":"2.0","id":i,"method":method,"params":params}) for i,(method,params) in enumerate(requests)]
            p = subprocess.run([str(STUDIO / "lab-studio-r3"), "mcp"], input="\n".join(lines)+"\n",
                               capture_output=True, env={**os.environ,"LAB_STUDIO_HOME":library},
                               text=True, timeout=10, check=True)
            replies = [json.loads(l)["result"] for l in p.stdout.splitlines()]
            play = next(t for t in replies[1]["tools"] if t["name"]=="lab_playtest")
            self.assertEqual(play["inputSchema"]["properties"]["panel"]["enum"], [480,720])
            self.assertEqual(json.loads(replies[2]["content"][0]["text"])["panel_sizes"], [[480,480],[720,720]])
            original = None
            for reply, size in zip(replies[3:6], (160,480,720)):
                state, frame = reply["content"]
                self.assertEqual(json.loads(state["text"])["state"]["score"], 136)
                with Image.open(BytesIO(base64.b64decode(frame["data"]))) as png:
                    self.assertEqual(png.size, (size,size))
                    if size == 160:
                        original = png.convert("RGB")
                    else:
                        self.assertEqual(original.resize((size,size),Image.Resampling.NEAREST).tobytes(),png.convert("RGB").tobytes())
            self.assertTrue(replies[6]["isError"])

    @unittest.skipUnless(Gdk.Display.get_default(), "Native editor test requires a GTK display")
    def test_find_recover_and_edit_details(self):
        with tempfile.TemporaryDirectory() as library, patch.dict(os.environ, LAB_STUDIO_HOME=library, LAB_STUDIO_ISOLATED="1"):
            app = ReleaseApp()
            app.register(None)
            app.activate()
            win = app.window
            try:
                win.search.set_text("prism")
                self.assertEqual(win.cart_count.get_text(), "1/3")
                self.assertEqual(win.project["id"], "falling-blocks")
                win.search.set_text("")
                win.tabs["source"].set_active(True)
                win.source_find.set_text("shuffled_bag")
                win.find_next()
                self.assertTrue(win.buffer.get_has_selection())
                win.buffer.set_text(win.source() + "\n# recovered draft\n")
                win.close()
                win = Workbench(app)
                self.assertTrue(win.dirty)
                self.assertTrue(win.source().endswith("# recovered draft\n"))
                win.save()
                self.assertFalse(win.dirty)
                win.tabs["settings"].set_active(True)
                win.metadata.title.set_text("Harbor")
                win.metadata.fields["left"].set_text("Sail west")
                # Simulate an agent saving the same project while the form is open.
                prior = win.project
                win.store.update_project(prior["id"], prior["source"], prior["revision"], title="Newer copy")
                win.poll()
                self.assertEqual(win.metadata.title.get_text(), "Harbor")
                win.metadata.save()
                self.assertEqual(win.store.get_project(prior["id"])["title"], "Newer copy")
                win.metadata.revert()
                win.metadata.title.set_text("Harbor")
                win.metadata.fields["left"].set_text("Sail west")
                win.metadata.save()
                self.assertEqual(win.project["title"], "Harbor")
                self.assertEqual(win.project["controls"]["left"], "Sail west")
                win.tabs["help"].set_active(True)
                win.support.search.set_text("cable")
                win.support.filter()
                self.assertEqual(sum(s.get_visible() for s,_ in win.support.rows),1)
                self.assertIn("Harbor", win.support.refresh())
            finally:
                win.close()
                app.quit()
