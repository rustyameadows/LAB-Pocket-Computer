# LAB Studio v0

LAB Studio is a local GTK 4 desktop application for making LAB Pocket Computer games. Play or remix a sample, edit its Python source, and run the new revision. A stdio MCP server shares the same cartridge library with the desktop app.

## Run Studio

From this directory on Linux, run:

```sh
./lab-studio
```

The launcher uses the system Python 3, PyGObject with GTK 4, and Pillow. On Ubuntu the packages are `python3-gi`, `gir1.2-gtk-4.0` and `python3-pil`. The app and the MCP server work offline. To add LAB Studio to the desktop application menu, run `/usr/bin/python3 install-desktop.py` from this checkout. Re-run it if the checkout moves.

**Stackfall** teaches the controls with a ready-made opening. Press Play and tap **X** to hard-drop the first bar and clear a row. Use **←/→** to move, **↑ or Z** to rotate, and **↓** to soft-drop. **Switchback** is a snake game with food, boost and collisions. **Prism Break** has paddle control, aim, destructible bricks and three lives. Its Z key launches the ball. The on-screen Pocket keypad also accepts clicks.

Select **Remix** to copy a project before editing. Open **Source**, change a rule or color, then choose **Save & run**. Invalid edits stay in the editor with an error message. The editor keeps local drafts through project switches and checks the saved revision when another client edits a cartridge.

## Connect an MCP client

Register the checkout once with Codex, using the absolute path to the launcher. The repository on this computer uses:

```sh
codex mcp add LAB -- /home/rusty-meadows/dev/LAB-Pocket-Computer/studio/lab-studio mcp
codex mcp get LAB
```

Other clients can launch the same executable with the argument `mcp` and stdio transport. The client and Studio should run as the same user with the same `LAB_STUDIO_HOME`. The default library lives in `$XDG_DATA_HOME/lab-studio` or `~/.local/share/lab-studio`. The desktop window observes committed changes. The MCP tools also work while the window is closed.

Try asking:

> Use LAB to make a falling-block game for my Pocket Computer. Give it an ocean palette and a bonus for clearing two rows at once. Playtest a line clear and open the game in Studio.

For a new game, the agent can read a sample such as `falling-blocks`, write its own `main.py`, and send the finished source and control labels to `lab_create_project`. This creates one new cartridge with its own ID. To try a draft before saving, call `lab_playtest` with `source`; after saving, replay the same inputs with `project_id`. Use `lab_update_project` when the user asks to edit a saved cartridge. MCP clients can request approval for that replacement.

| Tool | Result |
| --- | --- |
| `lab_info` | Game API, controls, templates and runtime limits |
| `lab_list_projects` | Cartridge library and selected project |
| `lab_create_project` | New project with authored source or a copy of a playable template, selected in Studio |
| `lab_read_project` | Editable source, metadata and revision |
| `lab_update_project` | Validate and save replacement source using the expected revision |
| `lab_open_project` | Select a project in Studio |
| `lab_playtest` | Replay held-button segments against a saved project or unsaved source and return state plus a 160 × 160 PNG |
| `lab_export_project` | Export the saved revision as a portable `.lab` archive |

For example, send `lab_playtest` the new project's ID, seed `1`, and `steps: [{"buttons":["b"],"frames":1}]`. Its returned frame belongs to that replay. The user's live game continues independently.

## Cartridge and runtime

A cartridge contains a versioned manifest and a UTF-8 `main.py`. Export saves a revision under the library's `exports/` directory. Use the **Import** button or open it as a new editable copy from a terminal:

```sh
./lab-studio open /path/to/game.lab
```

Games implement `init()`, `update()` and `draw()`. The runtime supplies a 160 × 160 pixel canvas, a 30 Hz logical clock, 20 physical key IDs, named actions, per-key lights, seeded randomness and a persistent-in-session `state` dictionary. Use `clear`, `rect`, `line`, `pixel` and `text` for drawing. The three complete projects in `samples/` are editable examples. See `engine.API_DOC` or call `lab_info` for the supported Python subset.

Studio runs scripts in a bounded desktop interpreter. The UI and MCP share that interpreter and report errors with source lines. Saves, selections, and edit checks use SQLite transactions. **Studio v0 targets original LAB games.** The Game Boy / Game Boy Color emulator is a separate future player.

### MicroPython target

`pocket_player.py` is the reference player for trusted source on a MicroPython port with `framebuf`. Unpack the cartridge, put `pocket_player.py`, `pixel_font.py` and `pocket_keys.py` on the module path, and read `main.py`. For example:

```python
from pocket_player import PocketPlayer

with open("main.py") as source:
    game = PocketPlayer(source.read(), seed=1)
game.step(("key09",))
# game.pixels is the 51,200-byte RGB565 buffer.
# game.lights maps physical keys to requested RGB colors.
```

A board adapter must poll the keypad, call `step` at the desired cadence, send frames to the ESP display host, and apply LED changes. Connectors, firmware installation and board timing await physical bring-up. The MicroPython reference executes trusted cartridge source as native MicroPython. The desktop editor uses its own restricted interpreter.

The exported example in `examples/Pocket-Cascade-v0-r1.lab` was created and edited through MCP. It adds a sunset palette and a scoring bonus for consecutive line clears.

`examples/Twin-Tide.lab` came from a fresh Codex agent given the ocean-game prompt above. It read the game API and starter, playtested its draft, created the cartridge with its authored source, then played, opened and exported the saved game through LAB MCP. To reproduce its double clear, start a new round, tap Up and then X (Pocket B). The two rows earn 200 points and the Twin Tide bonus adds 150. For a single clear, reset, move left once and hard-drop for 100 points. The agent tested both openings with seed 8.

## Checks

```sh
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 tests/check_micropython.py /path/to/unix/micropython
```

The optional second command compares all three samples on a Unix MicroPython build with `framebuf` and `json` against the desktop runner. It checks score, tick, status, key LEDs and every RGB565 pixel after the same input sequence. It also accepts additional cartridge source paths. This test covers behavior and rendering on a real interpreter. Physical display transport and frame rate require hardware measurements.

Open `design/studio-concepts-r1.html` locally to compare the Workbench, Cartridge shelf and Playtest UI studies. Each shows frames recorded from the included games.
