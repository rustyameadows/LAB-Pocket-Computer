"""Regression for GNOME resolving the visible entry and the previous desktop ID."""
import configparser
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

STUDIO = Path(__file__).resolve().parents[2]


class DesktopEntryTest(unittest.TestCase):
    def test_upgrade_exposes_one_menu_item_and_keeps_the_previous_id(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "XDG_DATA_HOME": directory}
            for installer in ("install-desktop.py", "install-desktop-r3.1.py", "install-desktop-r3.1.py"):
                subprocess.run([sys.executable, str(STUDIO / installer)], check=True, capture_output=True, env=env)
            apps = Path(directory) / "applications"
            visible = []
            for file in apps.glob("*.desktop"):
                config = configparser.ConfigParser(interpolation=None)
                config.read(file)
                entry = config["Desktop Entry"]
                self.assertEqual(entry["Exec"], f'"{STUDIO}/lab-studio-r3"')
                self.assertEqual(entry["Name"], "LAB Studio r3")
                if not entry.getboolean("NoDisplay", fallback=False):
                    visible.append(file.name)
            self.assertEqual(visible, ["us.lab.PocketStudio.R3.desktop"])
            self.assertTrue((apps / "us.lab.PocketStudio.desktop").exists())
