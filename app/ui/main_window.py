"""Main application window with a colourful top navigation bar."""

from __future__ import annotations

from PySide6.QtCore import Qt
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

from app.ui.converter_tab import ConverterTab
from app.ui.customizer_tab import CustomizerTab
from app.ui.gallery_tab import GalleryTab
from app.ui.theme import AMBER, CYAN, PINK, VIOLET, make_icon
from app.ui.widgets import Background, NavButton


class MainWindow(QMainWindow):
    APP_VERSION = "2.0.0"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Folders & Icons Studio")
        self.resize(980, 720)
        self.setMinimumSize(820, 600)

        root = Background()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_nav())

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: transparent; }")
        self.pages = {
            0: CustomizerTab(),
            1: ConverterTab(),
            2: GalleryTab(),
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

        lay.addStretch(1)
        self.nav_buttons[0].setChecked(True)
        return nav

    def select_page(self, index: int) -> None:
        for btn in self.nav_buttons:
            btn.setChecked(btn.index == index)
        self.stack.setCurrentIndex(index)
