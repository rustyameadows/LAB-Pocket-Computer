"""LAB Studio's application navigation. The local editor and device session are peers."""
import os
import sys
from pathlib import Path

from ui import (Gdk, Gio, Gtk, StudioWindow, box, button, cart_art, label, pad, space)
from r3.cartridge import CartridgePanel
from r3.main import Workbench
from r3.support import SupportPanel
from r3.workspace import DraftBook
from .devices import DeviceManager

APP_ID = "us.lab.PocketStudio.R4"


class HelpPanel(SupportPanel):
    def refresh(self):
        super().refresh()
        self.report.set_text(self.report.get_text().replace("LAB Studio r3", "LAB Studio r4", 1))
        return self.report.get_text()


class Studio(Workbench):
    def build_ui(self):
        self.draft_book = DraftBook(self.store.root)
        self.drafts.update(self.draft_book.all())
        # Build the existing editor with its Playtest and Source tabs.
        StudioWindow.build_ui(self)
        self.build_editor()
        self.build_navigation()

    def build_editor(self):
        self.metadata = CartridgePanel(self)
        mode = Gtk.ToggleButton(label="Cartridge")
        mode.set_group(self.tabs["play"])
        mode.add_css_class("mode-tab")
        mode.connect("toggled", self.change_mode, "settings")
        self.tabs["play"].get_parent().append(mode)
        self.tabs["settings"] = mode
        self.pages.add_named(self.metadata, "settings")

        source = self.pages.get_child_by_name("source")
        self.source_find = Gtk.SearchEntry(placeholder_text="Find in main.py", hexpand=True)
        self.source_find.connect("activate", lambda *_: self.find_next())
        self.find_bar = pad(box(spacing=6), 8, 4)
        self.find_bar.append(self.source_find)
        self.find_bar.append(button("Next", self.find_next))
        self.find_bar.append(button("Close", self.hide_find))
        source.insert_child_after(self.find_bar, source.get_first_child())
        self.find_bar.set_visible(False)
        self.shelf_scroll = self.library.get_ancestor(Gtk.ScrolledWindow)
        self.search = Gtk.SearchEntry(placeholder_text="Find a local game")
        self.search.set_size_request(135, -1)
        self.search.add_css_class("r3-search")
        self.search.connect("changed", lambda *_: self.apply_search())
        self.no_matches = pad(label("No games match", "shelf-caption", True), 14, 7)
        self.no_matches.set_visible(False)
        self.library.set_filter_func(self.filter_row)

    def build_navigation(self):
        root = self.get_child()
        shelf = root.get_first_child()
        shelf.set_size_request(236, -1)
        editor = root.get_last_child()
        root.remove(editor)
        self.section_pages = Gtk.Stack(hexpand=True, vexpand=True)
        self.section_pages.set_hhomogeneous(False)
        self.section_pages.set_vhomogeneous(False)
        root.append(self.section_pages)
        self.section_pages.add_named(editor, "local")
        self.device_panel = DeviceManager(self)
        self.support = HelpPanel(self)
        self.section_pages.add_named(self.workspace("Device Manager", self.device_panel, "devices"), "devices")
        self.section_pages.add_named(self.workspace("Help", self.support, "help"), "help")

        header = Gtk.HeaderBar()
        header.add_css_class("studio-header")
        header.set_title_widget(Gtk.Box())
        brand = box(spacing=9)
        brand.append(cart_art("logo", 30))
        brand.append(label("LAB Studio", "brand"))
        badge = label("r4", "version")
        badge.set_valign(Gtk.Align.CENTER)
        brand.append(badge)
        header.pack_start(brand)
        self.set_titlebar(header)

        count_row = shelf.get_first_child()
        footer = shelf.get_last_child()
        shelf.remove(count_row)
        shelf.remove(self.shelf_scroll)
        shelf.remove(footer)
        self.local_shelf = box(True, 0)
        self.local_shelf.set_vexpand(True)
        count_row.get_first_child().set_text("ON THIS COMPUTER")
        self.local_shelf.append(count_row)
        self.local_shelf.append(self.search)
        self.local_shelf.append(self.no_matches)
        self.local_shelf.append(self.shelf_scroll)
        local_actions = pad(box(True, 6), 12, 10)
        local_actions.append(button("New game", self.new_game, "new-cart", "list-add-symbolic"))
        local_actions.append(button("Import game", self.import_cartridge, "bridge-button", "document-open-symbolic"))
        self.local_shelf.append(local_actions)
        heading = self.remix_btn.get_parent()
        export = button("Export", self.export, "top-action", "document-save-as-symbolic")
        export.set_valign(Gtk.Align.START)
        heading.insert_child_after(export, self.remix_btn)
        self.export_btn = export

        self.section_buttons = {}
        nav = pad(box(True, 4, "app-nav"), 10, 12)
        shelf.append(nav)
        for name, title, icon in (("local", "Local Games", "applications-games-symbolic"),
                                  ("devices", "Device Manager", "computer-symbolic")):
            self.add_destination(nav, name, title, icon)
        shelf.append(Gtk.Separator())
        shelf.append(self.local_shelf)
        self.shelf_spacer = Gtk.Box(vexpand=True)
        shelf.append(self.shelf_spacer)
        utility = pad(box(True, 5), 10, 10)
        shelf.append(utility)
        self.add_destination(utility, "help", "Help", "help-browser-symbolic")
        utility.append(button("MCP connection", self.bridge, "bridge-button", "network-wired-symbolic"))
        self.section_buttons["local"].set_active(True)
        self.select_section("local")

    def workspace(self, title, child, section):
        page = pad(box(True, 12, "desk"), 23, 17)
        page.append(label(title, "game-name"))
        page.append(child)
        note = label("", "description", True)
        note.set_selectable(True)
        note.set_visible(False)
        page.append(note)
        if not hasattr(self, "workspace_messages"):
            self.workspace_messages = {}
        self.workspace_messages[section] = note
        return page

    def add_destination(self, parent, name, title, icon):
        tab = Gtk.ToggleButton()
        if self.section_buttons:
            tab.set_group(self.section_buttons["local"])
        tab.add_css_class("app-destination")
        row = box(spacing=10)
        row.append(Gtk.Image.new_from_icon_name(icon))
        row.append(label(title))
        tab.set_child(row)
        tab.update_property([Gtk.AccessibleProperty.LABEL], [title])
        self.section_buttons[name] = tab
        tab.connect("toggled", lambda control: self.select_section(name) if control.get_active() else None)
        parent.append(tab)

    def select_section(self, name):
        self.section_pages.set_visible_child_name(name)
        self.local_shelf.set_visible(name == "local")
        self.shelf_spacer.set_visible(name != "local")
        self.device_panel.on_visible(name == "devices")
        self.clear_keys()
        if name != "local":
            self.set_playing(False)
        if name == "help":
            self.support.refresh()
        self.context_heading()

    def change_mode(self, tab, mode):
        StudioWindow.change_mode(self, tab, mode)
        if tab.get_active() and mode != "play":
            self.set_playing(False)

    def context_heading(self):
        if not hasattr(self, "section_pages"):
            return
        section = self.section_pages.get_visible_child_name()
        title = {"devices": "Device Manager", "help": "Help"}.get(section)
        if title is None:
            title = self.project["title"] if self.project else "Local Games"
        self.set_title(title + " · LAB Studio")

    def poll(self):
        return StudioWindow.poll(self)

    def message(self, text, error=False):
        section = self.section_pages.get_visible_child_name() if hasattr(self, "section_pages") else "local"
        if section in ("devices", "help") and not getattr(self, "loading_local", False):
            note = self.workspace_messages[section]
            note.set_text(text)
            note.set_visible(True)
        else:
            super().message(text, error)

    def load(self, project, restore=True):
        self.loading_local = True
        try:
            super().load(project, restore)
        finally:
            self.loading_local = False

    def keyboard_down(self, controller, key, code, state):
        if key == Gdk.KEY_F1:
            self.section_buttons["help"].set_active(True)
            return True
        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and Gdk.keyval_to_lower(key) == Gdk.KEY_k:
            self.section_buttons["local"].set_active(True)
            self.search.grab_focus()
            return True
        if self.section_pages.get_visible_child_name() != "local":
            return False
        return super().keyboard_down(controller, key, code, state)


class StudioApp(Gtk.Application):
    def __init__(self):
        flags = Gio.ApplicationFlags.NON_UNIQUE if os.environ.get("LAB_STUDIO_ISOLATED") == "1" else Gio.ApplicationFlags.DEFAULT_FLAGS
        super().__init__(application_id=APP_ID, flags=flags | Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None

    def do_command_line(self, command_line):
        self.activate()
        if command_line.get_arguments()[1:] == ["local"]:
            self.window.section_buttons["local"].set_active(True)
        return 0

    def do_activate(self):
        if self.window is None:
            root = Path(__file__).resolve().parents[1]
            for path in (root / "studio.css", root / "r3/workbench.css", root / "r4/studio.css"):
                provider = Gtk.CssProvider()
                provider.load_from_path(str(path))
                Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.window = Studio(self)
        self.window.present()


def run(open_local=False):
    return StudioApp().run([sys.argv[0]] + (["local"] if open_local else []))
