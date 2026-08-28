"""Tab 2: PNG/JPG -> ICO converter with preview and batch handling."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.ico_converter import convert_image_to_ico
from app.ui.widgets import Card, Hero, labeled


class ConverterTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # scroll container so the section never crushes/overlaps its widgets
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
                "Image → ICO Studio",
                "Drop in any PNG, JPG or BMP — even a giant wallpaper — and it becomes "
                "a crisp multi-size Windows icon. Oversized images are auto-scaled to fit.",
            ),
            0,
        )

        # middle section: source | (preview + convert) in two columns
        mid = QHBoxLayout()
        mid.setSpacing(16)
        mid.addWidget(self._source_card(), 3)

        right = QWidget()
        right.setAttribute(Qt.WA_StyledBackground, False)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(16)
        right_lay.addWidget(self._preview_card(), 1)
        right_lay.addWidget(self._convert_card(), 1)
        mid.addWidget(right, 2)
        root.addLayout(mid, 0)

        root.addWidget(labeled("QUEUE"), 0)

        self._list = QListWidget()
        self._list.itemSelectionChanged.connect(self._update_preview)
        self._list.setMinimumHeight(100)
        root.addWidget(self._list, 1)

    def _source_card(self) -> QWidget:
        card = Card("Add your images", "Batch them up — we'll convert them all at once.")

        add_btn = QPushButton("  Add Images…")
        add_btn.clicked.connect(self._add_images)
        clear_btn = QPushButton("Clear All")
        clear_btn.setProperty("accent", "ghost")
        clear_btn.clicked.connect(self._clear)

        top = QHBoxLayout()
        self.src_label = QLabel("No images yet")
        self.src_label.setObjectName("CardSub")
        top.addWidget(self.src_label, 1)
        top.addWidget(add_btn)
        top.addWidget(clear_btn)
        card.body().addLayout(top)

        card.body().addSpacing(12)
        card.body().addWidget(labeled("OUTPUT FOLDER"))
        out_row = QHBoxLayout()
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("Leave empty = save beside each image")
        out_btn = QPushButton("Browse…")
        out_btn.setProperty("accent", "ghost")
        out_btn.clicked.connect(self._pick_output)
        out_row.addWidget(self.out_edit, 1)
        out_row.addWidget(out_btn)
        card.body().addLayout(out_row)

        card.body().addSpacing(12)
        card.body().addWidget(labeled("INCLUDE SIZES (PX)"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        self.size_checks: dict[int, QCheckBox] = {}
        for i, size in enumerate([16, 24, 32, 48, 64, 128, 256]):
            cb = QCheckBox(str(size))
            cb.setChecked(True)
            self.size_checks[size] = cb
            grid.addWidget(cb, i // 4, i % 4)
        card.body().addLayout(grid)
        card.body().addStretch(1)
        return card

    def _preview_card(self) -> QWidget:
        card = Card("Preview", "The chosen image, alive before converting.")
        self.preview_img = QLabel()
        self.preview_img.setMinimumSize(120, 120)
        self.preview_img.setAlignment(Qt.AlignCenter)
        self.preview_img.setStyleSheet(
            "border-radius:14px; background:#14152a; border:1px solid #3a3b6b;"
        )
        self.preview_name = QLabel("Nothing selected")
        self.preview_name.setObjectName("CardSub")
        self.preview_name.setAlignment(Qt.AlignCenter)
        card.body().addWidget(self.preview_img, 0, Qt.AlignCenter)
        card.body().addWidget(self.preview_name, 0, Qt.AlignCenter)
        card.body().addStretch(1)
        return card

    def _convert_card(self) -> QWidget:
        card = Card("Convert", "Make it an icon!")
        self.convert_btn = QPushButton("  Convert to .ico")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self._convert)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.status = QLabel("Ready when you are")
        self.status.setObjectName("CardSub")
        card.body().addWidget(self.convert_btn)
        card.body().addWidget(self.progress)
        card.body().addWidget(self.status)
        card.body().addStretch(1)
        return card

    # -- data -------------------------------------------------------------
    def _files(self) -> list[str]:
        return [self._list.item(i).data(Qt.UserRole) for i in range(self._list.count())]

    # -- slots ------------------------------------------------------------
    def _add_images(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if not paths:
            return
        existing = set(self._files())
        for p in paths:
            if p in existing:
                continue
            item = QListWidgetItem(Path(p).name)
            item.setData(Qt.UserRole, p)
            item.setToolTip(p)
            self._list.addItem(item)
        if self._list.count():
            self.convert_btn.setEnabled(True)
        self._update_src_label()
        self._select_last()

    def _clear(self) -> None:
        self._list.clear()
        self.convert_btn.setEnabled(False)
        self._update_src_label()
        self.preview_img.clear()
        self.preview_name.setText("Nothing selected")
        self.progress.setValue(0)
        self.status.setText("Ready when you are")

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self.out_edit.setText(d)

    def _select_last(self) -> None:
        if self._list.count():
            self._list.setCurrentRow(self._list.count() - 1)

    def _update_src_label(self) -> None:
        n = self._list.count()
        base = "No images yet" if n == 0 else f"{n} image(s)"
        if n:
            total = 0
            for p in self._files():
                try:
                    total += Path(p).stat().st_size
                except OSError:
                    pass
            self.src_label.setText(f"{base}  ·  ~{total / 1024 / 1024:.2f} MB")
        else:
            self.src_label.setText(base)

    def _update_preview(self) -> None:
        items = self._list.selectedItems()
        if not items:
            return
        path = items[0].data(Qt.UserRole)
        pix = QPixmap(path)
        self.preview_img.setPixmap(
            pix.scaled(
                self.preview_img.width() or 132,
                self.preview_img.height() or 132,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        self.preview_name.setText(Path(path).name)

    def _selected_sizes(self) -> list[int]:
        return [s for s, cb in self.size_checks.items() if cb.isChecked()] or [32]

    def _convert(self) -> None:
        files = self._files()
        if not files:
            return
        sizes = self._selected_sizes()
        out_dir = Path(self.out_edit.text().strip()) if self.out_edit.text().strip() else None

        self.convert_btn.setEnabled(False)
        total = len(files)
        results: list[str] = []
        errors: list[str] = []
        for i, path in enumerate(files):
            try:
                src = Path(path)
                target = out_dir / f"{src.stem}.ico" if out_dir else src.with_suffix(".ico")
                if out_dir and not out_dir.exists():
                    out_dir.mkdir(parents=True, exist_ok=True)
                res = convert_image_to_ico(src, target, sizes=sizes)
                line = f"  • {src.name} → {res.output_path}"
                if res.was_downscaled:
                    fw, fh = res.from_size
                    line += f"  (auto-scaled {fw}×{fh} → {res.source_size[0]}×{res.source_size[1]})"
                results.append(line)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{Path(path).name}: {exc}")
            self.progress.setValue(int((i + 1) / total * 100))

        self.progress.setValue(100)
        self.convert_btn.setEnabled(True)

        msg = f"Converted {len(results)} file(s):\n" + "\n".join(results)
        if errors:
            msg += "\n\nErrors:\n"
            for e in errors:
                msg += f"  ✗ {e}\n"
        self.status.setText(f"Converted {len(results)} file(s)." if errors else "All converted!")
        QMessageBox.information(self, "Conversion Complete", msg)
