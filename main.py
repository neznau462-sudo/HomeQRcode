import os

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, NoTransition

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

        tabs = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(2))
        for label, name in [
            ("Создать", "create"),
            ("Сканировать", "scan"),
            ("Инфо", "info"),
            ("Поиск", "search"),
        ]:
            b = Button(text=label, font_size="15sp")
            b.bind(on_release=lambda _x, n=name: self._switch(n))
            tabs.add_widget(b)
        self.add_widget(tabs)
        # Кнопка/жест "Назад" на Android: не выходить из приложения,
        # а возвращаться на главный экран.
        Window.bind(on_keyboard=self._on_keyboard)

    def _switch(self, name):
        self.sm.current = name

    def _on_keyboard(self, window, key, *args):
        if key == 27 and self.sm.current != "create":  # 27 == ESC / back
            self._switch("create")
            return True
        return False


class HomeQRApp(App):
    def build(self):
        Window.softinput_mode = "below_target"
        self.title = "HomeQRcode"
        self.qr_dir = os.path.join(self.user_data_dir, "qr")
        os.makedirs(self.qr_dir, exist_ok=True)
        self.db = Database(self.user_data_dir)

        try:
            from android.permissions import request_permissions, Permission
        except ImportError:
            request_permissions = None

        if request_permissions is not None:
            # На Android 13+ (API 33) WRITE_EXTERNAL_STORAGE уже не выдаётся,
            # вместо него нужен READ_MEDIA_IMAGES. Берём только те разрешения,
            # которые есть в текущей версии p4a, чтобы не упасть на старте.
            wanted = []
            for name in (
                "CAMERA",
                "READ_MEDIA_IMAGES",
                "READ_EXTERNAL_STORAGE",
                "WRITE_EXTERNAL_STORAGE",
            ):
                permission = getattr(Permission, name, None)
                if permission is not None:
                    wanted.append(permission)
            request_permissions(wanted)

        self.root_widget = RootWidget()
        return self.root_widget


if __name__ == "__main__":
    HomeQRApp().run()
