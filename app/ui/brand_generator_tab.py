"""Tab 5: Brand Icon Generator — type a name, get a logo icon in seconds.

This is the flagship "demo-friendly" feature. Give it a company/product name,
pick a style and a palette, and it renders a polished branded icon (initials or
a tiny emoji) with all the Studio effects — then apply to folders, save as ICO,
or export the full multi-platform asset set in one click.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.effects import IconSpec, brand_initials, render_icon, save_ico, save_png
from app.core.exporters import export_platform_assets
from app.core.desktop_ini import customize_folder_icon
from app.ui.icon_studio_tab import ColorButton
from app.ui.widgets import Card, Hero, labeled


#: name -> (IconSpec template) for each quick style.
BRAND_STYLES: dict[str, IconSpec] = {
    "Modern Gradient": IconSpec(
        pattern="linear", colors=["#6c5ce7", "#0abde3"], corner_radius=32,
        shadow=50, glow=55, glow_color="#0abde3", text_color="#ffffff",
    ),
    "Neon Pop": IconSpec(
        pattern="radial", colors=["#e84393", "#f39c12"], corner_radius=30,
        shadow=55, glow=75, glow_color="#ff00ff", text_color="#ffffff",
    ),
    "Corporate Blue": IconSpec(
        pattern="linear", colors=["#0f4c81", "#4a90d9"], corner_radius=14,
        shadow=40, border=2, border_color="#ffffff", text_color="#ffffff",
    ),
    "Prestige Gold": IconSpec(
        pattern="diagonal", colors=["#1a1a2e", "#d4af37"], corner_radius=30,
        shadow=50, glow=30, glow_color="#f5d76e", text_color="#f5d76e",
    ),
    "Gaming Volt": IconSpec(
        pattern="grid", colors=["#120f1f", "#39ff14"], corner_radius=22,
        shadow=55, glow=70, glow_color="#39ff14", border=2, border_color="#39ff14",
        text_color="#ffffff",
    ),
    "Minimal Dark": IconSpec(
        pattern="solid", colors=["#2f3640"], corner_radius=0,
        shadow=25, text_color="#ffffff",
    ),
}


class BrandGeneratorTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()
        self._wire()
        self._refresh_preview()

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
                "Brand Icon Generator",
                "Type a company or product name, pick a style, and get a polished "
                "branded icon in seconds — perfect for demos. Then apply it, save it, "
                "or export a full platform asset set.",
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
        card = Card("The essentials", "Everything you need for a brand icon.")
        b = card.body()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Acme Studio, OpenBox, Nova…")
        self.name_edit.setClearButtonEnabled(True)
        b.addWidget(labeled("BRAND / COMPANY NAME"))
        b.addWidget(self.name_edit)
        b.addSpacing(6)

        self.style_combo = QComboBox()
        for key in BRAND_STYLES:
            self.style_combo.addItem(key)
        b.addWidget(labeled("STYLE"))
        b.addWidget(self.style_combo)
        b.addSpacing(6)

        b.addWidget(labeled("PALETTE (secondary colour of the two nearest swatches)"))
        swatch = QHBoxLayout()
        self.color1 = ColorButton("#6c5ce7")
        self.color2 = ColorButton("#0abde3")
        swatch.addWidget(self.color1)
        swatch.addWidget(self.color2)
        b.addLayout(swatch)
        b.addSpacing(6)

        self.emoji_edit = QLineEdit()
        self.emoji_edit.setPlaceholderText("Optional emoji instead of initials, e.g. 🚀")
        self.emoji_edit.setClearButtonEnabled(True)
        b.addWidget(labeled("EMOJI (optional)"))
        b.addWidget(self.emoji_edit)

        b.addWidget(labeled("SHOWING"))
        self.mode_label = QLabel("")
        self.mode_label.setObjectName("CardSub")
        b.addWidget(self.mode_label)

        b.addStretch(1)
        return card

    def _preview_card(self) -> QWidget:
        card = Card("Live preview", "Your brand icon, rendered instantly.")
        b = card.body()
        self.preview_img = QLabel()
        self.preview_img.setMinimumSize(176, 176)
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

        apply_btn = QPushButton("  Apply to Folder…")
        apply_btn.clicked.connect(self._apply_to_folder)

        ico_btn = QPushButton("  Save as .ico")
        ico_btn.setProperty("accent", "ghost")
        ico_btn.clicked.connect(self._save_ico)

        png_btn = QPushButton("  Save as PNG")
        png_btn.setProperty("accent", "ghost")
        png_btn.clicked.connect(self._save_png)

        export_btn = QPushButton("  Export All Platforms…")
        export_btn.setProperty("accent", "cyan")
        export_btn.clicked.connect(self._export_platforms)

        lay.addWidget(apply_btn)
        lay.addWidget(ico_btn)
        lay.addWidget(png_btn)
        lay.addWidget(export_btn)
        lay.addStretch(1)
        return bar

    # ------------------------------------------------------------ data
    def _style(self) -> IconSpec:
        return BRAND_STYLES[self.style_combo.currentText()]

    def _brand_name(self) -> str:
        return self.name_edit.text().strip()

    def _brand_text(self) -> str:
        emoji = self.emoji_edit.text().strip()
        if emoji:
            return emoji
        return brand_initials(self._brand_name() or "Brand")

    def _spec(self) -> IconSpec:
        base = self._style()
        return IconSpec(
            pattern=base.pattern,
            colors=[self.color1.color(), self.color2.color()],
            corner_radius=base.corner_radius,
            shadow=base.shadow,
            glow=base.glow,
            glow_color=base.glow_color,
            border=base.border,
            border_color=base.border_color,
            text_color=base.text_color,
            overlay_text=self._brand_text(),
        )

    def _wire(self) -> None:
        self.name_edit.textChanged.connect(self._refresh_preview)
        self.emoji_edit.textChanged.connect(self._refresh_preview)
        self.style_combo.currentIndexChanged.connect(self._apply_style)
        self.color1.on_change = self._refresh_preview
        self.color2.on_change = self._refresh_preview

    def _apply_style(self) -> None:
        base = self._style()
        self.color1.set_color(base.colors[0])
        self.color2.set_color(base.colors[1] if len(base.colors) > 1 else base.colors[0])
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        text = self._brand_text()
        self.mode_label.setText(
            f"{self.style_combo.currentText()} · showing “{text}”"
        )
        spec = self._spec()
        try:
            img = render_icon(IconSpec(**{**spec.to_dict(), "size": 180}))
        except Exception as exc:  # noqa: BLE001
            self.preview_img.clear()
            self.preview_label.setText(f"preview error: {exc}")
            return
        from PySide6.QtGui import QImage

        from PIL import ImageQt

        qimage = ImageQt.ImageQt(img)
        self.preview_img.setPixmap(
            QPixmap.fromImage(qimage).scaled(
                176, 176, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.preview_label.setText(f"initial: “{text}” · {img.size[0]}×{img.size[1]}px")

    # ------------------------------------------------------------ actions
    def _save_ico(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Brand Icon as ICO",
            f"{self._file_slug()}.ico", "Windows Icon (*.ico)",
        )
        if path:
            if not path.lower().endswith(".ico"):
                path += ".ico"
            save_ico(self._spec(), path)
            self._info("Saved", f"Multi-size .ico saved:\n{path}")

    def _save_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Brand Icon as PNG",
            f"{self._file_slug()}.png", "PNG Image (*.png)",
        )
        if path:
            spec = IconSpec(**{**self._spec().to_dict(), "size": 512})
            save_png(spec, path)
            self._info("Saved", f"PNG icon saved:\n{path}")

    def _export_platforms(self) -> None:
        out_dir = QFileDialog.getExistingDirectory(
            self, "Choose export folder", str(Path.home() / "Desktop")
        )
        if not out_dir:
            return
        spec = IconSpec(**{**self._spec().to_dict(), "overlay_text": self._brand_text()})
        try:
            result = export_platform_assets(spec, out_dir, self._file_slug())
        except Exception as exc:  # noqa: BLE001
            self._info("Export Failed", str(exc))
            return
        self._info(
            "Exported",
            f"Wrote {len(result.files)} platform assets to:\n{result.output_dir}\n\n"
            "Includes favicon.ico, iOS, macOS, Android, Windows and web icons.",
        )

    def _apply_to_folder(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        folder, ok = QInputDialog.getText(
            self, "Apply to Folder", "Folder path:", text=str(Path.home())
        )
        if not ok or not folder:
            return
        try:
            customize_folder_icon(folder, self._spec_to_icon_file())
        except Exception as exc:  # noqa: BLE001
            self._info("Apply Failed", str(exc))
            return
        self._info("Done", f"Icon applied to:\n{folder}")

    def _spec_to_icon_file(self) -> str:
        import tempfile

        tmp = Path(tempfile.gettempdir()) / f"{self._file_slug()}_icon.png"
        return str(save_png(IconSpec(**{**self._spec().to_dict(), "size": 256}), tmp))

    def _file_slug(self) -> str:
        name = self._brand_name() or "brand"
        return "".join(c if c.isalnum() or c in "-_" else "" for c in name).strip() or "brand"

    def _info(self, title: str, text: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(text)
        box.addButton(QMessageBox.Close)
        box.exec()
