"""Searchable, offline help and local diagnostics."""
import platform
import sys
from gi.repository import Gtk
from ui import box, button, label, pad


GUIDES = (
    ("Connect a Pocket", "Open Devices and rescan. Choose your Pocket’s USB serial port, then Connect. "
     "A physical Pocket needs firmware that implements LAB Link. A virtual Pocket runs a separate game player and supports both panel sizes."),
    ("Recover a missing USB port", "Use a data-capable USB cable and close serial monitors that own the port. "
     "On Linux, check the device node’s permissions. Studio only opens the port you select. Rescan after reconnecting the cable."),
    ("Mirror and control a device", "Open Devices, connect, and read the reported panel size. The mirror shows the peer’s current framebuffer. "
     "Freeze the mirror to inspect or capture a frame. Use device controls to pause the game itself. Device commands depend on the capabilities reported at connection."),
    ("Choose a display profile", "Existing games draw at 160 × 160. A 480 × 480 Pocket displays each game pixel as a 3 × 3 square. "
     "The full-screen 720 × 720 profile alternates four and five panel pixels per logical pixel. Export a panel PNG to inspect the result at native size."),
    ("Record a playtest", "In Playtest, start recording from a reset game. Play a short sequence and stop recording. Replay starts from the recorded seed and inputs. "
     "Use frame stepping and the inspector to verify rules such as a line-clear bonus."),
    ("Recover a source draft", "Source changes are saved locally as drafts. Reopen Studio and select the same cartridge to continue editing. "
     "Save & run publishes a revision. If another client edited the game, Remix keeps your draft as a new cartridge."),
    ("Make a game with an agent", "The registered LAB MCP server shares this library. Ask your agent to make a game, playtest the scoring rule and open it in Studio. "
     "The MCP connection button includes a prompt you can copy."),
    ("Keyboard shortcuts", "Ctrl+K searches cartridges. Ctrl+F searches the current source file or opens library search. "
     "F1 opens Help. Ctrl+S saves and runs source. Space toggles playback in Playtest. A period steps one frame."),
)


class SupportPanel(Gtk.ScrolledWindow):
    def __init__(self, window):
        super().__init__(hexpand=True, vexpand=True)
        self.window = window
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.form = pad(box(True, 12, "r3-form"), 18, 15)
        self.set_child(self.form)
        self.search = Gtk.SearchEntry(placeholder_text="Search help")
        self.search.connect("search-changed", lambda *_: self.filter())
        self.form.append(self.search)
        self.rows = []
        for title, detail in GUIDES:
            section = Gtk.Expander(label=title)
            body = pad(label(detail, "description", True), 12, 8)
            section.set_child(body)
            self.form.append(section)
            self.rows.append((section, (title + " " + detail).casefold()))
        self.empty = label("No matching guides", "description")
        self.empty.set_visible(False)
        self.form.append(self.empty)
        self.form.append(Gtk.Separator())
        self.form.append(label("Studio diagnostics", "rail-title"))
        self.report = label("", "description", True)
        self.report.set_selectable(True)
        self.form.append(self.report)
        row = box(spacing=8)
        row.append(button("Refresh report", self.refresh))
        row.append(button("Copy report", self.copy))
        self.form.append(row)

    def filter(self):
        term = self.search.get_text().strip().casefold()
        for section, text in self.rows:
            section.set_visible(term in text)
        self.empty.set_visible(all(not section.get_visible() for section, _ in self.rows))

    def refresh(self):
        window = self.window
        project = window.project or {}
        device = getattr(window, "device_panel", None)
        connected = getattr(device, "connection_summary", None)
        details = [
            "LAB Studio r3 · " + platform.system() + " " + platform.machine(),
            f"GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()} · Python {sys.version.split()[0]}",
            f"Library · {len(window.store.list_projects())} cartridges",
            f"Selected · {project.get('title', '—')} · revision {project.get('revision', '—')}",
            "Pocket panels · 480 × 480 and 720 × 720",
        ]
        if isinstance(connected, str):
            details.append("Device · " + connected)
        self.report.set_text("\n".join(details))
        return self.report.get_text()

    def copy(self):
        self.window.get_clipboard().set(self.refresh())
        self.window.status_msg.set_text("Copied Studio diagnostics")
