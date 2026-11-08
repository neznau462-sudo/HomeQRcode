import os
import datetime


def save_qr_png(pil_image, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".png"
    path = os.path.join(target_dir, filename)
    pil_image.save(path, "PNG")
    return path


def copy_to_gallery(local_path):
    try:
        from androidstorage4kivy import SharedStorage
        shared = SharedStorage()
        shared.copy_to_shared(local_path, collection="Pictures")
    except Exception:
        pass