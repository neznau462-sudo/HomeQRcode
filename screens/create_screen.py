import io
import qrcode
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.app import App

from crypto_utils import encrypt_id
from storage_utils import save_qr_png, copy_to_gallery


class CreateScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_qr_path = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        form = GridLayout(cols=2, spacing=6, size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.ti_name = TextInput(multiline=False, hint_text="Например: Ботинки зимние")
        self.ti_category = TextInput(multiline=False, hint_text="Например: Обувь")
        self.ti_location = TextInput(multiline=False, hint_text="Например: справа на верхней полке")
        self.ti_description = TextInput(multiline=True, hint_text="Свободное описание")

        for label, widget in [
            ("Название*", self.ti_name),
            ("Категория", self.ti_category),
            ("Местоположение", self.ti_location),
            ("Описание", self.ti_description),
        ]:
            form.add_widget(Label(text=label, size_hint_x=0.35))
            form.add_widget(widget)

        root.add_widget(form)

        btn_generate = Button(text="Сгенерировать QR", size_hint_y=None, height=52)
        btn_generate.bind(on_release=self._on_generate)
        root.add_widget(btn_generate)

        self.img_preview = Image(size_hint=(1, 0.45))
        root.add_widget(self.img_preview)

        self.lbl_status = Label(text="", size_hint_y=None, height=30)
        root.add_widget(self.lbl_status)

        self.btn_save = Button(text="Сохранить в галерею",
                               size_hint_y=None, height=48, disabled=True)
        self.btn_save.bind(on_release=self._on_save_to_gallery)
        root.add_widget(self.btn_save)

        self.add_widget(root)

    def _on_generate(self, *_):
        app = App.get_running_app()
        name = self.ti_name.text.strip()
        if not name:
            self.lbl_status.text = "Укажите название"
            return

        obj_id = app.db.new_id()
        encrypted = encrypt_id(obj_id)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(encrypted)
        qr.make(fit=True)
        pil_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        local_path = save_qr_png(pil_img, app.qr_dir)
        self._last_qr_path = local_path

        app.db.insert(
            obj_id=obj_id,
            name=name,
            description=self.ti_description.text.strip(),
            category=self.ti_category.text.strip(),
            location=self.ti_location.text.strip(),
            qr_path=local_path,
        )

        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        self.img_preview.texture = CoreImage(buf, ext="png").texture

        self.lbl_status.text = "Готово. ID: " + obj_id[:8]
        self.btn_save.disabled = False

    def _on_save_to_gallery(self, *_):
        if self._last_qr_path:
            copy_to_gallery(self._last_qr_path)
            self.lbl_status.text = "Сохранено в галерею"
        self.btn_save.disabled = True