"""Native Pocket panel preview and deterministic input recording for Studio."""
import hashlib
import json
import time
from pathlib import Path

from gi.repository import GLib

from engine import FPS, Game, GameError
from pocket_keys import expand_buttons
from ui import Gsk, Gtk, Monitor, Pango, box, button, label, pad, rectangle

from r3.panels import PANELS, render_panel

SPEEDS = (0.5, 1.0, 2.0)
MAX_TICKS = FPS * 60 * 3
MAX_REPLAY_BYTES = 128 * 1024
KEY_IDS = tuple(f"key{n:02d}" for n in range(1, 21))


class InputTape:
    def __init__(self, source, seed=1):
        if type(seed) is not int or not 0 <= seed <= 0x7fffffff:
            raise ValueError("Replay seed must be a nonnegative 31-bit integer.")
        self.sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
        self.seed = seed
        self.runs = []
        self.length = 0

    def append(self, buttons):
        if self.length >= MAX_TICKS:
            raise ValueError("A recording holds up to three minutes of game time.")
        active = expand_buttons(buttons)
        mask = sum(1 << i for i, key in enumerate(KEY_IDS) if key in active)
        if self.runs and self.runs[-1][0] == mask:
            self.runs[-1][1] += 1
        else:
            self.runs.append([mask, 1])
        self.length += 1

    def frames(self):
        for mask, count in self.runs:
            buttons = tuple(key for i, key in enumerate(KEY_IDS) if mask & (1 << i))
            for _ in range(count):
                yield buttons

    def dumps(self):
        return json.dumps({"format": "lab-input-v1", "source_sha256": self.sha256,
                           "seed": self.seed, "runs": self.runs}, separators=(",", ":"))

    @classmethod
    def loads(cls, source, data):
        if len(data) > MAX_REPLAY_BYTES:
            raise ValueError("Replay file is too large.")
        try:
            record = json.loads(data)
        except (UnicodeError, RecursionError, ValueError) as exc:
            raise ValueError("The replay file contains invalid JSON.") from exc
        if not isinstance(record, dict) or record.get("format") != "lab-input-v1":
            raise ValueError("Choose a LAB input replay file.")
        tape = cls(source, record.get("seed"))
        if record.get("source_sha256") != tape.sha256:
            raise ValueError("This recording requires the cartridge source it was recorded with.")
        runs = record.get("runs")
        if not isinstance(runs, list) or not 0 < len(runs) <= MAX_TICKS:
            raise ValueError("Replay contains an invalid number of input runs.")
        for pair in runs:
            if not isinstance(pair, list) or len(pair) != 2:
                raise ValueError("Invalid replay input run.")
            mask, count = pair
            if (type(mask) is not int or not 0 <= mask < 1 << len(KEY_IDS)
                    or type(count) is not int or not 1 <= count <= MAX_TICKS - tape.length):
                raise ValueError("Replay input or duration is out of range.")
            tape.runs.append([mask, count])
            tape.length += count
        return tape


class PanelMonitor(Monitor):
    def __init__(self):
        super().__init__()
        self.panel_size = PANELS[0]
        self.set_size_request(160, 166)

    def frame(self, image):
        super().frame(render_panel(image, self.panel_size))

    def do_snapshot(self, snapshot):
        width, height = self.get_width(), self.get_height()
        if min(width, height) < 1:
            return
        bounds = rectangle(0, 0, width, height)
        snapshot.append_color(self.shades[0], bounds)
        snapshot.push_repeat(bounds, rectangle(0, 0, 14, 14))
        snapshot.append_color(self.shades[1], rectangle(9, 9, 1, 1))
        snapshot.pop()
        # The panel has already been rasterized. Let its preview fill the space
        # between controls, even when the window is only a few pixels below 2×.
        side = min(width - 30, height - 30, self.panel_size)
        if side < 1:
            return
        left, top = (width - side) // 2, (height - side) // 2
        snapshot.append_color(self.shades[2], rectangle(left-7, top-4, side+14, side+14))
        snapshot.append_color(self.shades[3], rectangle(left-7, top-7, side+14, side+14))
        snapshot.append_color(self.shades[4], rectangle(left-3, top-3, side+6, side+6))
        if self.surface is not None:
            snapshot.append_scaled_texture(self.surface, Gsk.ScalingFilter.NEAREST,
                                           rectangle(left, top, side, side))


