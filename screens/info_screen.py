from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from backup_utils import export_to_documents, import_from_shared, is_android
from ui_theme import SURFACE_HI, TEXT, TEXT_MUTED, Card, RoundedButton


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
                font_size="16sp",
                color=TEXT,
                halign="left",
                valign="top",
            ),
            dp(44),
        )
        root.add_widget(self.lbl_header)

        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", size_hint_y=None,
                            spacing=dp(12))
        content.bind(minimum_height=content.setter("height"))

        self.details = BoxLayout(orientation="vertical", size_hint_y=None,
                                 spacing=dp(8))
        self.details.bind(minimum_height=self.details.setter("height"))
        content.add_widget(self.details)

        content.add_widget(self._build_backup_card())

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)

    def _build_backup_card(self):
        card = Card(orientation="vertical", size_hint_y=None,
                    padding=dp(12), spacing=dp(8))
        card.bind(minimum_height=card.setter("height"))

        title = Label(
            text="Резервная копия",
            bold=True,
            color=TEXT,
            font_size="15sp",
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        _fit_label(title, dp(24))
        card.add_widget(title)

        hint = Label(
            text=("Копия базы сохраняется в папку Documents. "
                  "После переустановки нажмите «Восстановить из файла» "
                  "и выберите homeqr.db."),
            color=TEXT_MUTED,
            font_size="13sp",
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        _fit_label(hint, dp(36))
        card.add_widget(hint)

        self.btn_export = RoundedButton(
            text="Сохранить копию базы",
            size_hint_y=None,
            height=dp(46),
        )
        self.btn_export.bind(on_release=self._on_export)
        card.add_widget(self.btn_export)

        self.btn_import = RoundedButton(
            text="Восстановить из файла",
            size_hint_y=None,
            height=dp(46),
            bg_color=list(SURFACE_HI),
            bg_color_down=list(SURFACE_HI),
            text_color=list(TEXT),
        )
        self.btn_import.bind(on_release=self._on_import)
        card.add_widget(self.btn_import)

        self.lbl_backup = Label(
            text="",
            color=TEXT_MUTED,
            font_size="13sp",
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        _fit_label(self.lbl_backup, dp(20))
        card.add_widget(self.lbl_backup)

        return card

    def _on_export(self, *_):
        app = App.get_running_app()
        if not is_android():
            self.lbl_backup.text = "Доступно только на телефоне"
            return
        self.lbl_backup.text = "Сохраняю…"
        if export_to_documents(app.db.db_path):
            self.lbl_backup.text = "Готово: Documents/HomeQRcode/homeqr.db"
        else:
            self.lbl_backup.text = "Не удалось сохранить копию"

    def _on_import(self, *_):
        if not is_android():
            self.lbl_backup.text = "Доступно только на телефоне"
            return
        try:
            from androidstorage4kivy import Chooser
        except Exception:
            self.lbl_backup.text = "Модуль выбора файлов недоступен"
            return
        self.lbl_backup.text = "Выберите файл homeqr.db…"
        Chooser(callback=self._on_import_chosen).choose_content("*/*")

    def _on_import_chosen(self, files):
        app = App.get_running_app()
        if not files:
            self.lbl_backup.text = "Файл не выбран"
            return
        if import_from_shared(files[0], app.db.db_path):
            app.reload_db()
            self.lbl_backup.text = "Данные восстановлены. Откройте «Поиск»."
        else:
            self.lbl_backup.text = "Это не файл базы HomeQRcode"

    def show_object(self, obj):
        self.details.clear_widgets()
        self.lbl_header.text = "Объект: " + str(obj.get("name") or "")

        card = Card(orientation="vertical", size_hint_y=None,
                    padding=dp(12), spacing=dp(10))
        card.bind(minimum_height=card.setter("height"))

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
                text="[b][color=#8f97a8]" + label + "[/color][/b]\n" + str(value),
                markup=True,
                size_hint_y=None,
                font_size="14sp",
                color=TEXT,
                halign="left",
                valign="top",
            )
            _fit_label(lbl, dp(44))
            card.add_widget(lbl)

        self.details.add_widget(card)
