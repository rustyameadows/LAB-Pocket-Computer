"""Navigation and device/local ownership from the actual GTK controls."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

STUDIO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO))
from ui import Gtk, Gdk
from r3.tests.test_device_panel import until
from r4.main import StudioApp, APP_ID


def descendants(root):
    yield root
    node = root.get_first_child()
    while node:
        yield from descendants(node)
        node = node.get_next_sibling()


@unittest.skipUnless(Gdk.Display.get_default(), "GTK display required")
class NavigationTests(unittest.TestCase):
    def test_local_startup_device_inventory_and_explicit_transfer(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, LAB_STUDIO_HOME=folder, LAB_STUDIO_ISOLATED="1"):
            app = StudioApp()
            app.register(None)
            app.activate()
            w = app.window
            try:
                self.assertEqual(app.get_application_id(), APP_ID)
                self.assertEqual(w.section_pages.get_visible_child_name(), "local")
                self.assertTrue(w.local_shelf.get_visible())
                self.assertEqual(set(w.tabs), {"play","source","settings"})
                self.assertIs(w.section_buttons["devices"].get_parent(), w.section_buttons["local"].get_parent())
                local = w.project["id"]
                w.tabs["source"].set_active(True)
                draft = w.source() + "\n# a local draft"
                w.buffer.set_text(draft)
                w.section_buttons["devices"].set_active(True)
                d = w.device_panel
                until(lambda: "virtual:720" in d.device_rows)
                self.assertEqual(w.get_title(), "Device Manager · LAB Studio")
                self.assertFalse(w.local_shelf.get_mapped())
                self.assertFalse(w.editor.get_mapped())
                self.assertFalse(w.export_btn.get_mapped())
                self.assertFalse(d.body.get_mapped())
                self.assertTrue(d.inventory.get_mapped())
                self.assertFalse(d.load_button.get_sensitive())
                self.assertEqual(d.state, "offline")
                d.device_rows["virtual:720"].emit("clicked")
                until(lambda: d.current_frame is not None)
                running_title = d.current_frame.title
                self.assertEqual(d.current_frame.image.size, (720, 720))
                w.store.set_active("snake")
                w.poll()
                self.assertEqual(w.get_title(), "Device Manager · LAB Studio")
                self.assertEqual(w.section_pages.get_visible_child_name(), "devices")
                self.assertEqual(running_title, d.current_frame.title)
                d.load_button.emit("clicked")
                controls = list(descendants(d.picker))
                selector = next(x for x in controls if isinstance(x, Gtk.DropDown))
                confirm = next(x for x in controls if isinstance(x,Gtk.Button) and
                               any(isinstance(t,Gtk.Label) and t.get_text()=="Load into device memory" for t in descendants(x)))
                self.assertFalse(confirm.get_sensitive())
                projects = w.store.list_projects()
                target = next(i for i,x in enumerate(projects) if x["id"]=="breakout")
                selector.set_selected(target)
                confirm.emit("clicked")
                until(lambda: d.current_frame.title == projects[target]["title"])
                self.assertEqual(w.store.get_active(), "snake")
                w.section_buttons["local"].set_active(True)
                self.assertFalse(d.visible_page)
                self.assertEqual(w.project["id"], "snake")
                w.store.set_active(local)
                w.poll()
                self.assertTrue(w.dirty)
                self.assertEqual(w.source(), draft)
                self.assertEqual(w.pages.get_visible_child_name(), "source")
                w.section_buttons["devices"].set_active(True)
                self.assertEqual(d.state, "online")
                d.connect_button.emit("clicked")
                until(lambda: d.state == "offline")
                self.assertTrue(d.inventory.get_mapped())
            finally:
                w.close()
                app.quit()
