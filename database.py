import sqlite3
import os
import datetime
import uuid

DB_NAME = "homeqr.db"


class Database:
    def __init__(self, data_dir):
        self.db_path = os.path.join(data_dir, DB_NAME)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS objects ("
                "id TEXT PRIMARY KEY, "
                "name TEXT NOT NULL, "
                "description TEXT, "
                "category TEXT, "
                "created_at TEXT NOT NULL, "
                "location TEXT, "
                "qr_path TEXT)"
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_name ON objects(name)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_category ON objects(category)")

    def new_id(self):
        return str(uuid.uuid4())

    def insert(self, obj_id, name, description, category, location, qr_path=None):
        now = datetime.datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT INTO objects (id, name, description, category, created_at, location, qr_path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (obj_id, name, description, category, now, location, qr_path),
            )

    def get(self, obj_id):
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT * FROM objects WHERE id = ?", (obj_id,)).fetchone()
            return dict(row) if row else None

    def update_qr_path(self, obj_id, qr_path):
        with sqlite3.connect(self.db_path) as con:
            con.execute("UPDATE objects SET qr_path = ? WHERE id = ?", (qr_path, obj_id))

    def search(self, name_query="", category=""):
        sql = "SELECT * FROM objects WHERE 1=1"
        params = []
        if name_query:
            sql += " AND instr(name, ?) > 0"
            params.append(name_query)
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY created_at DESC"
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            return [dict(r) for r in con.execute(sql, params).fetchall()]

    def list_categories(self):
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute(
                "SELECT DISTINCT category FROM objects "
                "WHERE category IS NOT NULL AND category != '' ORDER BY category"
            ).fetchall()
            return [r[0] for r in rows]

    def export_all(self):
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            return [dict(r) for r in con.execute("SELECT * FROM objects ORDER BY created_at DESC").fetchall()]