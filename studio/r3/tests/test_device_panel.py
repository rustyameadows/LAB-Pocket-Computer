"""Native device console through its GTK controls. Requires a display session."""
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk
from PIL import Image

STUDIO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO))
from r3.device_panel import DevicePanel
from r3.device_link import DeviceError


def until(predicate, timeout=5):
    end = time.monotonic() + timeout
    context = GLib.MainContext.default()
    while time.monotonic() < end:
        while context.pending():
            context.iteration(False)
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError("Timed out waiting for native device panel")


@unittest.skipUnless(Gdk.Display.get_default(), "Device panel requires a GTK display")
class DevicePanelTest(unittest.TestCase):
    def test_scan_load_input_freeze_capture_reconnect(self):
        window = Gtk.Window()
        window.project = {"title": "QA Reef",
                          "source": (STUDIO / "samples/falling-blocks/main.py").read_text()}
        window.message = lambda *args: None
        panel = DevicePanel(window)
        window.set_child(panel)
        window.set_default_size(750, 620)
        window.present()
        panel.on_visible(True)
        try:
            until(lambda: panel.state == "offline" and len(panel.endpoints) >= 2)
            with patch("r3.device_panel.DeviceLink.open", side_effect=DeviceError("USB port is busy")):
                panel.connect_button.emit("clicked")
                until(lambda: panel.state == "offline")
                self.assertIn("USB port is busy", panel.endpoint_detail.get_text())
                self.assertTrue(panel.connect_button.get_sensitive())
            for size in (480, 720):
                size_index = next(i for i, ep in enumerate(panel.endpoints) if ep.id == f"virtual:{size}")
                panel.selector.set_selected(size_index)
                panel.connect_button.emit("clicked")
                until(lambda: panel.current_frame is not None)
                self.assertEqual(panel.current_frame.image.size, (size, size))
                self.assertIn("160 × 160", panel.identity.get_text())
                panel.load_button.emit("clicked")
                until(lambda: panel.current_frame.title == "QA Reef" and not panel.current_frame.running)
                panel.key_buttons["key09"].emit("clicked")
                until(lambda: panel.current_frame.score == 136)
                panel.freeze_button.emit("clicked")
                self.assertTrue(panel.frozen)
                held = panel.current_frame
                panel.control_buttons["play"].emit("clicked")
                until(lambda: panel.pending_actions == 0)
                with tempfile.TemporaryDirectory() as folder:
                    target = Path(folder) / "frame.png"
                    def save_dialog(dialog, _window, _cancel, callback):
                        callback(dialog, None)
                    with patch.object(Gtk.FileDialog, "save", save_dialog), patch.object(
                            Gtk.FileDialog, "save_finish", return_value=Gio.File.new_for_path(str(target))):
                        panel.capture_button.emit("clicked")
                    with Image.open(target) as png:
                        self.assertEqual(png.size, (size, size))
                        self.assertEqual(png.tobytes(), held.image.tobytes())
                self.assertIs(panel.current_frame, held)
                panel.freeze_button.emit("clicked")
                until(lambda: panel.current_frame.running and panel.current_frame.tick > held.tick)
                panel.connect_button.emit("clicked")
                until(lambda: panel.state == "offline")
                self.assertIsNone(panel.current_frame)
        finally:
            panel.shutdown()
            window.close()
