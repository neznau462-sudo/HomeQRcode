from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

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

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        self.ti_name = TextInput(
            multiline=False,
            hint_text="Поиск по названию",
            size_hint_y=None,
            height=dp(46),
            font_size="15sp",
        )
        root.add_widget(self.ti_name)

        self.spinner = Spinner(
            text="Все категории",
            values=["Все категории"],
            size_hint_y=None,
            height=dp(46),
            font_size="15sp",
        )
        root.add_widget(self.spinner)

        btn = Button(text="Найти", size_hint_y=None, height=dp(48), font_size="16sp")
        btn.bind(on_release=lambda *_: self._do_search())
        root.add_widget(btn)

        self.results = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(6),
        )
        self.results.bind(minimum_height=self.results.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.results)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_enter(self):
        app = App.get_running_app()
        cats = ["Все категории"] + app.db.list_categories()
        self.spinner.values = cats
        if self.spinner.text not in cats:
            self.spinner.text = "Все категории"

    def _do_search(self):
        app = App.get_running_app()
        name_q = self.ti_name.text.strip()
        cat = self.spinner.text
        cat_q = "" if cat == "Все категории" else cat
        rows = app.db.search(name_query=name_q, category=cat_q)
        self.results.clear_widgets()
        if not rows:
            self.results.add_widget(
                Label(text="Ничего не найдено", size_hint_y=None, height=dp(44))
            )
            return
        for row in rows:
            text = (
                "[b]" + str(row["name"]) + "[/b]\n"
                "Категория: " + str(row["category"] or "—") + "\n"
                "Местоположение: " + str(row["location"] or "—") + "\n"
                "Описание: " + str(row["description"] or "—") + "\n"
                "Создано: " + str(row["created_at"]))
            lbl = Label(
                text=text,
                markup=True,
                size_hint_y=None,
                font_size="14sp",
                halign="left",
                valign="top",
            )
            _fit_label(lbl, dp(120))
            self.results.add_widget(lbl)
            # без этого Label не переносит строки и текст обрезается
            lbl.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
            self.results.add_widget(lbl)
