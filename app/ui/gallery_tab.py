"""Tab 3: Icon library gallery - browse, preview and apply icons."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets import Hero

ICON_EXTS = {".ico", ".png", ".jpg", ".jpeg"}
FAVORITES_FILE = "favorites.json"


class GalleryTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dirs: list[Path] = []
        self._favorites: set[str] = set()
        self._build()
        self._load_favorites()
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
        import_pack_btn = QPushButton("  Import Pack…")
        import_pack_btn.setProperty("accent", "amber")
        import_pack_btn.setToolTip("Install a shared icon pack (.icp / .zip)")
        import_pack_btn.clicked.connect(self._import_pack)
        refresh = QPushButton("  Refresh")
        refresh.setProperty("accent", "ghost")
        refresh.clicked.connect(lambda: self._load(self.search.text()))

        self.menu_btn = QPushButton()
        self.menu_btn.setToolTip(
            "Add/remove a ‘Customize with Folder Icon Studio…’ entry to the "
            "Explorer right-click menu. Needs Administrator rights."
        )
        self.menu_btn.clicked.connect(self._toggle_context_menu)
        self._refresh_menu_button()

        self.fav_only = QCheckBox("★ Favorites only")
        self.fav_only.toggled.connect(lambda *_: self._load(self.search.text()))

        self.count_badge = QLabel("")
        self.count_badge.setStyleSheet(
            "background:#2c2d52; color:#9aa0c4; border-radius:10px; padding:4px 12px; font-weight:700;"
        )

        bar.addWidget(self.search, 1)
        bar.addWidget(self.fav_only)
        bar.addWidget(add_ico)
        bar.addWidget(import_pack_btn)
        bar.addWidget(add_dir)
        bar.addWidget(self.menu_btn)
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
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self._show_menu)
        root.addWidget(self.grid, 1)

    def _default_dirs(self) -> list[Path]:
        base = Path(__file__).resolve().parent.parent.parent
        return [base / "icons"]

    def _load(self, filter_text: str) -> None:
        self._dirs = list(self._default_dirs())
        for d in self._dirs:
            d.mkdir(exist_ok=True)
        filter_text = filter_text.lower()
        favs_only = self.fav_only.isChecked() if hasattr(self, "fav_only") else False
        self.grid.clear()
        seen: set[str] = set()
        for d in self._dirs:
            for p in sorted(d.iterdir()):
                key = str(p).lower()
                if p.suffix.lower() in ICON_EXTS and p.is_file() and key not in seen:
                    if filter_text and filter_text not in p.name.lower():
                        continue
                    fav = self._is_fav(p.name)
                    if favs_only and not fav:
                        continue
                    seen.add(key)
                    label = f"★ {p.name}" if fav else p.name
                    item = QListWidgetItem(QIcon(str(p)), label)
                    item.setData(Qt.UserRole, p)
                    item.setData(Qt.UserRole + 1, fav)
                    item.setToolTip(str(p))
                    self.grid.addItem(item)
        self.count_badge.setText(f" {self.grid.count()} icons ")

    # -- favorites -------------------------------------------------------
    def _favorites_file(self) -> Path:
        return self._default_dirs()[0] / FAVORITES_FILE

    def _load_favorites(self) -> None:
        try:
            data = json.loads(self._favorites_file().read_text(encoding="utf-8"))
            self._favorites = set(data.get("favorites", []))
        except (OSError, ValueError, TypeError):
            self._favorites = set()

    def _save_favorites(self) -> None:
        try:
            self._favorites_file().write_text(
                json.dumps({"favorites": sorted(self._favorites)}, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _is_fav(self, filename: str) -> bool:
        return filename.lower() in self._favorites

    def _toggle_favorite(self, item: QListWidgetItem) -> None:
        name = item.data(Qt.UserRole).name
        if name.lower() in self._favorites:
            self._favorites.discard(name.lower())
        else:
            self._favorites.add(name.lower())
        self._save_favorites()
        self._load(self.search.text())

    def _rename(self, item: QListWidgetItem) -> None:
        from PySide6.QtWidgets import QInputDialog

        p = item.data(Qt.UserRole)
        name, ok = QInputDialog.getText(self, "Rename Icon", "New file name:", text=p.stem)
        if not ok or not name.strip():
            return
        new = p.with_name(f"{name.strip()}{p.suffix}")
        if new.exists():
            QMessageBox.warning(self, "Rename Failed", "A file with that name already exists.")
            return
        try:
            p.rename(new)
        except OSError as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Rename Failed", str(exc))
            return
        # favourite key follows the file
        if p.name.lower() in self._favorites:
            self._favorites.discard(p.name.lower())
            self._favorites.add(new.name.lower())
            self._save_favorites()
        self._load(self.search.text())

    def _delete(self, item: QListWidgetItem) -> None:
        p = item.data(Qt.UserRole)
        box = QMessageBox(self)
        box.setWindowTitle("Delete Icon")
        box.setText(f"Delete ‘{p.name}’ from your library? The file will be removed.")
        box.addButton(QMessageBox.Cancel)
        box.addButton(QMessageBox.Delete)
        if box.exec() == QMessageBox.Delete:
            try:
                p.unlink()
                self._favorites.discard(p.name.lower())
                self._save_favorites()
                self._load(self.search.text())
            except OSError as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Delete Failed", str(exc))

    def _show_menu(self, pos) -> None:
        item = self.grid.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        fav = item.data(Qt.UserRole + 1)
        menu.addAction("★ Remove from Favorites" if fav else "☆ Add to Favorites",
                       lambda: self._toggle_favorite(item))
        menu.addSeparator()
        menu.addAction("Rename…", lambda: self._rename(item))
        menu.addAction("Delete", lambda: self._delete(item))
        menu.exec(self.grid.mapToGlobal(pos))

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

    def _import_pack(self) -> None:
        """Install a shared icon pack and refresh the gallery."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Icon Pack", "", "Icon Pack (*.icp *.zip);;All Files (*)"
        )
        if not path:
            return
        try:
            from app.core.pack import import_pack

            preset, icon = import_pack(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Import Failed", str(exc))
            return
        self._load(self.search.text())
        QMessageBox.information(
            self,
            "Imported",
            f"Preset ‘{preset.name}’ added to your library.\nIcon saved:\n{icon}",
        )

    def _refresh_menu_button(self) -> None:
        from app.core.shell_ext import is_installed

        if is_installed():
            self.menu_btn.setText("  Remove Explorer Menu")
            self.menu_btn.setProperty("accent", "danger")
        else:
            self.menu_btn.setText("  Add Explorer Menu")
            self.menu_btn.setProperty("accent", "ghost")
        try:
            self.menu_btn.style().unpolish(self.menu_btn)
            self.menu_btn.style().polish(self.menu_btn)
        except Exception:  # noqa: BLE001
            pass

    def _toggle_context_menu(self) -> None:
        from app.core.shell_ext import (
            install_context_menu,
            is_installed,
            uninstall_context_menu,
        )

        if is_installed():
            err = uninstall_context_menu()
            done = "Explorer right-click menu removed."
        else:
            err = install_context_menu()
            done = (
                "Explorer right-click menu added.\n\n"
                "Right-click a folder (or its background) and choose "
                "“Customize with Folder Icon Studio…”."
            )
        if err:
            QMessageBox.warning(self, "Explorer Menu", err)
            return
        self._refresh_menu_button()
        QMessageBox.information(self, "Explorer Menu", done)

    def _add_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Add Icon Folder")
        if d and d not in [str(x) for x in self._dirs]:
            self._dirs.append(Path(d))
            self._load(self.search.text())

    def _preview(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if Path(path).suffix.lower() == ".ico":
            self._show_index_grid(path)
            return

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
            self._apply_to_folder_path(str(path), index=0)

    def _show_index_grid(self, path: Path) -> None:
        """Show every icon embedded in a multi-image .ico, pick one to use."""
        from PIL import ImageQt

        from app.core.effects import read_ico_frames

        frames = read_ico_frames(path)
        if not frames:
            self._apply_to_folder_path(str(path), index=0)
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"{path.name} — built-in icons")
        dialog.resize(420, 360)
        lay = QVBoxLayout(dialog)
        hint = QLabel(f"{len(frames)} frames inside this .ico — pick one to apply.")
        hint.setObjectName("CardSub")
        lay.addWidget(hint)

        grid = QListWidget()
        grid.setViewMode(QListWidget.IconMode)
        grid.setIconSize(QSize(80, 80))
        grid.setGridSize(QSize(110, 108))
        grid.setResizeMode(QListWidget.Adjust)
        grid.setMovement(QListWidget.Static)
        grid.setSpacing(6)
        for size, _, img in frames:
            qimg = ImageQt.ImageQt(img)
            it = QListWidgetItem(
                QIcon(QPixmap.fromImage(qimg)), f"index {size}"
            )
            it.setData(Qt.UserRole, size)
            grid.addItem(it)
        lay.addWidget(grid, 1)

        apply_btn = QPushButton("  Apply Selected to Folder…")
        apply_btn.clicked.connect(lambda: self._apply_from_grid(path, grid))
        close_btn = QPushButton("Close")
        close_btn.setProperty("accent", "ghost")
        close_btn.clicked.connect(dialog.close)
        btnrow = QHBoxLayout()
        btnrow.addWidget(apply_btn)
        btnrow.addWidget(close_btn)
        btnrow.addStretch(1)
        lay.addLayout(btnrow)
        dialog.exec()

    def _apply_from_grid(self, path: Path, grid: QListWidget) -> None:
        idx_item = grid.currentItem()
        index = idx_item.data(Qt.UserRole) if idx_item else 0
        self._apply_to_folder_path(str(path), index=int(index))

    def _apply_to_folder_path(self, path: str, index: int = 0) -> None:
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

                customize_folder_icon(folder, path, index=index)
                QMessageBox.information(self, "Done", f"Icon applied to:\n{folder}")
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Apply Failed", str(exc))
