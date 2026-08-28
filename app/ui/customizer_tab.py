"""Tab 1: Apply a custom icon to a folder via desktop.ini."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.core.desktop_ini import (
    customize_folder_icon,
    repair_folder_visibility,
    reset_folder_icon,
)
from app.ui.widgets import Card, Hero, labeled


class CustomizerTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()
        self._refresh_suite()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(16)

        root.addWidget(
            Hero(
                "Style a Folder",
                "Pick any folder and give it a personality. Your icon lands instantly, "
                "and Explorer shows it off with a fresh look.",
            )
        )

        # Two-column layout: folder + icon
        columns = QHBoxLayout()
        columns.setSpacing(16)

        columns.addWidget(self._folder_card(), 1)
        columns.addWidget(self._icon_card(), 1)
        root.addLayout(columns, 1)

        root.addWidget(self._action_bar())

    # -- cards -------------------------------------------------------------
    def _folder_card(self) -> QWidget:
        card = Card("Choose your folder", "The folder you want to restyle.")

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("C:\\Users\\You\\Documents")
        self.folder_edit.setClearButtonEnabled(True)
        self.folder_edit.editingFinished.connect(self._repair_current_folder)

        browse = QPushButton("Browse…")
        browse.setProperty("accent", "ghost")
        browse.clicked.connect(self._pick_folder)

        row = QHBoxLayout()
        row.addWidget(self.folder_edit, 1)
        row.addWidget(browse)

        self.recursive_check = QCheckBox("Also restyle every sub-folder with this icon")

        card.body().addLayout(row)
        card.body().addSpacing(4)
        card.body().addWidget(self.recursive_check)
        card.body().addStretch(1)
        return card

    def _icon_card(self) -> QWidget:
        card = Card("Pick your icon", "A file from your library or anywhere on disk.")

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText(".ico, .png or .jpg file…")
        self.icon_edit.setClearButtonEnabled(True)
        browse_icon = QPushButton("Browse…")
        browse_icon.setProperty("accent", "ghost")
        browse_icon.clicked.connect(self._pick_icon)

        icon_row = QHBoxLayout()
        icon_row.addWidget(self.icon_edit, 1)
        icon_row.addWidget(browse_icon)

        card.body().addLayout(icon_row)

        card.body().addSpacing(12)
        card.body().addWidget(labeled("QUICK PICK FROM LIBRARY"))
        self.suite_combo = QComboBox()
        refresh = QPushButton("↻ Refresh")
        refresh.setProperty("accent", "ghost")
        refresh.clicked.connect(self._refresh_suite)
        combo_row = QHBoxLayout()
        combo_row.addWidget(self.suite_combo, 1)
        combo_row.addWidget(refresh)
        card.body().addLayout(combo_row)

        card.body().addSpacing(12)
        card.body().addWidget(labeled("ICON INDEX"))
        self.index_slider = QSlider(Qt.Horizontal)
        self.index_slider.setRange(0, 20)
        self.index_value = QLabel("0")
        self.index_value.setObjectName("CardTitle")
        self.index_value.setMinimumWidth(28)
        self.index_value.setAlignment(Qt.AlignCenter)
        idx_row = QHBoxLayout()
        idx_row.addWidget(self.index_slider, 1)
        idx_row.addWidget(self.index_value)
        self.index_slider.valueChanged.connect(
            lambda v: self.index_value.setText(str(v))
        )
        card.body().addLayout(idx_row)

        card.body().addStretch(1)
        return card

    def _action_bar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.apply_btn = QPushButton("  Apply Icon Now")
        self.apply_btn.clicked.connect(self._apply)
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.setProperty("accent", "danger")
        self.reset_btn.clicked.connect(self._reset)

        note = QLabel("Tip: applying may take a couple of seconds for Explorer to refresh.")
        note.setObjectName("CardSub")

        lay.addWidget(self.apply_btn)
        lay.addWidget(self.reset_btn)
        lay.addStretch(1)
        lay.addWidget(note)
        return bar

    # -- data --------------------------------------------------------------
    def _library_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent / "icons"

    def _refresh_suite(self) -> None:
        lib = self._library_dir()
        lib.mkdir(exist_ok=True)
        current = self.suite_combo.currentData()
        self.suite_combo.blockSignals(True)
        self.suite_combo.clear()
        self.suite_combo.addItem("— pick an icon from your library —", None)
        for p in sorted(lib.rglob("*")):
            if p.suffix.lower() in (".ico", ".png", ".jpg", ".jpeg"):
                self.suite_combo.addItem(QIcon(str(p)), p.name, str(p))
        if current:
            idx = self.suite_combo.findData(current)
            if idx >= 0:
                self.suite_combo.setCurrentIndex(idx)
        self.suite_combo.blockSignals(False)

    # -- slots -------------------------------------------------------------
    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.folder_edit.setText(path)
            self._repair_current_folder()

    def _repair_current_folder(self) -> None:
        """Automatically un-hide the entered folder (old-bug artifact).

        Runs when the path is committed via Browse or by finishing typing, so
        a previously-hidden folder is visible again — no manual attrib needed.
        """
        folder = self.folder_edit.text().strip()
        if not folder:
            return
        try:
            p = Path(folder).resolve()
            if p.is_dir():
                repair_folder_visibility(p)
        except Exception:  # noqa: BLE001 - cosmetic, never block the user
            pass

    def _pick_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            "",
            "Images (*.ico *.png *.jpg *.jpeg)",
        )
        if path:
            self.icon_edit.setText(path)

    def _resolve_icon(self) -> str | None:
        return self.icon_edit.text().strip() or self.suite_combo.currentData()

    def _apply(self) -> None:
        folder = self.folder_edit.text().strip()
        icon = self._resolve_icon()
        if not folder:
            QMessageBox.warning(self, "Missing Folder", "Please choose a folder first.")
            return
        if not icon:
            QMessageBox.warning(self, "Missing Icon", "Please choose an icon first.")
            return

        recursive = self.recursive_check.isChecked()
        try:
            res = customize_folder_icon(
                folder, icon, index=self.index_slider.value(), recursive=recursive
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Apply Failed", str(exc))
            return
        scope = f"{res.folders_customized} folder(s)" if recursive else folder
        QMessageBox.information(
            self,
            "Done",
            f"Icon applied to:\n{scope}\n\n"
            f"Icon source:\n{icon}\n\n"
            "It may take a few seconds for Explorer to refresh. "
            "If it does not, restart Explorer or refresh the folder."
        )

    def _reset(self) -> None:
        folder = self.folder_edit.text().strip()
        if not folder:
            QMessageBox.warning(self, "Missing Folder", "Please choose a folder first.")
            return
        reset_folder_icon(folder)
        QMessageBox.information(
            self,
            "Done",
            "Folder icon reset. Explorer may take a moment to refresh.",
        )
