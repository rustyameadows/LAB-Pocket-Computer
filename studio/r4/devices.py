"""Device inventory and live device sessions, independent of the local editor."""
import sqlite3

from r3.device_panel import DevicePanel, action
from ui import Gtk, box, button, label, pad, space


class DeviceManager(DevicePanel):
    def build(self):
        super().build()
        self.connection_card = self.selector.get_parent().get_parent()
        self.selector.set_visible(False)
        self.scan_button.set_visible(False)
        self.load_button.set_label("Load a local game…")
        self.load_detail.set_text("Choose a saved game to run in this device’s memory.")
        self.picker = None

        self.inventory = box(True, 14)
        self.body.get_parent().prepend(self.inventory)
        self.device_rows = {}
        self.groups = {}
        for kind, title in (("usb", "USB devices"), ("virtual", "Virtual devices")):
            card = box(True, 0, "inventory-card")
            self.inventory.append(card)
            head = box(spacing=8)
            card.append(head)
            head.append(label(title, "rail-title"))
            head.append(space())
            if kind == "usb":
                self.refresh_button = action("Rescan", self.scan)
                head.append(self.refresh_button)
            rows = box(True, 0)
            card.append(rows)
            self.groups[kind] = rows
        self.inventory_message = label("", "description", True)
        self.inventory.append(self.inventory_message)
        self.inventory_key = None

    def refresh_controls(self):
        super().refresh_controls()
        offline = self.state in ("offline", "scanning")
        self.inventory.set_visible(offline)
        self.connection_card.set_visible(not offline)
        self.body.set_visible(self.state == "online")
        self.refresh_button.set_sensitive(self.state == "offline")
        if self.state != "online" and self.picker:
            self.picker.close()
        self.inventory.set_sensitive(self.state == "offline")
        if offline:
            message = ""
            if self.state == "scanning":
                message = "Scanning USB ports…"
            elif getattr(self, "previous_state", None) in ("connecting", "disconnecting"):
                message = self.endpoint_detail.get_text()
            self.inventory_message.set_text(message)
            self.inventory_message.set_visible(bool(message))
            self.show_endpoints()
        self.previous_state = self.state

    def show_endpoints(self):
        endpoints = tuple((e.id, e.kind, e.name, e.detail) for e in self.endpoints)
        if self.inventory_key == endpoints:
            return
        self.inventory_key = endpoints
        self.device_rows.clear()
        for kind, rows in self.groups.items():
            while child := rows.get_first_child():
                rows.remove(child)
            entries = [e for e in self.endpoints if e.kind == kind]
            if not entries:
                empty = "No USB device found. Connect a Pocket and rescan." if kind == "usb" else "No virtual devices available."
                rows.append(pad(label(empty, "description", True), 0, 12))
            for endpoint in entries:
                row = pad(box(spacing=12), 0, 9)
                icon = "drive-removable-media-symbolic" if kind == "usb" else "computer-symbolic"
                row.append(Gtk.Image.new_from_icon_name(icon))
                names = box(True, 2)
                names.set_hexpand(True)
                row.append(names)
                names.append(label(endpoint.name, "device-name"))
                names.append(label(endpoint.detail, "description", True))
                connect = button("Connect", lambda e=endpoint: self.connect_endpoint(e.id))
                connect.update_property([Gtk.AccessibleProperty.LABEL], ["Connect to " + endpoint.name])
                row.append(connect)
                self.device_rows[endpoint.id] = connect
                rows.append(row)

    def connect_endpoint(self, ident):
        if self.state != "offline":
            return
        for index, endpoint in enumerate(self.endpoints):
            if endpoint.id == ident:
                self.selector.set_selected(index)
                self.toggle_connection()
                return

    def project_changed(self):
        self.load_button.set_sensitive(self.state == "online" and "load" in self.info.get("capabilities", ())
                                       and self.pending_actions == 0)

    def load_project(self):
        if self.state != "online" or "load" not in self.info.get("capabilities", ()):
            return
        if self.picker:
            self.picker.present()
            return
        try:
            projects = self.window.store.list_projects()
        except (OSError, ValueError, sqlite3.Error) as error:
            self.window.message(str(error), True)
            return
        dialog = Gtk.Window(transient_for=self.window, modal=True, title="Load a local game")
        self.picker = dialog
        generation = self.generation
        dialog.connect("close-request", self.close_picker)
        content = pad(box(True, 12, "dialog-content"), 18)
        dialog.set_child(content)
        content.append(label("Load a local game", "dialog-title"))
        content.append(label("Choose a saved game from this computer.", "description"))
        selector = Gtk.DropDown.new_from_strings([p["title"] for p in projects])
        selector.set_selected(Gtk.INVALID_LIST_POSITION)
        selector.update_property([Gtk.AccessibleProperty.LABEL], ["Local game to load"])
        content.append(selector)
        actions = box(spacing=8)
        actions.set_halign(Gtk.Align.END)
        content.append(actions)
        actions.append(button("Cancel", dialog.close))
        def load():
            index = selector.get_selected()
            if index >= len(projects) or self.state != "online" or self.generation != generation:
                return
            try:
                project = self.window.store.get_project(projects[index]["id"])
                self.command("load", project["source"], project["title"])
            except (OSError, ValueError, sqlite3.Error) as error:
                self.window.message(str(error), True)
            dialog.close()
        submit = button("Load into device memory", load, "primary-action")
        submit.set_sensitive(False)
        selector.connect("notify::selected", lambda *_: submit.set_sensitive(selector.get_selected() < len(projects)))
        actions.append(submit)
        dialog.present()

    def close_picker(self, *_):
        self.picker = None
        return False
