from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView


class InfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        self.lbl_header = Label(
            text="Здесь появятся данные отсканированного объекта",
            size_hint_y=None,
            height=dp(44),
            font_size="15sp",
        )
        self.lbl_header.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
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
                text="[b]" + label + ":[/b] " + str(value),
                markup=True,
                size_hint_y=None,
                height=dp(64),
                font_size="14sp",
                halign="left",
                valign="top",
            )
            lbl.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
            self.content.add_widget(lbl)
