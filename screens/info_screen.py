from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView


def _fit_label(label, min_height):
    """Подгоняет высоту Label под перенесённый текст (иначе он обрезается)."""

    def on_width(*_):
        label.text_size = (label.width, None)

    def on_texture(*_):
        label.height = max(min_height, label.texture_size[1] + dp(8))

    label.bind(width=on_width, texture_size=on_texture)
    on_width()
    on_texture()
    return label


class InfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        self.lbl_header = _fit_label(
            Label(
                text="Здесь появятся данные отсканированного объекта",
                size_hint_y=None,
                font_size="15sp",
                halign="left",
                valign="top",
            ),
            dp(44),
        )
        root.add_widget(self.lbl_header)

        scroll = ScrollView()
        self.content = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        root.add_widget(scroll)

        self.add_widget(root)

    def show_object(self, obj):
        self.content.clear_widgets()
        self.lbl_header.text = "Объект: " + str(obj.get("name") or "")
        for label, key in [
            ("ID", "id"),
            ("Название", "name"),
            ("Категория", "category"),
            ("Описание", "description"),
            ("Дата создания", "created_at"),
            ("Местоположение", "location"),
        ]:
            value = obj.get(key) or "—"
            lbl = Label(
                text="[b]" + label + "[/b] " + str(value),
                markup=True,
                size_hint_y=None,
                font_size="14sp",
                halign="left",
                valign="top",
            )
            _fit_label(lbl, dp(40))
            self.content.add_widget(lbl)
