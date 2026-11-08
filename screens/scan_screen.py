import time
import numpy as np
import cv2
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.app import App

from crypto_utils import decrypt_qr


class ScanScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._detector = cv2.QRCodeDetector()
        self._cam = None
        self._scan_event = None
        self._last_scan_time = 0
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=8, spacing=8)
        self.lbl_hint = Label(text="Наведите камеру на QR-код",
                              size_hint_y=None, height=40, font_size="16sp")
        root.add_widget(self.lbl_hint)
        self.cam_container = BoxLayout()
        root.add_widget(self.cam_container)
        btn_cancel = Button(text="Отмена", size_hint_y=None, height=48)
        btn_cancel.bind(on_release=lambda *_: App.get_running_app().root_widget._switch("create"))
        root.add_widget(btn_cancel)
        self.add_widget(root)

    def on_enter(self):
        self._start_camera()

    def on_leave(self):
        self._stop_camera()

    def _start_camera(self):
        if self._cam:
            return
        try:
            self._cam = Camera(play=True, resolution=(640, 480))
        except Exception as e:
            self.lbl_hint.text = "Ошибка камеры: " + str(e)
            return
        self.cam_container.add_widget(self._cam)
        self._scan_event = Clock.schedule_interval(self._scan_frame, 0.3)

    def _stop_camera(self):
        if self._scan_event:
            self._scan_event.cancel()
            self._scan_event = None
        if self._cam:
            self.cam_container.remove_widget(self._cam)
            self._cam = None

    def _scan_frame(self, dt):
        if not self._cam or not self._cam.texture:
            return
        now = time.time()
        if now - self._last_scan_time < 0.25:
            return
        self._last_scan_time = now
        w, h = self._cam.texture.size
        pixels = self._cam.texture.pixels
        frame = np.frombuffer(pixels, dtype=np.uint8).reshape((h, w, 4))
        gray = cv2.cvtColor(frame, cv2.COLOR_RGBA2GRAY)
        try:
            data, _points, _ = self._detector.detectAndDecode(gray)
        except cv2.error:
            return
        if not data:
            return
        obj_id = decrypt_qr(data)
        if obj_id is None:
            self.lbl_hint.text = "Это не код вашей системы"
            Clock.schedule_once(self._reset_hint, 1.5)
            return
        app = App.get_running_app()
        obj = app.db.get(obj_id)
        if obj is None:
            self.lbl_hint.text = "Объект не найден в базе"
            Clock.schedule_once(self._reset_hint, 1.5)
            return
        info = app.root_widget.sm.get_screen("info")
        info.show_object(obj)
        app.root_widget._switch("info")

    def _reset_hint(self, *args):
        self.lbl_hint.text = "Наведите камеру на QR-код"