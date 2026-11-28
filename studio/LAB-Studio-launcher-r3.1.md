# LAB Studio r3 launcher

Open **LAB Studio r3** from the Linux applications menu. The header shows **r3** and the workspace row includes **Devices** between **Cartridge** and **Help**.

From the repository root, install or repair the desktop entry with:

```sh
/usr/bin/python3 studio/install-desktop-r3.1.py
gtk-launch us.lab.PocketStudio.R3
```

The desktop filename matches the GTK application ID so GNOME can associate the launcher with the running r3 window. The installer also writes a hidden compatibility entry that sends older shortcuts to the same r3 executable. Both entries share the regular Studio cartridge library.

For a direct launch from the checkout, run `./studio/lab-studio-r3`. The original release is archived at `./studio/lab-studio`.
