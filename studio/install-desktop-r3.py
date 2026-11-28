#!/usr/bin/python3
"""Install the r3 Studio launcher in the current user's application menu."""
import os
from pathlib import Path
import runpy
import tempfile


def main():
    studio = Path(__file__).resolve().parent
    apps = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    target = apps / "us.lab.PocketStudio.desktop"
    quote = runpy.run_path(str(studio / "install-desktop.py"))["exec_arg"]
    content = "\n".join(("[Desktop Entry]", "Type=Application", "Version=1.0", "Name=LAB Studio",
                         "Comment=Create cartridges and connect a LAB Pocket", "Exec=" + quote(studio / "lab-studio-r3"),
                         "Icon=" + str(studio / "studio-icon.png").replace("\\", "\\\\"),
                         "Terminal=false", "Categories=Development;Game;", "StartupNotify=true", ""))
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=apps, delete=False) as file:
        file.write(content)
        temporary = Path(file.name)
    temporary.chmod(0o644)
    temporary.replace(target)
    print(target)


if __name__ == "__main__":
    main()
