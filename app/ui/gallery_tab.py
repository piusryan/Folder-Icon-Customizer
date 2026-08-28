"""Tab 3: Icon library gallery - browse, preview and apply icons."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets import Hero

ICON_EXTS = {".ico", ".png", ".jpg", ".jpeg"}


class GalleryTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dirs: list[Path] = []
        self._build()
        self._load("")

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(16)

        root.addWidget(
            Hero(
                "Icon Library",
                "Your whole collection in one colourful gallery. Double-click any icon "
                "for a big preview — then drop it straight onto a folder.",
            )
        )

        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter by name…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda t: self._load(t))

        add_dir = QPushButton("  Add Folder…")
        add_dir.setProperty("accent", "cyan")
        add_dir.clicked.connect(self._add_dir)
        add_ico = QPushButton("  Add ICO…")
        add_ico.setProperty("accent", "lime")
        add_ico.setToolTip(
            "Pick .ico files from anywhere — they get copied into the library folder"
        )
        add_ico.clicked.connect(self._add_ico_files)
        refresh = QPushButton("  Refresh")
        refresh.setProperty("accent", "ghost")
        refresh.clicked.connect(lambda: self._load(self.search.text()))

        self.count_badge = QLabel("")
        self.count_badge.setStyleSheet(
            "background:#2c2d52; color:#9aa0c4; border-radius:10px; padding:4px 12px; font-weight:700;"
        )

        bar.addWidget(self.search, 1)
        bar.addWidget(add_ico)
        bar.addWidget(add_dir)
        bar.addWidget(refresh)
        bar.addWidget(self.count_badge)
        root.addLayout(bar)

        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(64, 64))
        self.grid.setGridSize(QSize(104, 108))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setSpacing(6)
        self.grid.itemDoubleClicked.connect(self._preview)
        root.addWidget(self.grid, 1)

    def _default_dirs(self) -> list[Path]:
        base = Path(__file__).resolve().parent.parent.parent
        return [base / "icons"]

    def _load(self, filter_text: str) -> None:
        self._dirs = list(self._default_dirs())
        for d in self._dirs:
            d.mkdir(exist_ok=True)
        filter_text = filter_text.lower()
        self.grid.clear()
        seen: set[str] = set()
        for d in self._dirs:
            for p in sorted(d.iterdir()):
                key = str(p).lower()
                if p.suffix.lower() in ICON_EXTS and p.is_file() and key not in seen:
                    if filter_text and filter_text not in p.name.lower():
                        continue
                    seen.add(key)
                    item = QListWidgetItem(QIcon(str(p)), p.name)
                    item.setData(Qt.UserRole, p)
                    item.setToolTip(str(p))
                    self.grid.addItem(item)
        self.count_badge.setText(f" {self.grid.count()} icons ")

    def _add_ico_files(self) -> None:
        """Copy external .ico files into the project's icons/ library folder."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Icon Files",
            "",
            "Icons (*.ico);;All Files (*)",
        )
        if not paths:
            return
        lib = self._default_dirs()[0]
        lib.mkdir(parents=True, exist_ok=True)

        copied, skipped = 0, 0
        for p in paths:
            src = Path(p)
            target = lib / src.name
            if target.exists():
                skipped += 1
                continue
            try:
                shutil.copy2(src, target)
                copied += 1
            except OSError as exc:  # noqa: PERF203
                QMessageBox.warning(self, "Copy Failed", f"{src.name}: {exc}")

        self._load(self.search.text())
        msg = f"Added {copied} icon(s) to the library."
        if skipped:
            msg += f"\n{skipped} file(s) skipped (already exist)."
        QMessageBox.information(self, "Icons Added", msg)

    def _add_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Add Icon Folder")
        if d and d not in [str(x) for x in self._dirs]:
            self._dirs.append(Path(d))
            self._load(self.search.text())

    def _preview(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        box = QMessageBox(self)
        box.setWindowTitle(path.name)
        box.setIconPixmap(
            QPixmap(str(path)).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        pix = QPixmap(str(path))
        box.setInformativeText(f"{pix.width()}×{pix.height()}px\n\n{path}")
        apply_to_folder = box.addButton("Apply to Folder…", QMessageBox.ActionRole)
        box.addButton(QMessageBox.Close)
        box.exec()

        if box.clickedButton() is apply_to_folder:
            from PySide6.QtWidgets import QInputDialog

            folder, ok = QInputDialog.getText(
                self,
                "Apply Icon",
                "Folder path to apply this icon to:",
                text=str(Path.home()),
            )
            if ok and folder:
                try:
                    from app.core.desktop_ini import customize_folder_icon

                    customize_folder_icon(folder, str(path))
                    QMessageBox.information(self, "Done", f"Icon applied to:\n{folder}")
                except Exception as exc:  # noqa: BLE001
                    QMessageBox.critical(self, "Apply Failed", str(exc))
