import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window

from database import Database
from screens.create_screen import CreateScreen
from screens.scan_screen import ScanScreen
from screens.info_screen import InfoScreen
from screens.search_screen import SearchScreen


class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(CreateScreen(name="create"))
        self.sm.add_widget(ScanScreen(name="scan"))
        self.sm.add_widget(InfoScreen(name="info"))
        self.sm.add_widget(SearchScreen(name="search"))
        self.add_widget(self.sm)
        tabs = BoxLayout(size_hint_y=None, height=56, spacing=2)
        for label, name in [
            ("Создать", "create"),
            ("Сканировать", "scan"),
            ("Инфо", "info"),
            ("Поиск", "search"),
        ]:
            b = Button(text=label)
            b.bind(on_release=lambda _x, n=name: self._switch(n))
            tabs.add_widget(b)
        self.add_widget(tabs)

    def _switch(self, name):
        self.sm.current = name


class HomeQRApp(App):
    def build(self):
        Window.softinput_mode = "below_target"
        self.title = "HomeQRcode"
        self.qr_dir = os.path.join(self.user_data_dir, "qr")
        os.makedirs(self.qr_dir, exist_ok=True)
        self.db = Database(self.user_data_dir)
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
        except ImportError:
            pass
        self.root_widget = RootWidget()
        return self.root_widget


if __name__ == "__main__":
    HomeQRApp().run()