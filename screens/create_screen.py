import qrcode
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from crypto_utils import encrypt_id
from storage_utils import save_qr_png, copy_to_gallery
from ui_theme import (SURFACE_HI, TEXT, TEXT_MUTED, Card, RoundedButton,
                      RoundedTextInput)

ROW = dp(50)
LABEL_W = dp(120)


class FieldLabel(Label):
    """Подпись слева от поля ввода: фиксированная ширина, перенос по словам."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_x", None)
        kwargs.setdefault("width", LABEL_W)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", ROW)
        kwargs.setdefault("font_size", "14sp")
        kwargs.setdefault("color", TEXT_MUTED)
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)
        self.bind(size=self._sync_text_size)

    def _sync_text_size(self, *_):
        self.text_size = (self.width - dp(6), self.height)


class CreateScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_qr_path = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(12))

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        content.bind(minimum_height=content.setter("height"))

        form = Card(orientation="vertical", size_hint_y=None,
                    padding=dp(12), spacing=dp(8))
        form.bind(minimum_height=form.setter("height"))

        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        self.ti_name = RoundedTextInput(
            multiline=False,
            hint_text="Например: Ботинки зимние",
            size_hint_y=None,
            height=ROW,
        )
        self.ti_category = RoundedTextInput(
            multiline=False,
            hint_text="Например: Обувь",
            size_hint_y=None,
            height=ROW,
        )
        self.ti_location = RoundedTextInput(
            multiline=False,
            hint_text="Например: справа на верхней полке",
            size_hint_y=None,
            height=ROW,
        )
        self.ti_description = RoundedTextInput(
            multiline=True,
            hint_text="Свободное описание",
            size_hint_y=None,
            height=dp(96),
        )

        for label, widget in [
            ("Название*", self.ti_name),
            ("Категория", self.ti_category),
            ("Местоположение", self.ti_location),
            ("Описание", self.ti_description),
        ]:
            grid.add_widget(FieldLabel(text=label))
            grid.add_widget(widget)

        form.add_widget(grid)
        content.add_widget(form)

        self.btn_generate = RoundedButton(text="Сгенерировать QR",
                                          size_hint_y=None, height=dp(52))
        self.btn_generate.bind(on_release=self._on_generate)
        content.add_widget(self.btn_generate)

        preview = Card(size_hint_y=None, height=dp(260), padding=dp(8))
        self.img_preview = Image(size_hint_y=None, height=dp(240),
                                 fit_mode="contain")
        preview.add_widget(self.img_preview)
        content.add_widget(preview)

        self.lbl_status = Label(text="", size_hint_y=None, height=dp(28),
                                font_size="14sp", color=TEXT_MUTED)
        content.add_widget(self.lbl_status)

        self.btn_save = RoundedButton(
            text="Сохранить в галерею",
            size_hint_y=None,
            height=dp(48),
            bg_color=list(SURFACE_HI),
            bg_color_down=list(SURFACE_HI),
            text_color=list(TEXT),
            disabled=True,
        )
        self.btn_save.bind(on_release=self._on_save_to_gallery)
        content.add_widget(self.btn_save)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _on_generate(self, *_):
        app = App.get_running_app()
        name = self.ti_name.text.strip()
        if not name:
            self.lbl_status.text = "Укажите название"
            return

        obj_id = app.db.new_id()
        encrypted = encrypt_id(obj_id)

        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(encrypted)
            qr.make(fit=True)
            # convert() есть у qrcode через __getattr__ -> PIL.Image
            pil_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            local_path = save_qr_png(pil_img, app.qr_dir)
        except Exception as exc:
            self.lbl_status.text = "Ошибка: " + str(exc)
            return

        self._last_qr_path = local_path

        app.db.insert(
            obj_id=obj_id,
            name=name,
            description=self.ti_description.text.strip(),
            category=self.ti_category.text.strip(),
            location=self.ti_location.text.strip(),
            qr_path=local_path,
        )

        if self.img_preview.source == local_path:
            self.img_preview.reload()
        else:
            self.img_preview.source = local_path

        self.lbl_status.text = "Готово. ID: " + obj_id[:8]
        self.btn_save.disabled = False

    def _on_save_to_gallery(self, *_):
        if not self._last_qr_path:
            return
        if copy_to_gallery(self._last_qr_path):
            self.lbl_status.text = "Сохранено в галерею"
            self.btn_save.disabled = True
        else:
            self.lbl_status.text = "Не удалось сохранить в галерею"
