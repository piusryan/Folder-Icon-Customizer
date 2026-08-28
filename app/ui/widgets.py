"""Reusable, colourful building blocks for the app UI."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


def _rgba(r: int, g: int, b: int, a: int) -> QColor:
    return QColor(r, g, b, a)


class Background(QWidget):
    """Full-window background that paints an image behind a dark overlay.

    Uses ``clock.jpg`` in the project root when available; any image can be set
    via :attr:`image_path`. Child widgets render on top and receive mouse input
    normally.
    """

    image_path: str = ""
    overlay_stops = ((0.0, (12, 13, 30, 165)), (0.55, (15, 16, 36, 195)), (1.0, (11, 12, 26, 215)))

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        if not Background.image_path:
            base = self._project_root()
            for name in ("clock.jpg", "clock.png", "background.jpg"):
                candidate = base / name
                if candidate.exists():
                    Background.image_path = str(candidate)
                    break
        self.load_image()

    @staticmethod
    def _project_root() -> "Path":
        from pathlib import Path

        return Path(__file__).resolve().parent.parent.parent

    def load_image(self) -> None:
        from pathlib import Path

        if Background.image_path and Path(Background.image_path).exists():
            self._pixmap = QPixmap(Background.image_path)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        rect = self.rect()
        if self._pixmap and not self._pixmap.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scaled = self._pixmap.scaled(
                rect.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation,
            )
            painter.drawPixmap(rect, scaled)
        else:
            painter.fillRect(rect, "#0d0e1a")

        # dark overlay for readability
        grad = QLinearGradient(0, 0, rect.width(), rect.height())
        for pos, color in self.overlay_stops:
            grad.setColorAt(pos, _rgba(*color))
        painter.fillRect(rect, grad)
        painter.end()


def labeled(text: str, muted: bool = False, object_name: str = "SectionLabel") -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName(object_name)
    if muted:
        lbl.setProperty("muted", "true")
    return lbl


class Card(QFrame):
    """A rounded card container used to group related controls."""

    def __init__(self, title: str = "", sub: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 18, 18, 18)
        self._layout.setSpacing(10)

        if title:
            title_lbl = QLabel(title)
            title_lbl.setObjectName("CardTitle")
            self._layout.addWidget(title_lbl)
        if sub:
            sub_lbl = QLabel(sub)
            sub_lbl.setObjectName("CardSub")
            sub_lbl.setWordWrap(True)
            self._layout.addWidget(sub_lbl)

    def body(self) -> QVBoxLayout:
        return self._layout


class Hero(QFrame):
    """The colourful gradient banner on top of every feature tab."""

    def __init__(self, title: str, sub: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Hero")
        self.setMinimumHeight(96)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 18, 26, 18)
        lay.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("HeroTitle")
        sub_lbl = QLabel(sub)
        sub_lbl.setObjectName("HeroSub")
        sub_lbl.setWordWrap(True)

        lay.addWidget(title_lbl)
        lay.addWidget(sub_lbl)
        lay.addStretch(1)


class NavButton(QToolButton):
    """A colourful toggleable navigation button."""

    def __init__(self, text: str, icon: QIcon, index: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("NavButton")
        self.setText(text)
        self.setIcon(icon)
        self.setIconSize(icon.pixmap(22, 22).size())
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.index = index

    def on_click(self, callback: Callable[[int], None]) -> None:
        self.clicked.connect(lambda: callback(self.index))


def h_line() -> QLabel:
    line = QLabel()
    line.setFixedHeight(1)
    line.setStyleSheet("background:#2e2f55;")
    return line
