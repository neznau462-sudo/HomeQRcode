import datetime
import os
import uuid


def save_qr_png(pil_image, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    # Раньше имя было с точностью до секунды: два QR подряд перезаписывали
    # один и тот же файл. Добавляем уникальный хвост.
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = stamp + "_" + uuid.uuid4().hex[:8] + ".png"
    path = os.path.join(target_dir, filename)
    pil_image.save(path, "PNG")
    return path


def copy_to_gallery(local_path):
    """Копирует файл в общую галерею. Возвращает True, если получилось."""
    try:
        from androidstorage4kivy import SharedStorage
        SharedStorage().copy_to_shared(local_path, collection="Pictures")
        return True
    except Exception as exc:
        # Раньше ошибка молча проглатывалась, а интерфейс всё равно писал
        # "Сохранено в галерею". Теперь сообщаем честно.
        print("copy_to_gallery failed:", exc)
        return False
