from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.app import App


class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        self.ti_name = TextInput(multiline=False, hint_text="Поиск по названию",
                                 size_hint_y=None, height=44)
        root.add_widget(self.ti_name)
        self.spinner = Spinner(text="Все категории", values=["Все категории"],
                               size_hint_y=None, height=44)
        root.add_widget(self.spinner)
        btn = Button(text="Найти", size_hint_y=None, height=48)
        btn.bind(on_release=lambda *_: self._do_search())
        root.add_widget(btn)
        self.results = BoxLayout(orientation="vertical", size_hint_y=None, spacing=4)
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
            self.results.add_widget(Label(text="Ничего не найдено",
                                          size_hint_y=None, height=40))
            return
        for row in rows:
            text = (
                "[b]" + str(row["name"]) + "[/b]\n"
                "Категория: " + str(row["category"] or "—") + "\n"
                "Местоположение: " + str(row["location"] or "—") + "\n"
                "Описание: " + str(row["description"] or "—") + "\n"
                "Создано: " + str(row["created_at"]))
            lbl = Label(text=text, markup=True, size_hint_y=None, height=140,
                        text_size=(None, None), halign="left", valign="top")
            self.results.add_widget(lbl)