class PlaytestMixin:
    def play_page(self):
        self.tape = None
        self.recording = False
        self.replaying = None
        self.tape_position = 0
        self.preview_source = ""
        self.preview_project = None
        area = super().play_page()
        stage = self.monitor.get_parent()
        header = stage.get_first_child()
        header_strip = header.get_first_child()
        header_strip.remove(header_strip.get_last_child())
        self.panel_picker = Gtk.DropDown.new_from_strings(["480 × 480", "720 × 720"])
        self.panel_picker.set_tooltip_text("Pocket panel resolution")
        self.panel_picker.connect("notify::selected", self._panel_changed)
        header_strip.append(self.panel_picker)
        capture = button("", self.capture_panel, "minor-action", "camera-photo-symbolic")
        capture.set_tooltip_text("Save the selected panel as a PNG")
        header_strip.append(capture)
        stage.remove(self.monitor)
        self.monitor = PanelMonitor()
        stage.insert_child_after(self.monitor, header)

        transport = stage.get_last_child().get_first_child()
        self.step_btn = button("Step", self.step_once, "secondary-action")
        self.step_btn.set_tooltip_text("Pause and advance one game tick")
        transport.insert_child_after(self.step_btn, self.play_btn)
        self.speed_picker = Gtk.DropDown.new_from_strings(["½×", "1×", "2×"])
        self.speed_picker.set_selected(1)
        self.speed_picker.set_tooltip_text("Playback speed")
        self.speed_picker.connect("notify::selected", self._speed_changed)
        transport.insert_child_after(self.speed_picker, self.step_btn)

        ribbon = pad(box(spacing=6), 9, 6)
        self.record_btn = Gtk.Button(label="Record")
        self.record_btn.add_css_class("secondary-action")
        self.record_btn.set_tooltip_text("Record a new run from frame zero, seed 1")
        self.record_btn.connect("clicked", lambda *_: self.toggle_recording())
        ribbon.append(self.record_btn)
        self.replay_btn = button("Replay", self.replay_recording, "secondary-action")
        self.replay_btn.set_tooltip_text("Play back this input recording from frame zero")
        ribbon.append(self.replay_btn)
        self.tape_note = label("No recording", "caption")
        self.tape_note.set_hexpand(True)
        ribbon.append(self.tape_note)
        files = Gtk.MenuButton(icon_name="document-open-symbolic")
        files.set_tooltip_text("Open or save an input recording")
        file_menu = Gtk.Popover()
        actions = pad(box(True, 4), 5)
        self.save_tape_btn = button("Save recording…", self.save_recording)
        open_tape = button("Open recording…", self.open_recording)
        for item in (self.save_tape_btn, open_tape):
            item.connect("clicked", lambda *_: file_menu.popdown())
            actions.append(item)
        file_menu.set_child(actions)
        files.set_popover(file_menu)
        ribbon.append(files)
        stage.append(ribbon)

        controls = self.bindings.get_parent()
        inspector = Gtk.Expander(label="Game state")
        inspector.set_expanded(True)
        self.inspect_text = label("", "caption", True)
        self.inspect_text.set_selectable(True)
        self.inspect_text.set_max_width_chars(28)
        inspector.set_child(pad(self.inspect_text, 2, 5))
        controls.append(Gtk.Separator())
        controls.append(inspector)
        self._show_tape()
        return area

    def choose_panel(self, size):
        if size not in PANELS:
            raise ValueError("Unknown Pocket panel size.")
        self.panel_picker.set_selected(PANELS.index(size))

    def build_bindings(self, controls):
        super().build_bindings(controls)
        for row in self.bindings:
            chip = row.get_first_child()
            chip.set_ellipsize(Pango.EllipsizeMode.NONE)

    def _panel_changed(self, *_):
        self.monitor.panel_size = PANELS[self.panel_picker.get_selected()]
        if self.game:
            self.draw_frame()

    def _speed_changed(self, *_):
        self.clock = time.monotonic()
        self.playback_time = 0

    def export_panel(self, path):
        if not self.game:
            raise ValueError("Select a playable cartridge first.")
        render_panel(self.game.image(), self.monitor.panel_size).save(path, format="PNG")

    def capture_panel(self):
        if not self.game:
            return
        size = self.monitor.panel_size
        # Freeze pixels when Capture is clicked; the file chooser may stay open during play.
        image = render_panel(self.game.image(), size)
        filename = f"pocket-{size}-frame-{self.game.inspect()['tick']}.png"
        self._save_dialog("Save panel image", filename,
                          lambda path: image.save(path, format="PNG"))

    def _save_dialog(self, title, name, write):
        chooser = Gtk.FileDialog(title=title, initial_name=name)
        def selected(dialog, result):
            try:
                selected_file = dialog.save_finish(result)
                path = selected_file.get_path()
                if not path:
                    raise ValueError("Choose a local file.")
                write(Path(path))
                self.message(f"Saved {Path(path).name}")
            except GLib.Error as exc:
                if not exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self.message(str(exc), True)
            except (OSError, ValueError) as exc:
                self.message(str(exc), True)
        chooser.save(self, None, selected)

    def _show_tape(self):
        available = bool(self.tape and self.tape.length)
        self.replay_btn.set_sensitive(available and not self.recording)
        self.save_tape_btn.set_sensitive(available and not self.recording)
        self.record_btn.set_label("Stop" if self.recording else "Record")
        if self.recording:
            self.tape_note.set_text(f"Recording · {self.tape.length} ticks")
        elif self.replaying is not None:
            self.tape_note.set_text(f"Replay · {self.tape_position}/{self.tape.length}")
        elif available:
            self.tape_note.set_text(f"{self.tape.length} ticks · seed {self.tape.seed}")
        else:
            self.tape_note.set_text("No recording")

    def install_preview(self, source):
        ident = self.project["id"] if self.project else None
        if self.preview_source != source or self.preview_project != ident:
            self.tape = None
        self.recording = False
        self.replaying = None
        self.preview_source = source
        self.preview_project = ident
        super().install_preview(source)
        self.step_btn.set_sensitive(bool(self.game))
        self.record_btn.set_sensitive(bool(self.game))
        if not self.game:
            self.inspect_text.set_text("Preview stopped")
        self._show_tape()

    def draw_frame(self):
        super().draw_frame()
        state = self.game.inspect()
        self.meter.set_text(f"F{state['tick']} · {state['score']} pts")
        self.meter.set_tooltip_text(f"Frame {state['tick']} · Score {state['score']}")
        metrics = state["metrics"]
        # Prefer game counters before internal coordinates and animation bookkeeping.
        ordered = sorted(metrics, key=lambda key: (key not in (
            "lines", "last_bonus", "lives", "level", "length", "bricks", "locks"), key))
        details = [f"{k.replace('_', ' ').capitalize()}  {metrics[k]}" for k in ordered
                   if k not in ("score", "status")][:8]
        details.extend(("160 × 160 game canvas", f"{self.monitor.panel_size} × {self.monitor.panel_size} panel"))
        self.inspect_text.set_text("\n".join([str(state["status"]), f"Frame  {state['tick']}",
                                              f"Score  {state['score']}", *details]))
        if self.recording or self.replaying is not None:
            self._show_tape()

    def toggle_recording(self):
        if self.recording:
            self.recording = False
            self.set_playing(False)
            self._show_tape()
            return
        if not self.game:
            return
        self.replaying = None
        self.clear_keys()
        self.tape = InputTape(self.preview_source)
        self.game = Game(self.preview_source, seed=self.tape.seed)
        self.recording = True
        self.draw_frame()
        self.set_playing(True)
        self._show_tape()

    def replay_recording(self):
        if not self.tape or not self.tape.length:
            return
        self.recording = False
        self.clear_keys()
        self.game = Game(self.preview_source, seed=self.tape.seed)
        self.replaying = self.tape.frames()
        self.tape_position = 0
        self.draw_frame()
        self.set_playing(True)
        self._show_tape()

    def save_recording(self):
        if not self.tape or not self.tape.length or self.recording:
            return
        data = self.tape.dumps()
        self._save_dialog("Save input recording", "pocket-replay.labreplay.json",
                          lambda path: path.write_text(data, encoding="utf-8"))

    def open_recording(self):
        if not self.game:
            return
        chooser = Gtk.FileDialog(title="Open input recording")
        def selected(dialog, result):
            try:
                chosen = dialog.open_finish(result)
                path = chosen.get_path()
                if not path:
                    raise ValueError("Choose a local recording.")
                with open(path, "rb") as stream:
                    tape = InputTape.loads(self.preview_source, stream.read(MAX_REPLAY_BYTES + 1))
                self.tape = tape
                self.replay_recording()
            except GLib.Error as exc:
                if not exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self.message(str(exc), True)
            except (OSError, ValueError) as exc:
                self.message(str(exc), True)
        chooser.open(self, None, selected)

    def press_number(self, num):
        if self.replaying is None:
            super().press_number(num)

    def _advance_one(self):
        if self.replaying is None:
            buttons = self.held | self.pulse
        else:
            buttons = next(self.replaying)
        self.game.step(buttons)
        self.pulse.clear()
        if self.recording:
            self.tape.append(buttons)
            if self.tape.length == MAX_TICKS:
                self.toggle_recording()
                self.message("Recording stopped at three minutes of game time.")
        elif self.replaying is not None:
            self.tape_position += 1
            if self.tape_position == self.tape.length:
                self.replaying = None
                self.set_playing(False)
                self.status_msg.set_text(f"Replay complete · {self.tape_position} ticks")
                self._show_tape()

    def step_once(self):
        if not self.game:
            return
        self.set_playing(False)
        try:
            self._advance_one()
            self.draw_frame()
        except (GameError, ValueError) as exc:
            self._runtime_error(exc)

    def _runtime_error(self, exc):
        self.recording = False
        self.replaying = None
        self.set_playing(False)
        self._show_tape()
        self.message(str(exc), True)

    def tick(self):
        if not self.playing or not self.game:
            return True
        now = time.monotonic()
        elapsed = min(0.12, now - self.clock)
        self.clock = now
        self.playback_time += elapsed * SPEEDS[self.speed_picker.get_selected()]
        advanced = False
        try:
            while self.playing and self.playback_time >= 1 / FPS:
                self.playback_time -= 1 / FPS
                self._advance_one()
                advanced = True
            if advanced:
                self.draw_frame()
        except (GameError, ValueError) as exc:
            self._runtime_error(exc)
        return True
