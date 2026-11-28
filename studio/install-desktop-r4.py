#!/usr/bin/python3
"""Install LAB Studio r4 under its actual GTK/Wayland application ID."""
import os
from pathlib import Path
import runpy
import tempfile

APP_ID = "us.lab.PocketStudio.R4"
PREVIOUS_IDS = ("us.lab.PocketStudio", "us.lab.PocketStudio.R3")


def write_entry(path, content):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as out:
        out.write(content)
        temporary = Path(out.name)
    try:
        temporary.chmod(0o644)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def install(studio, data_dir):
    apps = data_dir / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    executable = studio / "lab-studio-r4"
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise FileNotFoundError(f"Missing executable: {executable}")
    quote = runpy.run_path(str(studio / "install-desktop.py"))["exec_arg"]
    common = ["[Desktop Entry]", "Type=Application", "Version=1.0", "Name=LAB Studio r4",
              "Comment=Make games and mirror a LAB Pocket Computer",
              "Exec=" + quote(executable), "Icon=" + str(studio / "studio-icon.png").replace("\\", "\\\\"),
              "Terminal=false", "Categories=Development;IDE;", "StartupNotify=true"]
    canonical = apps / f"{APP_ID}.desktop"
    write_entry(canonical, "\n".join(common + ["Keywords=Pocket;Cartridge;Device;Mirror;", ""]))
    # Keep existing links to the old desktop ID usable while advertising a single menu entry.
    for previous in PREVIOUS_IDS:
        write_entry(apps / f"{previous}.desktop", "\n".join(common + ["NoDisplay=true", ""]))
    return canonical


if __name__ == "__main__":
    data_home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    print(install(Path(__file__).resolve().parent, data_home))
