import os

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
from ui_theme import (DANGER, DANGER_DOWN, SURFACE_HI, TEXT, TEXT_MUTED,
                      Card, RoundedButton, RoundedTextInput, confirm)

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
        self._edit_id = None
        self._build_ui()

    @property
    def is_editing(self):
        return self._edit_id is not None

    @property
    def current_id(self):
        return self._edit_id

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

        # Подсказки категорий: существующие значения из базы.
        self.suggest_box = BoxLayout(orientation="horizontal", size_hint_y=None,
                                     height=0, spacing=dp(6))
        form.add_widget(self.suggest_box)

        content.add_widget(form)

        self.btn_generate = RoundedButton(text="Сгенерировать QR",
                                          size_hint_y=None, height=dp(52))
        self.btn_generate.bind(on_release=self._on_generate)
        content.add_widget(self.btn_generate)

        self.btn_cancel_edit = RoundedButton(
            text="Отменить редактирование",
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
            bg_color=list(SURFACE_HI),
            bg_color_down=list(SURFACE_HI),
            text_color=list(TEXT),
        )
        self.btn_cancel_edit.bind(on_release=lambda *_: self.start_create())
        content.add_widget(self.btn_cancel_edit)

        self.btn_delete = RoundedButton(
            text="Удалить запись",
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
            bg_color=list(DANGER),
            bg_color_down=list(DANGER_DOWN),
            text_color=list(TEXT),
        )
        self.btn_delete.bind(on_release=self._on_delete)
        content.add_widget(self.btn_delete)

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

        self.ti_category.bind(text=self._refresh_suggestions)
        self._refresh_suggestions()

    def on_enter(self):
        self._refresh_suggestions()

    # ---------- режим создания / редактирования ----------

    def start_create(self):
        self._edit_id = None
        self.ti_name.text = ""
        self.ti_category.text = ""
        self.ti_location.text = ""
        self.ti_description.text = ""
        self._last_qr_path = None
        self.img_preview.source = ""
        self.lbl_status.text = ""
        self.btn_save.disabled = True
        self.btn_generate.text = "Сгенерировать QR"
        self._set_editing_buttons(False)
        self._refresh_suggestions()

    def start_edit(self, obj_id):
        app = App.get_running_app()
        obj = app.db.get(obj_id) if app else None
        if not obj:
            return
        self._edit_id = obj_id
        self.ti_name.text = obj.get("name") or ""
        self.ti_category.text = obj.get("category") or ""
        self.ti_location.text = obj.get("location") or ""
        self.ti_description.text = obj.get("description") or ""

        qr_path = obj.get("qr_path") or ""
        self._last_qr_path = qr_path if qr_path and os.path.exists(qr_path) else None
        self.img_preview.source = self._last_qr_path or ""
        self.btn_save.disabled = self._last_qr_path is None

        self.lbl_status.text = ""
        self.btn_generate.text = "Сохранить изменения"
        self._set_editing_buttons(True)
        self._refresh_suggestions()

    def _set_editing_buttons(self, editing):
        for btn in (self.btn_cancel_edit, self.btn_delete):
            btn.disabled = not editing
            btn.opacity = 1 if editing else 0
            btn.height = dp(44) if editing else 0

    # ---------- удаление ----------

    def _on_delete(self, *_):
        if not self.is_editing:
            return
        app = App.get_running_app()
        obj = app.db.get(self._edit_id) or {}
        name = str(obj.get("name") or "Эта запись")
        if len(name) > 60:
            name = name[:57] + "…"
        confirm(
            "Удалить запись?",
            "«" + name + "» будет удалена вместе с QR-кодом. "
            "Отменить это действие нельзя.",
            self._delete_current,
        )

    def _delete_current(self):
        app = App.get_running_app()
        if not app.db.delete(self._edit_id):
            self.lbl_status.text = "Запись уже удалена"
            return
        self.start_create()
        self.lbl_status.text = "Запись удалена"

    # ---------- подсказки категорий ----------

    def _refresh_suggestions(self, *_):
        app = App.get_running_app()
        if app is None or not hasattr(app, "db"):
            return
        try:
            stats = app.db.category_stats()
        except Exception:
            stats = []

        needle = " ".join(self.ti_category.text.split()).casefold()
        picks = []

        if needle:
            # Пользователь вводит текст — ищем совпадения среди существующих.
            for item in stats:
                category = item["category"]
                folded = category.casefold()
                if needle != folded and needle in folded:
                    picks.append(category)
                if len(picks) >= 3:
                    break
        else:
            # Поле пустое — две подсказки: самая частая и самая свежая.
            if stats:
                picks.append(stats[0]["category"])
            if len(stats) > 1:
                recent = max(stats, key=lambda s: s["last_used"])["category"]
                if recent.casefold() != picks[0].casefold():
                    picks.append(recent)

        self._set_suggestions(picks)

    def _set_suggestions(self, categories):
        self.suggest_box.clear_widgets()
        if not categories:
            self.suggest_box.height = 0
            return

        self.suggest_box.height = dp(40)
        for category in categories:
            chip = RoundedButton(
                text=category,
                font_size="13sp",
                size_hint_y=None,
                height=dp(36),
                bg_color=list(SURFACE_HI),
                bg_color_down=list(SURFACE_HI),
                text_color=list(TEXT),
            )
            chip.bind(on_release=lambda _x, c=category: self._apply_category(c))
            self.suggest_box.add_widget(chip)

    def _apply_category(self, category):
        self.ti_category.text = category
        self.ti_category.focus = False

    # ---------- сохранение ----------

    def _on_generate(self, *_):
        app = App.get_running_app()
        name = self.ti_name.text.strip()
        if not name:
            self.lbl_status.text = "Укажите название"
            return

        # Приводим категорию к уже существующему написанию,
        # чтобы не появлялись дубли «обувь»/«Обувь»/«Обувь ».
        category = app.db.canonical_category(self.ti_category.text)
        if category != self.ti_category.text:
            self.ti_category.text = category

        description = self.ti_description.text.strip()
        location = self.ti_location.text.strip()

        if self.is_editing:
            app.db.update(self._edit_id, name=name, description=description,
                          category=category, location=location)
            self.lbl_status.text = "Изменения сохранены"
            self._refresh_suggestions()
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
            description=description,
            category=category,
            location=location,
            qr_path=local_path,
        )

        if self.img_preview.source == local_path:
            self.img_preview.reload()
        else:
            self.img_preview.source = local_path

        self.lbl_status.text = "Готово. ID: " + obj_id[:8]
        self.btn_save.disabled = False
        self._refresh_suggestions()

    def _on_save_to_gallery(self, *_):
        if not self._last_qr_path:
            return
        if copy_to_gallery(self._last_qr_path):
            self.lbl_status.text = "Сохранено в галерею"
            self.btn_save.disabled = True
        else:
            self.lbl_status.text = "Не удалось сохранить в галерею"
