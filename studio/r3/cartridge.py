"""Edit cartridge metadata and control legends while preserving the current source."""
import sqlite3
from gi.repository import Gtk
from studio_store import RevisionConflict
from ui import ACTION_KEYS, box, button, label, pad


class CartridgePanel(Gtk.ScrolledWindow):
    def __init__(self, window):
        super().__init__(hexpand=True, vexpand=True)
        self.window = window
        self.project = None
        self.revision = None
        self.fields = {}
        self.pending = {}
        self.saved_fields = None
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        form = pad(box(True, 10, "r3-form"), 18, 15)
        self.set_child(form)
        form.append(label("Cartridge details", "rail-title"))
        self.title = self.field(form, "Title", 80)
        self.about = self.field(form, "Description", 1000)
        form.append(Gtk.Separator())
        form.append(label("Control guide", "rail-title"))
        form.append(label("Describe what each button does in this game. Blank actions are hidden from its guide.", "description", True))
        self.grid = Gtk.Grid(column_spacing=10, row_spacing=6)
        form.append(self.grid)
        actions = box(spacing=8)
        form.append(actions)
        self.status = label("", "description", True)
        self.status.set_hexpand(True)
        actions.append(self.status)
        actions.append(button("Revert fields", self.revert))
        actions.append(button("Save details", self.save, "primary-action"))

    @staticmethod
    def field(form, name, limit):
        form.append(label(name, "file-label"))
        field = Gtk.Entry(max_length=limit, hexpand=True)
        field.update_property([Gtk.AccessibleProperty.LABEL], [name])
        form.append(field)
        return field

    def revert(self):
        if self.window.project:
            self.pending.pop(self.project, None)
            self.bind(self.window.store.get_project(self.window.project["id"]), force=True)

    def values(self):
        return (self.title.get_text(), self.about.get_text(),
                {action: field.get_text() for action, field in self.fields.items() if field.get_text()})

    def bind(self, project, force=False):
        if self.project and not force:
            if self.values() != self.saved_fields:
                self.pending[self.project] = (self.values(), self.revision, self.saved_fields)
            else:
                self.pending.pop(self.project, None)
        self.project = project["id"]
        latest = (project["title"], project["description"], project["controls"])
        values, self.revision, self.saved_fields = self.pending.get(self.project, (latest, project["revision"], latest))
        title, description, controls = values
        self.title.set_text(title)
        self.about.set_text(description)
        self.status.set_text("Another client changed this cartridge. Revert fields to load that revision."
                             if project["revision"] != self.revision else "")
        while child := self.grid.get_first_child():
            self.grid.remove(child)
        self.fields = {}
        actions = list(dict.fromkeys([*ACTION_KEYS, *project["controls"], *controls]))
        for index, action in enumerate(actions):
            name = f"{action.upper()}  ·  {ACTION_KEYS[action]}" if action in ACTION_KEYS else action
            self.grid.attach(label(name, "file-label"), 0, index, 1, 1)
            field = Gtk.Entry(hexpand=True, max_length=160)
            field.set_text(controls.get(action, ""))
            field.update_property([Gtk.AccessibleProperty.LABEL], [action + " control description"])
            self.grid.attach(field, 1, index, 1, 1)
            self.fields[action] = field

    def save(self):
        window = self.window
        try:
            current = window.store.get_project(self.project)
            if window.dirty:
                self.status.set_text("Save or remix your source draft before editing cartridge details.")
                return
            controls = {key: field.get_text().strip() for key, field in self.fields.items() if field.get_text().strip()}
            updated = window.store.update_project(self.project, current["source"], self.revision,
                                                  title=self.title.get_text(), description=self.about.get_text(),
                                                  controls=controls)
        except RevisionConflict:
            self.status.set_text("Another client changed this cartridge. Revert fields to load that revision.")
            return
        except (ValueError, OSError, sqlite3.Error) as error:
            self.status.set_text(str(error))
            return
        self.pending.pop(self.project, None)
        self.bind(updated, force=True)
        window.load(updated)
        self.status.set_text("Details saved to revision " + str(updated["revision"]))
