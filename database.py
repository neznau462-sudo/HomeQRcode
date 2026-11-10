import datetime
import os
import sqlite3
import uuid
from contextlib import closing

DB_NAME = "homeqr.db"


class Database:
    def __init__(self, data_dir):
        self.db_path = os.path.join(data_dir, DB_NAME)
        self._init_db()

    def _connect(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self):
        # closing() обязателен: `with sqlite3.connect(...)` делает commit,
        # но НЕ закрывает соединение — на Android так копятся открытые файлы.
        with closing(self._connect()) as con, con:
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
        with closing(self._connect()) as con, con:
            con.execute(
                "INSERT INTO objects (id, name, description, category, created_at, location, qr_path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (obj_id, name, description, category, now, location, qr_path),
            )

    def get(self, obj_id):
        with closing(self._connect()) as con:
            row = con.execute("SELECT * FROM objects WHERE id = ?", (obj_id,)).fetchone()
            return dict(row) if row else None

    def update_qr_path(self, obj_id, qr_path):
        with closing(self._connect()) as con, con:
            con.execute("UPDATE objects SET qr_path = ? WHERE id = ?", (qr_path, obj_id))

    def update(self, obj_id, name, description, category, location):
        with closing(self._connect()) as con, con:
            con.execute(
                "UPDATE objects SET name = ?, description = ?, category = ?, location = ? "
                "WHERE id = ?",
                (name, description, category, location, obj_id),
            )

    def delete(self, obj_id):
        """Удаляет запись вместе с её PNG-файлом.

        Возвращает True, если запись существовала. Файл удаляется только
        после успешного удаления строки и только если он реально есть.
        """
        with closing(self._connect()) as con, con:
            row = con.execute(
                "SELECT qr_path FROM objects WHERE id = ?", (obj_id,)
            ).fetchone()
            if row is None:
                return False
            con.execute("DELETE FROM objects WHERE id = ?", (obj_id,))

        path = row["qr_path"]
        if path:
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError as exc:
                # Строка уже удалена — тихо переживаем, если файл занят.
                print("delete: cannot remove QR file:", exc)
        return True

    def category_stats(self):
        """Существующие категории: [{'category', 'count', 'last_used'}].

        Сортировка: сначала самые частые, при равенстве — самые свежие.
        Регистр не важен: «обувь» и «Обувь» считаются одной категорией.
        """
        with closing(self._connect()) as con:
            rows = con.execute(
                "SELECT category, created_at FROM objects "
                "WHERE category IS NOT NULL AND TRIM(category) != ''"
            ).fetchall()

        groups = {}
        for row in rows:
            exact = " ".join(row["category"].split())
            key = exact.casefold()
            if not key:
                continue
            item = groups.get(key)
            if item is None:
                item = {"variants": {}, "count": 0, "last_used": ""}
                groups[key] = item
            item["variants"][exact] = item["variants"].get(exact, 0) + 1
            item["count"] += 1
            if row["created_at"] > item["last_used"]:
                item["last_used"] = row["created_at"]

        result = []
        for item in groups.values():
            variants = item["variants"]
            # каноническим считаем самое частое написание среди вариантов
            canonical = max(variants, key=variants.get)
            result.append({
                "category": canonical,
                "count": item["count"],
                "last_used": item["last_used"],
            })

        result.sort(key=lambda s: s["last_used"], reverse=True)
        result.sort(key=lambda s: s["count"], reverse=True)
        return result

    def canonical_category(self, text):
        """Возвращает уже существующее написание категории, если оно есть."""
        value = " ".join((text or "").split())
        if not value:
            return ""
        needle = value.casefold()
        for item in self.category_stats():
            if item["category"].casefold() == needle:
                return item["category"]
        return value

    def search(self, name_query="", category="", order="desc"):
        """Поиск записей. order: "desc" — сначала новые, "asc" — сначала старые."""
        direction = "ASC" if str(order).lower() == "asc" else "DESC"

        sql = "SELECT * FROM objects WHERE 1=1"
        params = []
        if category:
            # категория выбирается из списка, поэтому сравнение точное
            sql += " AND category = ?"
            params.append(category)
        # rowid — вторичный ключ: записи, созданные в одну секунду,
        # не будут «прыгать» при сортировке.
        sql += " ORDER BY created_at " + direction + ", rowid " + direction

        with closing(self._connect()) as con:
            rows = [dict(r) for r in con.execute(sql, params).fetchall()]

        # Поиск по названию делаем в Python: SQLite-функция lower() не знает
        # кириллицу, поэтому "ботинки" не находило бы "Ботинки".
        if name_query:
            needle = name_query.casefold()
            rows = [r for r in rows if needle in (r.get("name") or "").casefold()]
        return rows

    def list_categories(self):
        with closing(self._connect()) as con:
            rows = con.execute(
                "SELECT DISTINCT category FROM objects "
                "WHERE category IS NOT NULL AND category != '' ORDER BY category"
            ).fetchall()
            return [r[0] for r in rows]

    def export_all(self):
        with closing(self._connect()) as con:
            return [dict(r) for r in con.execute(
                "SELECT * FROM objects ORDER BY created_at DESC"
            ).fetchall()]
