from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

from ui_theme import (SURFACE, TEXT, TEXT_MUTED, Card, RoundedButton,
                      RoundedTextInput)


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


class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        self.ti_name = RoundedTextInput(
            multiline=False,
            hint_text="Поиск по названию",
            size_hint_y=None,
            height=dp(48),
        )
        root.add_widget(self.ti_name)

        # Spinner прозрачный, а скруглённый фон даёт карточка под ним.
        spinner_card = Card(size_hint_y=None, height=dp(48), padding=0,
                            bg_color=list(SURFACE))
        self.spinner = Spinner(
            text="Все категории",
            values=["Все категории"],
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=TEXT,
            font_size="15sp",
        )
        spinner_card.add_widget(self.spinner)
        root.add_widget(spinner_card)

        btn = RoundedButton(text="Найти", size_hint_y=None, height=dp(48))
        btn.bind(on_release=lambda *_: self._do_search())
        root.add_widget(btn)

        self.results = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(8),
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
                Label(text="Ничего не найдено", size_hint_y=None,
                      height=dp(44), color=TEXT_MUTED)
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
                color=TEXT,
                halign="left",
                valign="top",
            )
            _fit_label(lbl, dp(120))

            card = Card(orientation="vertical", size_hint_y=None,
                        padding=dp(12), spacing=dp(4))
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(lbl)
            self.results.add_widget(card)
