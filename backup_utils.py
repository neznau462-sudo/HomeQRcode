"""Резервная копия базы: экспорт в общую память и импорт через выбор файла."""
import os
import shutil
import sqlite3
import tempfile

DB_NAME = "homeqr.db"


def make_db_copy(db_path, target_dir):
    """Согласованная копия sqlite-базы (безопасна даже при открытом соединении)."""
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, DB_NAME)
    if os.path.exists(target):
        os.remove(target)

    src = sqlite3.connect(db_path)
    try:
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    return target


def is_android():
    try:
        from kivy.utils import platform
        return platform == "android"
    except Exception:
        return False


def export_to_documents(db_path):
    """Кладёт копию базы в Documents/<Название приложения>/.

    Возвращает True при успехе. На компьютере всегда False.
    """
    if not is_android():
        return False
    try:
        from androidstorage4kivy import SharedStorage
    except Exception:
        return False

    tmp_dir = tempfile.mkdtemp()
    try:
        copy_path = make_db_copy(db_path, tmp_dir)
        uri = SharedStorage().copy_to_shared(copy_path, collection="Documents")
        return uri is not None
    except Exception as exc:
        print("export_to_documents failed:", exc)
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def import_from_shared(shared_file, db_path):
    """Копирует выбранный пользователем файл базы на место текущей.

    Возвращает True, если файл действительно является базой HomeQRcode.
    """
    if not is_android():
        return False
    try:
        from androidstorage4kivy import SharedStorage
    except Exception:
        return False

    try:
        local = SharedStorage().copy_from_shared(shared_file)
    except Exception as exc:
        print("import_from_shared: copy failed:", exc)
        return False

    if not local or not os.path.exists(local):
        return False
    if not _is_homeqr_db(local):
        return False

    try:
        if os.path.exists(db_path):
            shutil.copyfile(db_path, db_path + ".before_import")
        shutil.copyfile(local, db_path)
        return True
    except Exception as exc:
        print("import_from_shared: replace failed:", exc)
        return False


def _is_homeqr_db(path):
    """Проверяем, что это sqlite-база и в ней есть наша таблица."""
    try:
        con = sqlite3.connect(path)
        try:
            row = con.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='objects'"
            ).fetchone()
            return row is not None
        finally:
            con.close()
    except Exception:
        return False
