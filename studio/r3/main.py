"""Native LAB Studio r3 workbench."""
import os
import sqlite3
import sys
from pathlib import Path
from gi.repository import Gio, GLib
from ui import Gdk, Gtk, StudioApp, StudioWindow, box, button, label, pad
from .cartridge import CartridgePanel
from .device_panel import DevicePanel
from .playtest_tools import PlaytestMixin
from .support import SupportPanel
from .workspace import DraftBook


class Workbench(PlaytestMixin, StudioWindow):
    def __init__(self, app):
        self.draft_delay = 0
        self.draft_book = None
        self.library_query = ""
        super().__init__(app)
        self.set_default_size(1190, 808)

    def build_ui(self):
        self.draft_book = DraftBook(self.store.root)
        self.drafts.update(self.draft_book.all())
        super().build_ui()
        header = self.get_titlebar()
        brand = self._find_label(header, "v0")
        if brand:
            brand.set_text("r3")

        # Insert discovery in the existing sidebar so search never changes the open game.
        self.shelf_scroll = self.library.get_ancestor(Gtk.ScrolledWindow)
        shelf = self.shelf_scroll.get_parent()
        self.search = Gtk.SearchEntry(placeholder_text="Find a cartridge")
        self.search.set_size_request(135, -1)
        self.search.set_hexpand(False)
        self.search.add_css_class("r3-search")
        self.search.connect("changed", lambda *_: self.apply_search())
        shelf.insert_child_after(self.search, self.shelf_scroll.get_prev_sibling())
        self.no_matches = pad(label("No cartridges match", "shelf-caption", True), 14, 7)
        shelf.insert_child_after(self.no_matches, self.search)
        self.no_matches.set_visible(False)
        self.library.set_filter_func(self.filter_row)

        modes = self.tabs["play"].get_parent()
        self.metadata = CartridgePanel(self)
        self.device_panel = DevicePanel(self)
        self.support = SupportPanel(self)
        for name, title, panel in (("settings", "Cartridge", self.metadata), ("devices", "Devices", self.device_panel),
                                   ("help", "Help", self.support)):
            tab = Gtk.ToggleButton(label=title)
            tab.set_group(self.tabs["play"])
            tab.add_css_class("mode-tab")
            tab.connect("toggled", self.change_mode, name)
            modes.append(tab)
            self.tabs[name] = tab
            self.pages.add_named(panel, name)

        self.source_find = Gtk.SearchEntry(placeholder_text="Find in main.py")
        self.source_find.update_property([Gtk.AccessibleProperty.LABEL], ["Find in main.py"])
        self.source_find.connect("activate", lambda *_: self.find_next())
        self.find_bar = pad(box(spacing=6), 8, 4)
        self.source_find.set_hexpand(True)
        self.find_bar.append(self.source_find)
        self.find_bar.append(button("Next", self.find_next))
        self.find_bar.append(button("Close", self.hide_find))
        source = self.pages.get_child_by_name("source")
        source.insert_child_after(self.find_bar, source.get_first_child())
        self.find_bar.set_visible(False)
        self.footer_context = self._find_label(self.get_child(), "POCKET SIMULATOR")

    @staticmethod
    def _find_label(root, text):
        if isinstance(root, Gtk.Label) and root.get_text() == text:
            return root
        child = root.get_first_child()
        while child:
            found = Workbench._find_label(child, text)
            if found:
                return found
            child = child.get_next_sibling()
        return None

    def filter_row(self, row):
        return self.library_query in getattr(row, "search_text", "")

    def list_rows(self, items):
        super().list_rows(items)
        row = self.library.get_first_child()
        for item in items:
            row.search_text = " ".join([item["title"], item["description"], item["template"]]).casefold()
            row = row.get_next_sibling()
        self.apply_search()

    def apply_search(self):
        self.library_query = self.search.get_text().strip().casefold()
        was = self.selecting
        self.selecting = True
        try:
            self.library.invalidate_filter()
            row = self.library.get_first_child()
            count = total = 0
            while row:
                total += 1
                count += int(self.filter_row(row))
                row = row.get_next_sibling()
            self.no_matches.set_visible(count == 0)
            self.cart_count.set_text(f"{count}/{total}" if self.library_query else f"{total:02d}")
            if self.project:
                self.select_row(self.project["id"])
        finally:
            self.selecting = was

    def source_changed(self, *args):
        super().source_changed(*args)
        if self.loading or not self.project:
            return
        if self.draft_delay:
            GLib.source_remove(self.draft_delay)
        self.draft_delay = GLib.timeout_add(350, self.persist_draft)

    def persist_draft(self):
        self.draft_delay = 0
        try:
            self.write_draft()
        except (OSError, sqlite3.Error) as error:
            self.message(f"Could not save the recovery draft. {error}", True)
        return False

    def write_draft(self):
        if self.project and self.dirty:
            self.draft_book.put(self.project["id"], self.source(), self.project["revision"])
        elif self.project:
            self.draft_book.remove(self.project["id"])

    def flush_draft(self):
        if self.draft_delay:
            GLib.source_remove(self.draft_delay)
            self.draft_delay = 0
            self.write_draft()

    def load(self, project, restore=True):
        self.flush_draft()
        if not restore:
            self.draft_book.remove(project["id"])
        super().load(project, restore)
        self.metadata.bind(project)
        if hasattr(self.device_panel, "project_changed"):
            self.device_panel.project_changed()
        self.context_heading()

    def change_mode(self, tab, mode):
        super().change_mode(tab, mode)
        if not tab.get_active() or not hasattr(self, "device_panel"):
            return
        if mode != "play":
            self.set_playing(False)
        self.device_panel.on_visible(mode == "devices")
        if mode == "help":
            self.support.refresh()
        self.context_heading()

    def context_heading(self):
        page = self.pages.get_visible_child_name()
        remote = page in ("devices", "help")
        if page == "devices":
            title, desc = "Devices", "Connect a Pocket, inspect its display and run a cartridge."
        elif page == "help":
            title, desc = "Studio help", "Setup guides, keyboard shortcuts and local diagnostics."
        elif self.project:
            title, desc = self.project["title"], self.project["description"]
        else:
            return
        self.game_title.set_text(title)
        self.description.set_text(desc)
        if page == "devices":
            self.status_msg.set_text(self.device_panel.connection_summary)
        elif page == "help":
            self.status_msg.set_text("Offline guides and diagnostics")
        elif page == "settings":
            self.status_msg.set_text("Edit cartridge details and control descriptions")
        self.remix_btn.set_visible(not remote)
        self.rev_note.set_visible(not remote)
        if getattr(self, "footer_context", None):
            self.footer_context.set_text({"devices": "DEVICE WORKSPACE", "help": "STUDIO SUPPORT",
                                         "settings": "CARTRIDGE DETAILS", "source": "SOURCE EDITOR"}.get(page, "POCKET SIMULATOR"))

    def poll(self):
        result = super().poll()
        if hasattr(self, "device_panel") and self.pages.get_visible_child_name() == "devices":
            self.status_msg.set_text(self.device_panel.connection_summary)
        return result

    def choose_row(self, widget, row):
        selecting = not self.selecting and row and (not self.project or row.project_id != self.project["id"])
        super().choose_row(widget, row)
        if selecting and self.pages.get_visible_child_name() == "help":
            self.tabs["play"].set_active(True)

    def hide_find(self):
        self.find_bar.set_visible(False)
        self.editor.grab_focus()

    def find_next(self):
        query = self.source_find.get_text()
        if not query:
            return
        text = self.source()
        end = self.buffer.get_iter_at_mark(self.buffer.get_insert()).get_offset()
        index = text.find(query, end)
        if index < 0:
            index = text.find(query)
        if index < 0:
            self.status_msg.set_text("No source match")
            return
        start_iter = self.buffer.get_iter_at_offset(index)
        end_iter = self.buffer.get_iter_at_offset(index + len(query))
        self.buffer.select_range(end_iter, start_iter)
        self.editor.scroll_to_iter(start_iter, .15, False, 0, 0)
        self.status_msg.set_text(f"Source match on line {start_iter.get_line()+1}")

    def keyboard_down(self, controller, key, code, state):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        page = self.pages.get_visible_child_name()
        key_lower = Gdk.keyval_to_lower(key)
        if key == Gdk.KEY_F1:
            self.tabs["help"].set_active(True)
            return True
        if ctrl and key_lower in (Gdk.KEY_k, Gdk.KEY_f):
            if key_lower == Gdk.KEY_f and page == "source":
                self.find_bar.set_visible(True)
                self.source_find.grab_focus()
            else:
                self.search.grab_focus()
            return True
        focus = self.get_focus()
        if focus and (isinstance(focus, Gtk.Editable) or focus.get_ancestor(Gtk.SearchEntry) is not None):
            if key == Gdk.KEY_Escape:
                if self.find_bar.get_visible():
                    self.hide_find()
                else:
                    self.search.set_text("")
                    self.tabs[page].grab_focus()
                return True
            return False
        if ctrl and key_lower == Gdk.KEY_s and page != "source":
            return False
        if page == "play" and key == Gdk.KEY_period:
            self.step_once()
            return True
        return super().keyboard_down(controller, key, code, state)

    def on_close(self, *args):
        try:
            self.flush_draft()
            self.write_draft()
        except (sqlite3.Error, OSError) as error:
            self.message(f"Could not keep your source draft. {error}", True)
            return True
        self.skip_close_confirm = True
        self.device_panel.shutdown()
        return super().on_close(*args)


class ReleaseApp(StudioApp):
    def __init__(self):
        flags = Gio.ApplicationFlags.NON_UNIQUE if os.environ.get("LAB_STUDIO_ISOLATED") == "1" else Gio.ApplicationFlags.DEFAULT_FLAGS
        Gtk.Application.__init__(self, application_id="us.lab.PocketStudio.R3", flags=flags)
        self.window = None

    def do_activate(self):
        if self.window is None:
            here = Path(__file__).resolve().parent
            for css in (here.parent / "studio.css", here / "workbench.css"):
                provider = Gtk.CssProvider()
                provider.load_from_path(str(css))
                Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.window = Workbench(self)
        self.window.present()


def run():
    return ReleaseApp().run([sys.argv[0]])
