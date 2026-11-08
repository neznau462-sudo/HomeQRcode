import json
import os
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

PREFIX = "HQ1|"
VERSION = 1

_KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys", "secret.key")


def _load_key():
    with open(_KEY_PATH, "rb") as f:
        return base64.urlsafe_b64decode(f.read().strip())


_KEY = _load_key()


def encrypt_id(obj_id):
    nonce = get_random_bytes(12)
    cipher = AES.new(_KEY, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(
        json.dumps({"id": obj_id, "v": VERSION}).encode("utf-8")
    )
    payload = nonce + tag + ct
    return PREFIX + base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_qr(qr_text):
    if not qr_text or not qr_text.startswith(PREFIX):
        return None
    try:
        payload = base64.urlsafe_b64decode(qr_text[len(PREFIX):])
    except Exception:
        return None
    if len(payload) < 28:
        return None
    nonce, tag, ct = payload[:12], payload[12:28], payload[28:]
    try:
        cipher = AES.new(_KEY, AES.MODE_GCM, nonce=nonce)
        pt = cipher.decrypt_and_verify(ct, tag)
        data = json.loads(pt.decode("utf-8"))
    except Exception:
        return None
    if data.get("v") != VERSION:
        return None
    return data.get("id")