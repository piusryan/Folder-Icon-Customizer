"""Tab 1: Apply a custom icon to a folder via desktop.ini."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.core.desktop_ini import (
    copy_folder_style,
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
        self.setAcceptDrops(True)

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
        card = Card("Choose your folder(s)", "Restyle one folder — or several at once.")

        self.folder_list = QListWidget()
        self.folder_list.setMinimumHeight(150)
        self.folder_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.folder_list.itemSelectionChanged.connect(self._active_folders)

        add = QPushButton("  Add Folder…")
        add.clicked.connect(self._pick_folder)
        rem = QPushButton("Remove Selected")
        rem.setProperty("accent", "ghost")
        rem.clicked.connect(self._remove_folders)

        self.count_label = QLabel("0 folders")
        self.count_label.setStyleSheet(
            "background:#2c2d52; color:#9aa0c4; border-radius:10px; padding:4px 12px; font-weight:700;"
        )

        top = QHBoxLayout()
        top.addWidget(self.count_label, 1)
        top.addWidget(add)
        top.addWidget(rem)

        self.recursive_check = QCheckBox("Also restyle every sub-folder with this icon")
        self.recursive_check.setEnabled(False)

        card.body().addLayout(top)
        card.body().addWidget(self.folder_list)
        card.body().addSpacing(4)
        card.body().addWidget(self.recursive_check)
        card.body().addStretch(1)

        # keep the live folder count accurate as items are added/removed
        self.folder_list.model().rowsInserted.connect(lambda *_: self._active_folders())
        self.folder_list.model().rowsRemoved.connect(lambda *_: self._active_folders())
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
        self.template_btn = QPushButton("  Copy Style From Folder…")
        self.template_btn.setProperty("accent", "cyan")
        self.template_btn.setToolTip(
            "Clone one already-customized folder's icon onto all the folders above"
        )
        self.template_btn.clicked.connect(self._template)

        note = QLabel("Tip: applying may take a couple of seconds for Explorer to refresh.")
        note.setObjectName("CardSub")

        lay.addWidget(self.apply_btn)
        lay.addWidget(self.reset_btn)
        lay.addWidget(self.template_btn)
        lay.addStretch(1)
        lay.addWidget(note)
        return bar

    # -- drag & drop ------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if self._drop_has_image(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = [
            u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()
        ]
        images = [p for p in paths if Path(p).suffix.lower() in self._image_exts()]
        if not images:
            event.ignore()
            return
        event.acceptProposedAction()
        self.icon_edit.setText(images[0])
        # If folders are already queued, apply immediately.
        if self._all_folders():
            self._apply()

    @staticmethod
    def _drop_has_image(event) -> bool:
        if not event.mimeData().hasUrls():
            return False
        return any(
            u.isLocalFile()
            and Path(u.toLocalFile()).suffix.lower()
            in {".ico", ".png", ".jpg", ".jpeg", ".bmp", ".gif"}
            for u in event.mimeData().urls()
        )

    @staticmethod
    def _image_exts() -> set[str]:
        return {".ico", ".png", ".jpg", ".jpeg", ".bmp", ".gif"}

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
        if not path:
            return
        if path in self._all_folders():
            return
        item = QListWidgetItem(path)
        item.setData(Qt.UserRole, path)
        self.folder_list.addItem(item)
        self._active_folders()
        self._repair_folder(path)

    def _remove_folders(self) -> None:
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))
        self._active_folders()

    def _all_folders(self) -> list[str]:
        return [
            self.folder_list.item(i).data(Qt.UserRole)
            for i in range(self.folder_list.count())
        ]

    def set_initial_folders(self, folders: list[str]) -> None:
        """Pre-populate the folder list (e.g. restore the last-used folder)."""
        for f in folders:
            if not f or f in self._all_folders():
                continue
            item = QListWidgetItem(f)
            item.setData(Qt.UserRole, f)
            self.folder_list.addItem(item)
        self._active_folders()

    def _repair_folder(self, folder: str | None = None) -> None:
        """Automatically un-hide a previously-customized folder (legacy artifact)."""
        for f in [folder] if folder else self._all_folders():
            if not f:
                continue
            try:
                p = Path(f).resolve()
                if p.is_dir():
                    repair_folder_visibility(p)
            except Exception:  # noqa: BLE001 - cosmetic, never block the user
                pass

    def _active_folders(self) -> list[str]:
        folders = [
            self.folder_list.item(i).data(Qt.UserRole)
            for i in range(self.folder_list.count())
        ]
        n = len(folders)
        self.count_label.setText(f"{n} folder{'s' if n != 1 else ''}")
        # Recursive option only makes sense for a single target folder.
        self.recursive_check.setEnabled(n == 1)
        if n != 1:
            self.recursive_check.setChecked(False)
        return folders

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
        folders = self._all_folders()
        icon = self._resolve_icon()
        if not folders:
            QMessageBox.warning(self, "Missing Folder", "Please add at least one folder first.")
            return
        if not icon:
            QMessageBox.warning(self, "Missing Icon", "Please choose an icon first.")
            return

        recursive = self.recursive_check.isChecked()
        index = self.index_slider.value()

        total_folders = 0
        errors: list[str] = []
        for folder in folders:
            try:
                res = customize_folder_icon(
                    folder, icon, index=index, recursive=recursive
                )
                total_folders += res.folders_customized
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{folder}: {exc}")

        if not total_folders and not errors:
            QMessageBox.warning(self, "Apply Failed", "No folders were customized.")
            return

        msg = f"Customized {total_folders} folder(s)\n\nIcon source:\n{icon}"
        if errors:
            msg += "\n\nSkipped:\n" + "\n".join(f"  ✗ {e}" for e in errors)
        msg += (
            "\n\nIt may take a few seconds for Explorer to refresh. "
            "If it does not, restart Explorer or refresh the folder."
        )
        QMessageBox.information(self, "Done", msg)

    def _reset(self) -> None:
        folders = self._all_folders()
        if not folders:
            QMessageBox.warning(self, "Missing Folder", "Please add at least one folder first.")
            return
        for folder in folders:
            reset_folder_icon(folder)
        scope = " / ".join(folders) if len(folders) <= 3 else f"{len(folders)} folders"
        QMessageBox.information(
            self,
            "Done",
            f"Folder icon reset for:\n{scope}\n\nExplorer may take a moment to refresh.",
        )

    def _template(self) -> None:
        """Clone one customized folder's icon onto every folder in the list."""
        folders = self._all_folders()
        if not folders:
            QMessageBox.warning(self, "Missing Folder", "Please add at least one folder first.")
            return
        source = QFileDialog.getExistingDirectory(
            self, "Choose a folder whose icon/style to copy"
        )
        if not source:
            return
        try:
            customized, errors = copy_folder_style(source, folders)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "No Customized Icon", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Copy Failed", str(exc))
            return
        msg = f"Copied the icon from ‘{source}’ onto {customized} folder(s)."
        if errors:
            msg += "\n\nSkipped:\n" + "\n".join(f"  ✗ {e}" for e in errors)
        msg += "\n\nExplorer may take a moment to refresh."
        QMessageBox.information(self, "Done", msg)
