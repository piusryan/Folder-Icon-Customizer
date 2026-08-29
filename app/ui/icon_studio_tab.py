"""Tab 4: Icon Studio — design, preview and export custom icons.

Users pick a fill (colour, gradient or pattern), add effects (shadow, glow,
border, opacity, blur) and an optional text/emoji overlay, see a live preview,
then export as PNG / ICO, save as a preset, or ship it as a shareable pack.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.core.effects import PATTERNS, IconSpec, render_icon, save_ico, save_png
from app.core.pack import export_pack, import_pack
from app.core.presets import Preset, builtin_presets, list_presets, save_preset
from app.ui.widgets import Card, Hero, labeled


class ColorButton(QPushButton):
    """A swatch button that opens a colour dialog and stores a hex colour."""

    def __init__(self, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.on_change: callable | None = None
        self._value = color
        self.setFixedSize(52, 32)
        self._paint()
        self.clicked.connect(self._pick)

    def _paint(self) -> None:
        self.setStyleSheet(
            f"QPushButton {{ border-radius:8px; border:2px solid #3a3c68;"
            f" background:{self._value}; }}"
            f"QPushButton:hover {{ border:2px solid #ffffff; }}"
        )

    def color(self) -> str:
        return self._value

    def set_color(self, color: str) -> None:
        self._value = color
        self._paint()

    def _pick(self) -> None:
        c = QColorDialog.getColor(QColor(self._value), self, "Pick colour")
        if c.isValid():
            self.set_color(c.name())
            if self.on_change:
                self.on_change()


class IconStudioTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._loading_preset = False
        self._states: list[dict] = []
        self._pos: int = -1
        self._commit_timer = QTimer(self)
        self._commit_timer.setSingleShot(True)
        self._commit_timer.setInterval(350)
        self._commit_timer.timeout.connect(self._commit_snapshot)
        self._build()
        self._reload_presets()
        self._populate_defaults()
        self._states = [self._spec().to_dict()]
        self._pos = 0
        self._wire_shortcuts()
        self._refresh_preview()

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer.addWidget(scroll)

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, False)
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(16)

        root.addWidget(
            Hero(
                "Icon Studio",
                "Compose a fresh folder icon from scratch: pick a fill, layer on "
                "glow, shadow and borders, drop in a text or emoji — then save it, "
                "preset it, or export a shareable pack.",
            ),
            0,
        )

        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(self._editor_card(), 3)
        row.addWidget(self._preview_card(), 2)
        root.addLayout(row, 0)

        root.addWidget(self._action_bar(), 0)

    def _editor_card(self) -> QWidget:
        card = Card("Design your icon", "Every control feeds a live preview.")
        b = card.body()

        self.preset_combo = QComboBox()
        b.addWidget(labeled("LOAD A PRESET"))
        b.addWidget(self.preset_combo)
        b.addSpacing(6)

        b.addWidget(labeled("FILL STYLE"))
        self.pattern_combo = QComboBox()
        for key, label in PATTERNS.items():
            self.pattern_combo.addItem(label, key)
        b.addWidget(self.pattern_combo)

        swatch = QHBoxLayout()
        self.color1 = ColorButton("#6c5ce7")
        self.color2 = ColorButton("#e84393")
        swatch.addWidget(self.color1)
        swatch.addWidget(self.color2)
        b.addLayout(swatch)

        self.base_image_edit = QLineEdit()
        self.base_image_edit.setPlaceholderText("Optional base image (overrides fill)…")
        self.base_image_edit.setClearButtonEnabled(True)
        pick_base = QPushButton("Browse…")
        pick_base.setProperty("accent", "ghost")
        pick_base.clicked.connect(self._pick_base_image)
        base_row = QHBoxLayout()
        base_row.addWidget(self.base_image_edit, 1)
        base_row.addWidget(pick_base)
        b.addLayout(base_row)

        b.addSpacing(6)

        self.shadow_slider = self._slider(b, "SHADOW", 0, 100, 40)
        self.glow_slider = self._slider(b, "GLOW", 0, 100, 0)

        glow_row = QHBoxLayout()
        self.glow_color = ColorButton("#0abde3")
        glow_row.addWidget(self.glow_color)
        glow_row.addStretch(1)
        b.addLayout(glow_row)

        self.border_slider = self._slider(b, "BORDER WIDTH", 0, 12, 0)

        border_row = QHBoxLayout()
        self.border_color = ColorButton("#ffffff")
        border_row.addWidget(self.border_color)
        border_row.addStretch(1)
        b.addLayout(border_row)

        self.radius_slider = self._slider(b, "CORNER RADIUS", 0, 128, 28)
        self.opacity_slider = self._slider(b, "OPACITY", 20, 100, 100)
        self.blur_slider = self._slider(b, "BLUR", 0, 30, 0)

        b.addSpacing(6)
        b.addWidget(labeled("TEXT / EMOJI OVERLAY"))
        text_row = QHBoxLayout()
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Text or emoji in the middle, e.g. ★ ♦ 🎮")
        self.text_edit.setClearButtonEnabled(True)
        self.text_color = ColorButton("#ffffff")
        text_row.addWidget(self.text_edit, 1)
        text_row.addWidget(self.text_color)
        b.addLayout(text_row)

        b.addStretch(1)
        return card

    def _slider(self, body: QVBoxLayout, label: str, lo: int, hi: int, default: int) -> QSlider:
        body.addWidget(labeled(label))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(default)
        slider.valueChanged.connect(self._on_change)
        body.addWidget(slider)
        return slider

    def _preview_card(self) -> QWidget:
        card = Card("Live preview", "What your icon looks like right now.")
        b = card.body()
        self.preview_img = QLabel()
        self.preview_img.setMinimumSize(196, 196)
        self.preview_img.setAlignment(Qt.AlignCenter)
        self.preview_img.setStyleSheet(
            "border-radius:16px; background:#14152a; border:1px solid #3a3b6b;"
        )
        self.preview_label = QLabel("")
        self.preview_label.setObjectName("CardSub")
        self.preview_label.setAlignment(Qt.AlignCenter)
        b.addWidget(self.preview_img, 0, Qt.AlignCenter)
        b.addWidget(self.preview_label, 0, Qt.AlignCenter)
        b.addStretch(1)
        return card

    def _action_bar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        undo_btn = QPushButton("  ↶ Undo")
        undo_btn.setEnabled(False)
        undo_btn.clicked.connect(self.undo)
        redo_btn = QPushButton("  ↷ Redo")
        redo_btn.setEnabled(False)
        redo_btn.clicked.connect(self.redo)
        self.undo_btn = undo_btn
        self.redo_btn = redo_btn

        png_btn = QPushButton("  Save as PNG")
        png_btn.setProperty("accent", "ghost")
        png_btn.clicked.connect(self._save_png)

        self.ico_btn = QPushButton("  Save as .ico")
        self.ico_btn.clicked.connect(self._save_ico)

        preset_btn = QPushButton("  Save as Preset")
        preset_btn.setProperty("accent", "cyan")
        preset_btn.clicked.connect(self._save_as_preset)

        export_btn = QPushButton("  Export Pack…")
        export_btn.setProperty("accent", "amber")
        export_btn.clicked.connect(self._export_pack)

        import_btn = QPushButton("  Import Pack…")
        import_btn.setProperty("accent", "lime")
        import_btn.clicked.connect(self._import_pack)

        lay.addWidget(undo_btn)
        lay.addWidget(redo_btn)
        lay.addWidget(png_btn)
        lay.addWidget(self.ico_btn)
        lay.addWidget(preset_btn)
        lay.addWidget(export_btn)
        lay.addWidget(import_btn)
        lay.addStretch(1)
        return bar

    # ------------------------------------------------------------ spec
    def _spec(self) -> IconSpec:
        return IconSpec(
            pattern=self.pattern_combo.currentData() or "linear",
            colors=[self.color1.color(), self.color2.color()],
            base_image=self.base_image_edit.text().strip(),
            corner_radius=self.radius_slider.value(),
            shadow=self.shadow_slider.value(),
            glow=self.glow_slider.value(),
            glow_color=self.glow_color.color(),
            border=self.border_slider.value(),
            border_color=self.border_color.color(),
            opacity=self.opacity_slider.value(),
            blur=self.blur_slider.value(),
            overlay_text=self.text_edit.text().strip(),
            text_color=self.text_color.color(),
        )

    def _populate_defaults(self) -> None:
        s = IconSpec()
        self.pattern_combo.setCurrentIndex(self.pattern_combo.findData(s.pattern))
        self.color1.set_color(s.colors[0])
        self.color2.set_color(s.colors[1])
        self.glow_color.set_color(s.glow_color)
        self.border_color.set_color(s.border_color)
        self.text_color.set_color(s.text_color)
        self.color1.on_change = self._on_change
        self.color2.on_change = self._on_change
        self.glow_color.on_change = self._on_change
        self.border_color.on_change = self._on_change
        self.text_color.on_change = self._on_change
        self.pattern_combo.currentIndexChanged.connect(self._on_change)
        self.base_image_edit.textChanged.connect(self._on_change)

    # ------------------------------------------------------------ presets
    def _reload_presets(self) -> None:
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("— choose a preset to load —", None)
        for p in builtin_presets() + list_presets():
            self.preset_combo.addItem(p.name, p)
        self.preset_combo.blockSignals(False)
        self.preset_combo.currentIndexChanged.connect(self._load_preset)

    def _load_preset(self, index: int) -> None:
        preset = self.preset_combo.currentData()
        if preset is None:
            return
        self._set_spec_from_dict(preset.spec.to_dict())
        self._refresh_preview()

    # ------------------------------------------------------------ preview
    def _on_change(self) -> None:
        if not self._loading_preset:
            self._commit_timer.start()
            self._refresh_preview()

    # ------------------------------------------------------------ undo/redo
    def _wire_shortcuts(self) -> None:
        QShortcut(QKeySequence.Undo, self, activated=self.undo)
        QShortcut(QKeySequence.Redo, self, activated=self.redo)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.redo)

    def _commit_snapshot(self) -> None:
        snap = self._spec().to_dict()
        # Avoid duplicate consecutive states (e.g. a restart of the timer).
        if self._states and self._states[self._pos] == snap:
            return
        self._states = self._states[: self._pos + 1] + [snap]
        self._pos = len(self._states) - 1
        self._sync_undo_buttons()

    def _set_spec_from_dict(self, d: dict) -> None:
        s = IconSpec.from_dict(d)
        self._loading_preset = True
        idx = self.pattern_combo.findData(s.pattern)
        self.pattern_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.color1.set_color(s.colors[0] if s.colors else "#6c5ce7")
        self.color2.set_color(s.colors[1] if len(s.colors) > 1 else s.colors[0])
        self.base_image_edit.setText(s.base_image)
        self.radius_slider.setValue(s.corner_radius)
        self.shadow_slider.setValue(s.shadow)
        self.glow_slider.setValue(s.glow)
        self.glow_color.set_color(s.glow_color)
        self.border_slider.setValue(s.border)
        self.border_color.set_color(s.border_color)
        self.opacity_slider.setValue(s.opacity)
        self.blur_slider.setValue(s.blur)
        self.text_edit.setText(s.overlay_text)
        self.text_color.set_color(s.text_color)
        self._loading_preset = False

    def _go_to(self, pos: int) -> None:
        pos = max(0, min(len(self._states) - 1, pos))
        if pos < 0:
            return
        self._set_spec_from_dict(self._states[pos])
        self._pos = pos
        self._refresh_preview()
        self._sync_undo_buttons()

    def undo(self) -> None:
        if self._pos > 0:
            self._go_to(self._pos - 1)

    def redo(self) -> None:
        if self._pos < len(self._states) - 1:
            self._go_to(self._pos + 1)

    def _sync_undo_buttons(self) -> None:
        if hasattr(self, "undo_btn"):
            self.undo_btn.setEnabled(self._pos > 0)
            self.redo_btn.setEnabled(self._pos < len(self._states) - 1)

    def _refresh_preview(self) -> None:
        try:
            img = render_icon(IconSpec(**{**self._spec().to_dict(), "size": 180}))
        except Exception as exc:  # noqa: BLE001
            self.preview_img.clear()
            self.preview_label.setText(f"preview error: {exc}")
            return
        pix = _pixmap_from_rgba(img)
        self.preview_img.setPixmap(
            pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.preview_label.setText(
            f"{self.pattern_combo.currentText().lower()} · {img.size[0]}×{img.size[1]}px"
        )

    # ------------------------------------------------------------ actions
    def _pick_base_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Base Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self.base_image_edit.setText(path)

    def _save_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Icon as PNG", "folder-icon.png", "PNG Image (*.png)"
        )
        if path:
            spec = IconSpec(**{**self._spec().to_dict(), "size": 512})
            save_png(spec, path)
            self._show_info("Saved", f"PNG icon saved:\n{path}")

    def _save_ico(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Icon as ICO", "folder-icon.ico", "Windows Icon (*.ico)"
        )
        if path:
            if not path.lower().endswith(".ico"):
                path += ".ico"
            save_ico(self._spec(), path)
            self._show_info(
                "Saved",
                f"Multi-size .ico saved (16–256 px):\n{path}",
            )

    def _save_as_preset(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Save as Preset", "Preset name:")
        if not ok or not name.strip():
            return
        preset = Preset(name=name.strip(), description="", spec=self._spec())
        save_preset(preset)
        self._reload_presets()
        self._show_info(
            "Saved", f"Preset ‘{name.strip()}’ saved and added to the preset list."
        )

    def _export_pack(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Export Pack", "Pack name:")
        if not ok or not name.strip():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Icon Pack", f"{name.strip()}.icp", "Icon Pack (*.icp *.zip)"
        )
        if not path:
            return
        preset = Preset(name=name.strip(), description="", spec=self._spec())
        try:
            result = export_pack(preset, path)
        except Exception as exc:  # noqa: BLE001
            self._show_error("Export Failed", str(exc))
            return
        self._show_info("Exported", f"Icon pack exported to:\n{result.path}")

    def _import_pack(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Icon Pack", "", "Icon Pack (*.icp *.zip);;All Files (*)"
        )
        if not path:
            return
        try:
            preset, icon = import_pack(path)
        except Exception as exc:  # noqa: BLE001
            self._show_error("Import Failed", str(exc))
            return
        self._reload_presets()
        self._show_info(
            "Imported",
            f"Preset ‘{preset.name}’ added to your library.\nIcon saved:\n{icon}",
        )

    def _show_info(self, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.addButton(QMessageBox.Close)
        box.exec()

    def _show_error(self, title: str, text: str) -> None:
        QMessageBox.critical(self, title, text)


def _pixmap_from_rgba(img) -> QPixmap:
    from PIL import ImageQt

    return QPixmap.fromImage(ImageQt.ImageQt(img))
