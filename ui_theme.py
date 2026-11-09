"""Оформление: палитра и скруглённые виджеты."""
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

# палитра
BG = (0.055, 0.065, 0.085, 1)
SURFACE = (0.10, 0.115, 0.145, 1)
SURFACE_HI = (0.16, 0.18, 0.23, 1)
PRIMARY = (0.29, 0.56, 0.98, 1)
PRIMARY_DOWN = (0.21, 0.43, 0.80, 1)
TEXT = (0.94, 0.95, 0.97, 1)
TEXT_MUTED = (0.60, 0.65, 0.74, 1)
ACCENT = (0.36, 0.86, 0.72, 1)

RADIUS = dp(14)


class Card(BoxLayout):
    """Скруглённая подложка (карточка / панель)."""

    bg_color = ListProperty(list(SURFACE))
    radius = NumericProperty(RADIUS)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg = Color(*self.bg_color)
            self._rect = RoundedRectangle(radius=[self.radius] * 4)
        self.bind(pos=self._sync, size=self._sync,
                  bg_color=self._sync_color, radius=self._sync_radius)
        self._sync()

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _sync_color(self, *_):
        self._bg.rgba = self.bg_color

    def _sync_radius(self, *_):
        self._rect.radius = [self.radius] * 4


class RoundedButton(Button):
    bg_color = ListProperty(list(PRIMARY))
    bg_color_down = ListProperty(list(PRIMARY_DOWN))
    text_color = ListProperty(list(TEXT))
    radius = NumericProperty(RADIUS)

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("font_size", "16sp")
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg = Color(*self.bg_color)
            self._rect = RoundedRectangle(radius=[self.radius] * 4)
        self.bind(pos=self._sync, size=self._sync, state=self._sync_state,
                  disabled=self._sync_state, bg_color=self._sync_state,
                  bg_color_down=self._sync_state, radius=self._sync_radius,
                  text_color=self._sync_text)
        self._sync()
        self._sync_state()
        self._sync_text()

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _sync_radius(self, *_):
        self._rect.radius = [self.radius] * 4

    def _sync_state(self, *_):
        color = self.bg_color_down if self.state == "down" else self.bg_color
        alpha = 0.45 if self.disabled else color[3]
        self._bg.rgba = (color[0], color[1], color[2], alpha)

    def _sync_text(self, *_):
        self.color = self.text_color


class RoundedTextInput(TextInput):
    bg_color = ListProperty(list(SURFACE_HI))
    radius = NumericProperty(dp(12))

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_active", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("foreground_color", TEXT)
        kwargs.setdefault("hint_text_color", TEXT_MUTED)
        kwargs.setdefault("cursor_color", PRIMARY)
        kwargs.setdefault("selection_color", (0.29, 0.56, 0.98, 0.35))
        kwargs.setdefault("font_size", "15sp")
        kwargs.setdefault("padding", [dp(12), dp(12), dp(12), dp(12)])
        super().__init__(**kwargs)
        self._bg = Color(*self.bg_color)
        self._rect = RoundedRectangle(radius=[self.radius] * 4)
        # ВАЖНО: вставляем в НАЧАЛО canvas.before.
        # Стандартное правило Kivy для TextInput заканчивается инструкцией
        # Color, которой красится текст. Если дописать свой Color в конец,
        # текст начнёт рисоваться цветом фона и станет невидимым.
        self.canvas.before.insert(0, self._rect)
        self.canvas.before.insert(0, self._bg)
        self.bind(pos=self._sync, size=self._sync, radius=self._sync_radius)
        self._sync()

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _sync_radius(self, *_):
        self._rect.radius = [self.radius] * 4
