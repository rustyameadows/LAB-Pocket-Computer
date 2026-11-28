#!/usr/bin/python3
"""Install this checkout's native application launcher for the current user."""
import os
from pathlib import Path
import tempfile


def exec_arg(path):
    text = str(path)
    if any(ch in text for ch in "\r\n"):
        raise ValueError("The checkout path must fit on one line.")
    for char in ('\\', '"', '$', '`'):
        text = text.replace(char, '\\' + char)
    # Desktop-entry string escaping is applied before Exec argument quoting.
    return '"' + text.replace("\\", "\\\\").replace('%', '%%') + '"'


def main():
    studio = Path(__file__).resolve().parent
    home = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    apps = home / 'applications'
    apps.mkdir(parents=True, exist_ok=True)
    target = apps / 'us.lab.PocketStudio.desktop'
    content = "\n".join([
        '[Desktop Entry]', 'Type=Application', 'Version=1.0', 'Name=LAB Studio',
        'Comment=Create and play LAB Pocket Computer cartridges',
        'Exec=' + exec_arg(studio / 'lab-studio'),
        'Icon=' + str(studio / 'studio-icon.png').replace('\\', '\\\\'),
        'Terminal=false', 'Categories=Development;Game;', 'StartupNotify=true', ''
    ])
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=apps, delete=False) as out:
        out.write(content)
        temp_path = Path(out.name)
    temp_path.chmod(0o644)
    temp_path.replace(target)
    print(target)


if __name__ == '__main__':
    main()
