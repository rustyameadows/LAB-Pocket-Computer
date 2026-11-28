# LAB Studio r3

Launch **LAB Studio** from the Linux application menu, or run `./studio/lab-studio-r3` from the project root. It opens the same local cartridge library used by the original Studio and its MCP server. The original version is also available through `./studio/lab-studio`.

## Ten additions

| | In Studio | What you can do |
|---|---|---|
| 1 | Cartridge shelf | Search titles, descriptions and game types. Ctrl+K jumps to the search field. Filtering keeps the current cartridge open. |
| 2 | Cartridge | Edit a title, description and button guide. Studio checks the saved revision when you apply changes. |
| 3 | Source | Find code with Ctrl+F. Drafts recover across close and reopen. Save & run publishes a revision. Remix preserves a draft that conflicts with another editor. |
| 4 | Playtest panel picker | Choose a 480 × 480 or 720 × 720 Pocket. The camera button saves a PNG at that physical resolution. |
| 5 | Playtest transport | Pause, step one frame, switch between ½×, 1× and 2×, and inspect score, tick and game-specific state. |
| 6 | Playtest recording | Record inputs for up to three minutes of game time. Replay, save or open a recording tied to its source and seed. |
| 7 | Devices | Rescan Linux USB serial ports, select a Pocket, connect, inspect identity and capabilities, then disconnect. Two virtual profiles are built in. |
| 8 | Device mirror | View frames fetched from the connected peer, freeze the view, resume and save a native-resolution PNG. The peer can keep playing while the view is frozen. |
| 9 | Device controls | Load the selected saved game into a compatible peer’s memory, tap any of twenty keys, play, pause or reset. Available controls follow the peer’s reported capabilities. |
| 10 | Help | Open offline guides with F1, search troubleshooting steps, or copy a local diagnostics report. Devices also has a connection log. |

## Try the complete device path

1. Select **Twin Tide** in the library. If this is a fresh library, use **Import** and choose `studio/examples/Twin-Tide.lab`.
2. Open **Devices**, choose **Virtual Pocket · 720 × 720**, and click **Connect**. Each virtual Pocket runs its own game clock and framebuffer in a separate local process.
3. Click **Load selected game**. Tap **↑**, then **B** on the device keypad. The mirror shows two cleared rows and 350 points. Click **Freeze** and **Save PNG** for a 720 × 720 image.
4. Disconnect, select the 480 × 480 Pocket, and reconnect to test the other panel.

For a repeatable local playtest, select Twin Tide and open **Playtest**. In the recording menu beside **Replay**, choose **Open recording** and select `studio/r3/examples/Twin-Tide-double-clear-r3.labreplay.json`. It recreates the opening and scores 350 from two input ticks. On the desktop keyboard, **X** maps to Pocket **B**.

## Panels and physical hardware

The physical Pocket screens are **480 × 480** and **720 × 720**. Original LAB v0 cartridges draw at **160 × 160**. The player scales the whole frame using nearest-neighbor sampling. On the 480 panel each source pixel occupies 3 × 3 physical pixels. At 720 the scale is 4.5×, so source pixels alternate between four and five panel pixels along each axis. A hardware mirror can also show native-panel content outside the cartridge canvas.

USB device functions require board firmware that speaks **Pocket Link v1**. The host driver, board-side protocol adapter, and independent reference peer are in this release. The ESP/RP board package must connect the adapter to its USB, active framebuffer, keypad and game callbacks. See [Pocket Link and board integration](r3/DEVICE-LINK-r3.md). Physical throughput and panel behavior still require bench validation.

## MCP and installation

From the studio directory, use the r3 launcher in the MCP registration. Adjust the absolute path if the checkout moves.

```sh
codex mcp add LAB -- /home/rusty-meadows/dev/LAB-Pocket-Computer/studio/lab-studio-r3 mcp
/usr/bin/python3 install-desktop-r3.py
```

The original eight MCP tools remain available. `lab_info` reports the logical canvas and both physical panels. `lab_playtest` accepts optional `panel: 480` or `panel: 720` and returns a PNG at that size. Omitting the panel returns the original 160 × 160 image. This tool runs the cartridge in the local simulator. Use **Devices** to inspect a connected peer.

Linux requires system Python 3, GTK 4 with PyGObject and Pillow. USB serial support uses Linux device nodes and the Python standard library. The reference board adapter is compatible with MicroPython. The r3 recovery database lives beside `studio.sqlite3` in the Studio data directory.

Run both suites from the studio directory. A graphical session enables the native UI checks.

```sh
/usr/bin/python3 -B -m unittest discover -s tests -v
/usr/bin/python3 -B -m unittest discover -s r3/tests -v
```
