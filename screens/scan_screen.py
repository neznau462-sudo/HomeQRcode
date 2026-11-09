import time

import cv2
import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import PopMatrix, PushMatrix, Rotate
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.stencilview import StencilView

from crypto_utils import decrypt_qr
from ui_theme import SURFACE, SURFACE_HI, TEXT, Card, RoundedButton

# Поворот превью камеры в градусах.
# Сейчас картинка приходит "боком" — разворачиваем на 90° по часовой.
# Если после сборки превью окажется повёрнутым в другую сторону — поставь 90,
# если поворот вообще не нужен — 0.
CAM_ROTATION = -90


class ScanScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._detector = cv2.QRCodeDetector()
        self._cam = None
        self._cam_rotate = None
        self._scan_event = None
        self._last_scan_time = 0
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")

        top = Card(size_hint_y=None, height=dp(56), radius=0,
                   padding=[dp(16), 0, dp(16), 0], bg_color=list(SURFACE))
        self.lbl_hint = Label(text="Наведите камеру на QR-код", color=TEXT,
                              font_size="15sp")
        self.lbl_hint.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
        top.add_widget(self.lbl_hint)
        root.add_widget(top)

        # StencilView обрезает превью по своим границам.
        self.preview = StencilView()
        self.preview.bind(pos=self._sync_preview, size=self._sync_preview)
        root.add_widget(self.preview)

        bottom = Card(size_hint_y=None, height=dp(76), radius=0,
                      padding=dp(12), bg_color=list(SURFACE))
        btn_cancel = RoundedButton(text="Отмена", size_hint_y=None, height=dp(48),
                                   bg_color=list(SURFACE_HI),
                                   bg_color_down=list(SURFACE_HI),
                                   text_color=list(TEXT))
        btn_cancel.bind(
            on_release=lambda *_: App.get_running_app().root_widget._switch("create")
        )
        bottom.add_widget(btn_cancel)
        root.add_widget(bottom)

        self.add_widget(root)

    def on_enter(self):
        self._start_camera()

    def on_leave(self):
        self._stop_camera()

    def _start_camera(self):
        if self._cam:
            return
        try:
            # fit_mode="fill": картинка заполняет коробку камеры ровно, без
            # полей. Небольшое растяжение по ширине (~10%) — плата за то,
            # что превью занимает весь экран, а не висит мелким окошком.
            self._cam = Camera(play=True, resolution=(640, 480),
                               fit_mode="fill", size_hint=(None, None))
        except Exception as exc:
            self.lbl_hint.text = "Ошибка камеры: " + str(exc)
            return

        # Разворот превью: сенсор отдаёт кадр в альбомной ориентации.
        with self._cam.canvas.before:
            PushMatrix()
            self._cam_rotate = Rotate(angle=CAM_ROTATION, origin=(0, 0))
        with self._cam.canvas.after:
            PopMatrix()

        self.preview.add_widget(self._cam)
        self._sync_preview()
        self._scan_event = Clock.schedule_interval(self._scan_frame, 0.3)

    def _stop_camera(self):
        if self._scan_event:
            self._scan_event.cancel()
            self._scan_event = None
        if self._cam:
            self._cam.play = False
            self.preview.remove_widget(self._cam)
            self._cam = None
            self._cam_rotate = None

    def _sync_preview(self, *_):
        """Кладём камеру «набок» и растягиваем на весь контейнер.

        До поворота коробка камеры должна быть транспонированной
        (высота x ширина) — тогда после поворота на 90° картинка
        займёт весь прямоугольник превью.
        """
        if not self._cam:
            return
        area = self.preview
        if area.width <= 0 or area.height <= 0:
            return
        self._cam.size = (area.height, area.width)
        self._cam.center = area.center
        if self._cam_rotate is not None:
            self._cam_rotate.origin = (area.center_x, area.center_y)

    def _scan_frame(self, dt):
        if not self._cam or not self._cam.texture:
            return
        now = time.time()
        if now - self._last_scan_time < 0.25:
            return
        self._last_scan_time = now

        width, height = self._cam.texture.size
        width, height = int(width), int(height)
        pixels = self._cam.texture.pixels
        frame = np.frombuffer(pixels, dtype=np.uint8)
        if frame.size < width * height * 4:
            return
        frame = frame[: width * height * 4].reshape((height, width, 4))
        gray = cv2.cvtColor(frame, cv2.COLOR_RGBA2GRAY)

        try:
            data, _points, _ = self._detector.detectAndDecode(gray)
        except cv2.error:
            return
        if not data:
            return

        obj_id = decrypt_qr(data)
        if obj_id is None:
            self._show_hint("Это не код вашей системы")
            return

        app = App.get_running_app()
        obj = app.db.get(obj_id)
        if obj is None:
            self._show_hint("Объект не найден в базе")
            return

        info = app.root_widget.sm.get_screen("info")
        info.show_object(obj)
        app.root_widget._switch("info")

    def _show_hint(self, text):
        self.lbl_hint.text = text
        Clock.schedule_once(self._reset_hint, 1.5)

    def _reset_hint(self, *args):
        self.lbl_hint.text = "Наведите камеру на QR-код"
