"""Main application window with a colourful top navigation bar."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.brand_generator_tab import BrandGeneratorTab
from app.ui.converter_tab import ConverterTab
from app.ui.customizer_tab import CustomizerTab
from app.ui.gallery_tab import GalleryTab
from app.ui.icon_studio_tab import IconStudioTab
from app.ui.theme import AMBER, CYAN, LIME, PINK, VIOLET, make_icon
from app.ui.widgets import Background, NavButton


class MainWindow(QMainWindow):
    APP_VERSION = "2.0.0"

    def __init__(self, initial_folder: str | None = None) -> None:
        super().__init__()
        self._initial_folder = initial_folder
        self.settings = QSettings("FolderIconCustomizer", "FoldersAndIconsStudio")
        self.setWindowTitle("Folders & Icons Studio")
        self.resize(980, 720)
        self.setMinimumSize(820, 600)
        self._restore_geometry()

        root = Background()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_nav())

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: transparent; }")
        self.customizer = CustomizerTab()
        self._restore_last_folder()
        self.pages = {
            0: self.customizer,
            1: ConverterTab(),
            2: GalleryTab(),
            3: IconStudioTab(),
            4: BrandGeneratorTab(),
        }
        for _, page in self.pages.items():
            page.setAttribute(Qt.WA_StyledBackground, False)
            page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.stack.addWidget(page)
        root_layout.addWidget(self.stack, 1)

        self.setCentralWidget(root)
        self.statusBar().showMessage(
            f"Folders & Icons Studio v{self.APP_VERSION} — Make every folder yours."
        )
        if self._initial_folder:
            self.select_page(0)

    def _restore_geometry(self) -> None:
        try:
            w = int(self.settings.value("window/width", 980))
            h = int(self.settings.value("window/height", 720))
            self.resize(w, h)
        except (TypeError, ValueError):
            self.resize(980, 720)

    def _restore_last_folder(self) -> None:
        if self._initial_folder:
            self.customizer.set_initial_folders([self._initial_folder])
            return
        last = self.settings.value("lastFolder", "")
        if last:
            self.customizer.set_initial_folders([str(last)])

    def closeEvent(self, event) -> None:  # noqa: N802
        self.settings.setValue("window/width", self.width())
        self.settings.setValue("window/height", self.height())
        folders = self.customizer._all_folders()
        if folders:
            self.settings.setValue("lastFolder", folders[0])
        super().closeEvent(event)

    def _build_nav(self) -> QWidget:
        nav = QWidget()
        nav.setObjectName("TopNav")
        lay = QHBoxLayout(nav)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(8)

        title = QLabel('Folders <span style="color:#2BD9FE">&</span> Icons')
        title.setObjectName("AppTitle")
        lay.addWidget(title)
        lay.addSpacing(14)

        self.nav_buttons: list[NavButton] = []

        def add(text: str, color: str, glyph: str, index: int) -> QToolButton:
            btn = NavButton(text, make_icon(color, glyph, 22), index)
            btn.on_click(self.select_page)
            lay.addWidget(btn)
            self.nav_buttons.append(btn)
            return btn

        add("Style a Folder", VIOLET, "F", 0)
        add("Image → ICO", PINK, "I", 1)
        add("Icon Library", CYAN, "G", 2)
        add("Icon Studio", AMBER, "S", 3)
        add("Brand Maker", LIME, "B", 4)

        lay.addStretch(1)
        self.nav_buttons[0].setChecked(True)
        return nav

    def select_page(self, index: int) -> None:
        for btn in self.nav_buttons:
            btn.setChecked(btn.index == index)
        self.stack.setCurrentIndex(index)
