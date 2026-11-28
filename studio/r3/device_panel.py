"""GTK device console. All serial operations run on a single worker thread."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import re

from gi.repository import Gdk, Gio, GLib, Gsk, Gtk, Pango
from pocket_keys import BOARD
from ui import CAPS, box, label, pad, rectangle, rgba, space, texture

from .device_link import DeviceError, DeviceLink, discover


class DeviceScreen(Gtk.Widget):
    def __init__(self):
        super().__init__(hexpand=True, vexpand=True)
        self.set_size_request(150, 210)
        self.surface = None
        self.background = rgba("#dce5dd")
        self.dot = rgba("#bacbbd")
        self.edge = rgba("#3b5147")

    def set_image(self, image):
        self.surface = texture(image) if image is not None else None
        self.queue_draw()

    def do_snapshot(self, snapshot):
        w, h = self.get_width(), self.get_height()
        if w < 1 or h < 1:
            return
        bounds = rectangle(0, 0, w, h)
        snapshot.append_color(self.background, bounds)
        snapshot.push_repeat(bounds, rectangle(0, 0, 12, 12))
        snapshot.append_color(self.dot, rectangle(4, 4, 1, 1))
        snapshot.pop()
        if self.surface:
            side = min(w - 24, h - 18)
            if side > 0:
                x, y = (w - side) // 2, (h - side) // 2
                snapshot.append_color(self.edge, rectangle(x - 3, y - 3, side + 6, side + 6))
                snapshot.append_scaled_texture(self.surface, Gsk.ScalingFilter.NEAREST,
                                               rectangle(x, y, side, side))


def action(title, callback, css="secondary-action", tooltip=None):
    item = Gtk.Button(label=title)
    item.add_css_class(css)
    item.connect("clicked", lambda *_: callback())
    if tooltip:
        item.set_tooltip_text(tooltip)
    return item


class DevicePanel(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
        self.window = window
        self.add_css_class("device-panel")
        self.css = Gtk.CssProvider()
        self.css.load_from_path(str(Path(__file__).with_name("device-panel.css")))
        Gtk.StyleContext.add_provider_for_display(self.get_display(), self.css,
                                                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)
        self.led_css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(self.get_display(), self.led_css,
                                                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 3)
        self.led_colors = {}
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="PocketLink")
        self.link = None  # Used only on the worker.
        self.endpoints = []
        self.state = "offline"
        self.info = {}
        self.frozen = False
        self.visible_page = False
        self.closed = False
        self.pending_frame = False
        self.pending_actions = 0
        self.generation = 0
        self.current_frame = None
        self.log_entries = deque(maxlen=18)
        self.build()
        self.refresh_controls()
        self.timer = GLib.timeout_add(120, self._pulse)

    def build(self):
        scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroll)
        content = box(True, 10)
        content.set_vexpand(True)
        scroll.set_child(content)

        connection = pad(box(True, 7, "device-card"), 0, 0)
        content.append(connection)
        top = box(spacing=8)
        connection.append(top)
        top.append(label("Connection", "rail-title"))
        top.append(space())
        self.link_status = label("Offline", "device-status")
        top.append(self.link_status)
        choices = box(spacing=5)
        connection.append(choices)
        self.selector = Gtk.DropDown.new_from_strings([])
        self.selector.set_hexpand(True)
        self.selector.set_tooltip_text("Choose a Virtual Pocket or a discovered USB serial port")
        choices.append(self.selector)
        self.scan_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.scan_button.set_tooltip_text("Rescan for USB devices")
        self.scan_button.update_property([Gtk.AccessibleProperty.LABEL], ["Rescan for USB devices"])
        self.scan_button.connect("clicked", lambda *_: self.scan())
        self.scan_button.add_css_class("secondary-action")
        choices.append(self.scan_button)
        self.connect_button = action("Connect", self.toggle_connection, "primary-action")
        choices.append(self.connect_button)
        self.endpoint_detail = label("Choose a device to open its link.", "description", True)
        connection.append(self.endpoint_detail)
        self.selector.connect("notify::selected", lambda *_: self._selection_changed())

        self.body = box(spacing=10)
        self.body.set_vexpand(True)
        content.append(self.body)
        stage = box(True, 0, "stage")
        stage.set_hexpand(True)
        stage.set_vexpand(True)
        self.body.append(stage)
        title = pad(box(spacing=6, css="stage-head"), 10, 6)
        stage.append(title)
        mirror_heading = label("DEVICE MIRROR", "stage-tag")
        mirror_heading.set_ellipsize(Pango.EllipsizeMode.NONE)
        mirror_heading.set_hexpand(True)
        title.append(mirror_heading)
        self.panel_size = label("—", "caption")
        title.append(self.panel_size)
        overlay = Gtk.Overlay(vexpand=True)
        stage.append(overlay)
        self.screen = DeviceScreen()
        overlay.set_child(self.screen)
        self.idle_card = pad(box(True, 6, "device-empty"), 0)
        self.idle_card.set_halign(Gtk.Align.CENTER)
        self.idle_card.set_valign(Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name("video-display-symbolic")
        icon.set_pixel_size(27)
        self.idle_card.append(icon)
        self.idle_title = label("Waiting for a device", "rail-title")
        self.idle_title.set_xalign(.5)
        self.idle_card.append(self.idle_title)
        overlay.add_overlay(self.idle_card)
        meta = pad(box(spacing=5, css="stage-foot"), 8, 5)
        stage.append(meta)
        self.freeze_button = action("Freeze", self.toggle_freeze, tooltip="Hold the displayed frame while the Pocket continues")
        self.capture_button = action("Save PNG", self.save_png, tooltip="Save the displayed physical-resolution frame")
        meta.append(self.freeze_button)
        meta.append(self.capture_button)
        meta.append(space())
        self.tick_label = label("", "caption")
        meta.append(self.tick_label)

        control = box(True, 7, "device-card")
        self.body.append(control)
        control.append(label("Device controls", "rail-title"))
        self.game_label = label("No cartridge connected", "description", True)
        control.append(self.game_label)
        transport = box(spacing=3)
        control.append(transport)
        self.control_buttons = {}
        for command, caption in [("play", "Play"), ("pause", "Pause"), ("reset", "Reset")]:
            item = action(caption, lambda cmd=command: self.command("control", cmd), "device-transport")
            transport.append(item)
            self.control_buttons[command] = item
        control.append(Gtk.Separator())
        key_title = label("Pocket keypad", "stage-tag")
        key_title.set_ellipsize(Pango.EllipsizeMode.NONE)
        self.key_grid = Gtk.Grid(column_homogeneous=True, row_homogeneous=True,
                                 row_spacing=3, column_spacing=3)
        control.append(key_title)
        control.append(self.key_grid)
        self.key_buttons = {}
        for number in range(1, 21):
            key_id = f"key{number:02}"
            key = BOARD.get(number)
            cap = action(CAPS.get(key, f"{number:02}"), lambda name=key_id: self.command("tap", name), "keycap")
            cap.set_name(f"link-{key_id}")
            cap.set_tooltip_text(f"Tap key {number:02}" + (f" · {key}" if key else ""))
            cap.update_property([Gtk.AccessibleProperty.LABEL], [f"Device key {number:02}" + (f" {key}" if key else "")])
            if key:
                cap.add_css_class("mapped")
            self.key_grid.attach(cap, (number-1) % 5, (number-1) // 5, 1, 1)
            self.key_buttons[key_id] = cap
        control.append(Gtk.Separator())
        self.load_button = action("Load selected game", self.load_project, "secondary-action")
        control.append(self.load_button)
        self.load_detail = label("Select a cartridge in the library.", "caption", True)
        control.append(self.load_detail)

        self.details = Gtk.Expander(label="Device details & connection log")
        self.details.add_css_class("device-details")
        content.append(self.details)
        details = box(True, 7)
        self.details.set_child(details)
        self.identity = label("Connect a Pocket to read its firmware and capabilities.", "description", True)
        self.identity.set_selectable(True)
        details.append(self.identity)
        self.log_label = label("", "device-log", True)
        self.log_label.set_selectable(True)
        details.append(self.log_label)
        help_text = label("USB setup · Use a data-capable cable and a Pocket running the LAB device bridge. "
                          "Select its serial port, then Connect. If access is denied, check your serial-port permissions.",
                          "description", True)
        details.append(help_text)

    def _selection_changed(self):
        pos = self.selector.get_selected()
        if self.state != "offline" or pos >= len(self.endpoints):
            return
        endpoint = self.endpoints[pos]
        self.endpoint_detail.set_text(endpoint.detail)

    def _log(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_entries.append(f"{now}   {text}")
        self.log_label.set_text("\n".join(self.log_entries))

    def _run(self, work, finished):
        if self.closed:
            return
        future = self.executor.submit(work)
        def handle(_future):
            try:
                result, error = _future.result(), None
            except Exception as exc:
                result, error = None, str(exc) or type(exc).__name__
            def deliver():
                if not self.closed:
                    finished(result, error)
                return GLib.SOURCE_REMOVE
            GLib.idle_add(deliver)
        future.add_done_callback(handle)

    def scan(self):
        if self.state != "offline":
            return
        pos = self.selector.get_selected()
        old = self.endpoints[pos].id if pos < len(self.endpoints) else None
        self.state = "scanning"
        self.refresh_controls()
        def done(endpoints, error):
            self.state = "offline"
            if error:
                self._log(error)
                self.endpoint_detail.set_text(error)
            else:
                self.endpoints = endpoints
                self.selector.set_model(Gtk.StringList.new([e.name for e in endpoints]))
                new_pos = next((i for i, e in enumerate(endpoints) if old and e.id == old), 0)
                self.selector.set_selected(new_pos)
                self._selection_changed()
                usb = sum(e.kind == "usb" for e in endpoints)
                self._log(f"Found {usb} USB serial port" + ("" if usb == 1 else "s") + ".")
            self.refresh_controls()
        self._run(discover, done)

    def toggle_connection(self):
        if self.state == "online":
            self.disconnect()
            return
        pos = self.selector.get_selected()
        if self.state != "offline" or pos >= len(self.endpoints):
            return
        endpoint = self.endpoints[pos]
        self.state = "connecting"
        self.generation += 1
        self.endpoint_detail.set_text(f"Opening {endpoint.name}…")
        self._log(f"Connecting to {endpoint.name}.")
        self.refresh_controls()
        def connect():
            self.link = DeviceLink.open(endpoint)
            return self.link.info.copy()
        def done(info, error):
            if error:
                self.state = "offline"
                self.endpoint_detail.set_text(error)
                self._log(error)
            else:
                self.state = "online"
                self.info = info
                caps = ", ".join(sorted(info["capabilities"]))
                model = info["model"]
                peer_name = info["name"]
                self.endpoint_detail.set_text(f"{peer_name} · {model}")
                canvas = f"{info['logical_width']} × {info['logical_height']}"
                self.identity.set_text(f"Firmware {info['firmware']}  ·  {model}\n"
                                       f"Physical panel {info['width']} × {info['height']}  ·  Game canvas {canvas}\n"
                                       f"Capabilities · {caps}")
                self.panel_size.set_text(f"{info['width']} × {info['height']} px")
                self._log(f"{peer_name} connected over {endpoint.kind.upper()}.")
                self.idle_title.set_text("Receiving display…" if "mirror" in info["capabilities"] else "Mirror unavailable")
                self.poll_frame()
            self.refresh_controls()
        self._run(connect, done)

    def _close_link(self):
        link, self.link = self.link, None
        if link is not None:
            link.close()

    def disconnect(self, reason=None):
        if self.state != "online":
            return
        self.generation += 1
        self.state = "disconnecting"
        self.refresh_controls()
        def done(_unused, error):
            self.info = {}
            self.state = "offline"
            self.frozen = False
            self.current_frame = None
            self.screen.set_image(None)
            self.idle_card.set_visible(True)
            self.idle_title.set_text("Waiting for a device")
            self.panel_size.set_text("—")
            self.game_label.set_text("No cartridge connected")
            self.tick_label.set_text("")
            self.identity.set_text("Connect a Pocket to read its firmware and capabilities.")
            for item in self.key_buttons.values():
                item.remove_css_class("lit")
            self.led_css.load_from_string("")
            self.led_colors = {}
            self._selection_changed()
            message = reason or error or "Disconnected."
            self._log(message)
            if reason or error:
                self.endpoint_detail.set_text(message)
            self.refresh_controls()
        self._run(self._close_link, done)

    def refresh_controls(self):
        online = self.state == "online"
        self.link_status.set_text({"online": "Connected", "offline": "Offline", "scanning": "Scanning…",
                                   "connecting": "Connecting…", "disconnecting": "Closing…"}[self.state])
        if online:
            self.link_status.add_css_class("online")
        else:
            self.link_status.remove_css_class("online")
        self.selector.set_sensitive(self.state == "offline" and bool(self.endpoints))
        self.scan_button.set_sensitive(self.state == "offline")
        self.connect_button.set_label("Disconnect" if online or self.state == "disconnecting" else "Connect")
        self.connect_button.set_sensitive(online or (self.state == "offline" and bool(self.endpoints)))
        available = set(self.info.get("capabilities", ())) if online else set()
        for item in self.control_buttons.values():
            item.set_sensitive("control" in available)
        self.key_grid.set_sensitive("input" in available)
        self.freeze_button.set_label("Resume mirror" if self.frozen else "Freeze")
        self.freeze_button.set_sensitive("mirror" in available and self.current_frame is not None)
        self.capture_button.set_sensitive(self.current_frame is not None and online)
        self.project_changed()

    def project_changed(self):
        project = getattr(self.window, "project", None)
        allowed = self.state == "online" and "load" in self.info.get("capabilities", ())
        self.load_button.set_sensitive(bool(project) and allowed and not self.pending_actions)
        self.load_detail.set_text(f"Saved cartridge · {project['title']}" if project else "Select a cartridge in the library.")

    @property
    def connection_summary(self):
        if self.state == "online":
            return f"{self.info['name']} · {self.info['width']} × {self.info['height']} · {self.info['firmware']}"
        return self.link_status.get_text()

    def on_visible(self, visible):
        self.visible_page = bool(visible)
        if self.visible_page:
            self.project_changed()
            if not self.endpoints and self.state == "offline":
                self.scan()
            self._resize()
            self.poll_frame()

    def _resize(self):
        width = self.get_width()
        if width:
            self.body.set_orientation(Gtk.Orientation.VERTICAL if width < 500 else Gtk.Orientation.HORIZONTAL)

    def _pulse(self):
        if self.closed:
            return GLib.SOURCE_REMOVE
        if self.visible_page:
            self._resize()
            self.poll_frame()
        return GLib.SOURCE_CONTINUE

    def poll_frame(self):
        if (self.state != "online" or self.pending_frame or self.frozen or not self.visible_page
                or "mirror" not in self.info.get("capabilities", ())):
            return
        self.pending_frame = True
        generation = self.generation
        def done(frame, error):
            self.pending_frame = False
            if generation != self.generation or self.state != "online":
                return
            if error:
                self.disconnect(f"Device link lost · {error}")
                return
            if self.frozen or not self.visible_page:
                return
            first = self.current_frame is None
            self.current_frame = frame
            self.screen.set_image(frame.image)
            self.idle_card.set_visible(False)
            run = "Playing" if frame.running else "Paused"
            self.game_label.set_text(f"{frame.title} · {run} · Score {frame.score}")
            self.tick_label.set_text(f"Tick {frame.tick}")
            self.panel_size.set_text(f"{frame.image.width} × {frame.image.height} px")
            if frame.keys != self.led_colors:
                self.led_colors = dict(frame.keys)
                rules = [f"button#link-{key} {{ box-shadow: inset 0 -4px {color}; }}"
                         for key, color in frame.keys.items() if key in self.key_buttons]
                self.led_css.load_from_string("\n".join(rules))
            for name, item in self.key_buttons.items():
                color = frame.keys.get(name)
                if color and color.lower() not in ("#000", "#000000"):
                    item.add_css_class("lit")
                else:
                    item.remove_css_class("lit")
            if first:
                self.refresh_controls()
        self._run(lambda: self.link.frame(), done)

    def command(self, method, *args):
        required = {"control": "control", "tap": "input", "load": "load"}[method]
        if self.state != "online" or required not in self.info.get("capabilities", ()):
            return
        if self.pending_actions >= 5:
            return
        generation = self.generation
        self.pending_actions += 1
        self.project_changed()
        def send():
            try:
                getattr(self.link, method)(*args)
            except DeviceError as exc:
                return str(exc), self.link.fd is None
            return None, False
        def done(outcome, error):
            self.pending_actions -= 1
            if generation != self.generation:
                return
            rejected, lost = outcome or (None, False)
            error = error or rejected
            if lost:
                self.disconnect(f"Device link lost · {error}")
                return
            if error:
                self._log(error)
                self.endpoint_detail.set_text(error)
            else:
                if method == "load":
                    self._log(f"Loaded {args[1]} into device memory.")
                elif method == "control":
                    self._log(f"Device command · {args[0]}")
                self.poll_frame()
            self.project_changed()
        self._run(send, done)

    def load_project(self):
        project = getattr(self.window, "project", None)
        if project:
            self.command("load", project["source"], project["title"])

    def toggle_freeze(self):
        if self.current_frame is None or self.state != "online":
            return
        self.frozen = not self.frozen
        self.freeze_button.set_label("Resume mirror" if self.frozen else "Freeze")
        if self.frozen:
            self.tick_label.set_text(f"Held · {self.current_frame.tick}")
        else:
            self.poll_frame()

    def save_png(self):
        if self.current_frame is None:
            return
        frame = self.current_frame
        dialog = Gtk.FileDialog(title="Save device mirror")
        stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", frame.title).strip("-")[:60] or "pocket"
        dialog.set_initial_name(f"{stem}-tick-{frame.tick}.png")
        allowed = Gtk.FileFilter()
        allowed.set_name("PNG image")
        allowed.add_suffix("png")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(allowed)
        dialog.set_filters(filters)
        def chosen(chooser, result):
            try:
                path = chooser.save_finish(result).get_path()
                if not path:
                    raise ValueError("Choose a local folder to save the PNG.")
                frame.image.save(path, format="PNG")
                self._log(f"Saved {frame.image.width} × {frame.image.height} PNG · {path}")
                self.window.message(f"Saved device mirror to {path}")
            except GLib.Error as exc:
                if not exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self.window.message(str(exc), True)
            except (ValueError, OSError) as exc:
                self.window.message(str(exc), True)
        dialog.save(self.window, None, chosen)

    def shutdown(self):
        if self.closed:
            return
        self.closed = True
        GLib.source_remove(self.timer)
        self.executor.submit(self._close_link)
        self.executor.shutdown(wait=False)
        Gtk.StyleContext.remove_provider_for_display(self.get_display(), self.css)
        Gtk.StyleContext.remove_provider_for_display(self.get_display(), self.led_css)
