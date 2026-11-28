"""Shared on-disk studio library. Each writer commits one SQLite transaction."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import uuid
import zlib
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED, ZIP_STORED, ZipInfo

from engine import ACTIONS, Game

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"
MAX_SOURCE_BYTES = 48 * 1024
MAX_MANIFEST_BYTES = 32 * 1024


class StoreError(ValueError):
    """An invalid project, template, edit, or package."""


class RevisionConflict(StoreError):
    """Another Studio client saved after this client read the project."""


def _text(value, label, limit, *, empty=False):
    if not isinstance(value, str) or "\0" in value:
        raise StoreError(f"{label} must be text.")
    value = value.strip()
    if (not value and not empty) or len(value) > limit:
        raise StoreError(f"{label} must be {'0' if empty else '1'}–{limit} characters.")
    return value


def _controls(mapping):
    if not isinstance(mapping, dict) or not set(mapping) <= ACTIONS:
        raise StoreError("Controls must map supported action names to short descriptions.")
    return {key: _text(label, "Control description", 160) for key, label in mapping.items()}


def check_source_text(value):
    if not isinstance(value, str) or not value.strip() or "\0" in value:
        raise StoreError("Game source must contain Python text.")
    if len(value.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise StoreError(f"Game source exceeds {MAX_SOURCE_BYTES} UTF-8 bytes.")


def _check_source(value):
    check_source_text(value)
    game = Game(value, seed=1)
    game.step(())


def _summarize(record):
    return {key: value for key, value in record.items() if key != "source"}


def _decode(row):
    record = dict(row)
    record["controls"] = json.loads(record["controls"])
    return record


class Store:
    def __init__(self, root=None):
        custom_home = root or os.environ.get("LAB_STUDIO_HOME")
        xdg = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
        self.root = Path(custom_home or Path(xdg) / "lab-studio").expanduser().resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.database = self.root / "studio.sqlite3"
        self.templates = {}
        for directory in sorted(SAMPLES_DIR.iterdir()):
            if not directory.is_dir() or not (directory / "manifest.json").is_file():
                continue
            data = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            slug = directory.name
            self.templates[slug] = {
                "id": slug, "title": _text(data["title"], "Title", 80),
                "description": _text(data["description"], "Description", 1000, empty=True),
                "controls": _controls(data["controls"]), "template": slug,
                "accent": data.get("accent", "#92d547"),
                "source": (directory / "main.py").read_text(encoding="utf-8"),
            }
        if "falling-blocks" not in self.templates:
            raise StoreError("The bundled falling-blocks sample is missing.")
        with self._db(write=True) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
                template TEXT NOT NULL, controls TEXT NOT NULL, accent TEXT NOT NULL,
                source TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS workspace (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                active_id TEXT NOT NULL, library_version INTEGER NOT NULL
            )""")
            for sample in self.templates.values():
                inserted = self._insert(db, sample, ignore_existing=True)
                if inserted:
                    db.execute("UPDATE workspace SET library_version=library_version+1")
            db.execute("""INSERT OR IGNORE INTO workspace VALUES (1,'falling-blocks',1)""")

    @contextmanager
    def _db(self, *, write=False):
        db = sqlite3.connect(self.database, timeout=8, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            if write:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _insert(db, project, *, ignore_existing=False):
        controls = json.dumps(project["controls"], ensure_ascii=False)
        sql = """INSERT INTO projects (id, title, description, template, accent, controls, source)
                 VALUES (:id, :title, :description, :template, :accent, :controls, :source)"""
        if ignore_existing:
            sql += " ON CONFLICT(id) DO NOTHING"
        cursor = db.execute(sql, dict(project, controls=controls))
        return cursor.rowcount

    @staticmethod
    def _fetch(db, project_id):
        if not isinstance(project_id, str):
            raise StoreError("Project id must be text.")
        row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            raise StoreError(f"Unknown project {project_id!r}.")
        return _decode(row)

    def list_templates(self):
        return [_summarize(dict(template, revision=1)) for template in self.templates.values()]

    def list_projects(self):
        with self._db() as db:
            rows = db.execute("""SELECT id,title,description,template,controls,accent,revision
                                 FROM projects ORDER BY CASE id WHEN 'falling-blocks' THEN 0
                                 WHEN 'snake' THEN 1 WHEN 'breakout' THEN 2 ELSE 3 END,
                                 rowid""")
            return [_decode(row) for row in rows]

    def get_project(self, project_id):
        with self._db() as db:
            return self._fetch(db, project_id)

    def workspace_status(self):
        with self._db() as db:
            return dict(db.execute("""SELECT active_id, revision, library_version FROM workspace
                                      JOIN projects ON projects.id=workspace.active_id
                                      WHERE singleton=1""").fetchone())

    def get_active(self):
        return self.workspace_status()["active_id"]

    def set_active(self, project_id):
        with self._db(write=True) as db:
            self._fetch(db, project_id)
            db.execute("UPDATE workspace SET active_id=? WHERE singleton=1", (project_id,))

    def _add_and_open(self, db, project, title, description=None):
        title = _text(title, "Title", 80)
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "game"
        result = dict(project, id=f"{slug}-{uuid.uuid4().hex[:12]}", title=title, revision=1)
        if description is not None:
            result["description"] = _text(description, "Description", 1000, empty=True)
        self._insert(db, result)
        db.execute("UPDATE workspace SET active_id=?, library_version=library_version+1",
                   (result["id"],))
        return result

    def create_project(self, title, template="falling-blocks", description=None, *, source=None, controls=None):
        if not isinstance(template, str) or template not in self.templates:
            raise StoreError(f"Unknown template. Choose from {', '.join(sorted(self.templates))}.")
        project = dict(self.templates[template])
        if source is not None:
            _check_source(source)
            project["source"] = source
        if controls is not None:
            project["controls"] = _controls(controls)
        with self._db(write=True) as db:
            return self._add_and_open(db, project, title, description)

    def duplicate_project(self, project_id, title):
        with self._db(write=True) as db:
            return self._add_and_open(db, self._fetch(db, project_id), title)

    def update_project(self, project_id, source, expected_revision, *, title=None,
                       description=None, controls=None):
        if type(expected_revision) is not int or expected_revision < 1:
            raise StoreError("expected_revision must be a positive integer.")
        _check_source(source)
        with self._db(write=True) as db:
            project = self._fetch(db, project_id)
            if project["revision"] != expected_revision:
                raise RevisionConflict(
                    f"Stale revision {expected_revision}; project is now revision "
                    f"{project['revision']}. Read the project and merge your changes."
                )
            new_title = project["title"] if title is None else _text(title, "Title", 80)
            new_desc = project["description"] if description is None else _text(
                description, "Description", 1000, empty=True)
            new_controls = project["controls"] if controls is None else _controls(controls)
            db.execute("""UPDATE projects SET source=?, title=?, description=?, controls=?,
                          revision=revision+1 WHERE id=?""",
                       (source, new_title, new_desc, json.dumps(new_controls), project_id))
            db.execute("UPDATE workspace SET library_version=library_version+1")
            return self._fetch(db, project_id)

    def export_project(self, project_id):
        project = self.get_project(project_id)
        directory = self.root / "exports"
        directory.mkdir(exist_ok=True)
        target = directory / f"{project['id']}-r{project['revision']}.lab"
        content = project["source"].encode("utf-8")
        manifest = {
            "format": "lab-studio-v0", "runtime": "lab-python-v0", "entrypoint": "main.py",
            "display": [160, 160], "ticks_per_second": 30, "sha256": hashlib.sha256(content).hexdigest(),
            **_summarize(project),
        }
        descriptor = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".tmp", delete=False) as scratch:
            scratch_path = Path(scratch.name)
        try:
            with ZipFile(scratch_path, "w") as cart:
                for name, data in (("manifest.json", descriptor), ("main.py", content)):
                    entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    cart.writestr(entry, data, compress_type=ZIP_DEFLATED)
            os.replace(scratch_path, target)
        finally:
            scratch_path.unlink(missing_ok=True)
        return target

    def import_project(self, path):
        """Read a v0 cartridge from disk and open an independent, editable copy."""
        path = Path(path)
        if path.stat().st_size > 128 * 1024:
            raise StoreError("Cartridge exceeds the v0 archive size limit.")
        limits = {"manifest.json": MAX_MANIFEST_BYTES, "main.py": MAX_SOURCE_BYTES}
        try:
            with ZipFile(path) as cart:
                members = cart.infolist()
                if len(members) != 2 or {info.filename for info in members} != set(limits):
                    raise StoreError("A v0 cartridge must contain exactly manifest.json and main.py.")
                contents = {}
                for entry in members:
                    limit = limits[entry.filename]
                    if entry.file_size > limit or entry.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                        raise StoreError(f"Unsupported or oversized cartridge member: {entry.filename}")
                    with cart.open(entry) as stream:
                        data = stream.read(limit + 1)
                    if len(data) > limit:
                        raise StoreError(f"Cartridge member exceeds its limit: {entry.filename}")
                    contents[entry.filename] = data
            manifest = json.loads(contents["manifest.json"].decode("utf-8"))
            source = contents["main.py"].decode("utf-8")
        except (BadZipFile, UnicodeError, json.JSONDecodeError, RuntimeError, RecursionError, EOFError, zlib.error) as exc:
            raise StoreError(f"Cannot read this LAB cartridge: {exc}") from exc
        if not isinstance(manifest, dict) or any((
            manifest.get("format") != "lab-studio-v0",
            manifest.get("runtime") != "lab-python-v0",
            manifest.get("entrypoint") != "main.py",
            manifest.get("display") != [160, 160],
            manifest.get("ticks_per_second") != 30,
        )):
            raise StoreError("Unsupported cartridge format, runtime or display profile.")
        if manifest.get("sha256") != hashlib.sha256(contents["main.py"]).hexdigest():
            raise StoreError("Cartridge source checksum does not match its manifest.")
        title = _text(manifest.get("title"), "Title", 80)
        description = _text(manifest.get("description", ""), "Description", 1000, empty=True)
        controls = _controls(manifest.get("controls", {}))
        accent = manifest.get("accent", "#92d547")
        if not isinstance(accent, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            raise StoreError("Cartridge accent must be a six-digit hex color.")
        template = manifest.get("template", "imported")
        if not isinstance(template, str) or template not in self.templates:
            template = "imported"
        _check_source(source)
        project = {"template": template, "controls": controls, "accent": accent, "source": source}
        with self._db(write=True) as db:
            return self._add_and_open(db, project, title, description)
