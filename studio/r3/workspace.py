"""Local draft recovery for the r3 editor. Saved cartridges use Studio's shared store."""
import sqlite3
from contextlib import closing
from pathlib import Path


class DraftBook:
    def __init__(self, library):
        self.path = Path(library) / "editor-drafts-r3.sqlite3"
        with closing(self.connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS drafts
                          (project TEXT PRIMARY KEY, revision INTEGER NOT NULL, source TEXT NOT NULL)""")

    def connect(self):
        return sqlite3.connect(self.path, timeout=1)

    def all(self):
        with closing(self.connect()) as db:
            return {p: (s, r) for p, r, s in db.execute("SELECT project,revision,source FROM drafts")}

    def put(self, project, source, revision):
        with closing(self.connect()) as db, db:
            db.execute("""INSERT INTO drafts VALUES(?,?,?)
                          ON CONFLICT(project) DO UPDATE SET revision=excluded.revision,source=excluded.source""",
                       (project, revision, source))

    def remove(self, project):
        with closing(self.connect()) as db, db:
            db.execute("DELETE FROM drafts WHERE project=?", (project,))
