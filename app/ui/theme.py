"""Vibrant color system + stylesheet for the Folders & Icons app."""

# --- Palette (dark, low-brightness) ----------------------------------------
BG = "#0d0e1a"            # deep window background
BG_SOFT = "#141526"       # raised surface
CARD = "#1b1d30"          # card background (semi-transparent, dark)
CARD_SOLID = "#1b1d33"    # opaque card fallback
CARD_DEEP = "#12131f"     # inner surfaces

VIOLET = "#6c5ce7"
PINK = "#e84393"
CYAN = "#0abde3"
LIME = "#20c966"
AMBER = "#f39c12"

TEXT = "#eaeaff"
MUTED = "#9aa0c4"

# --- QSS --------------------------------------------------------------------
APP_STYLESHEET = f"""
QWidget {{
    color: {TEXT};
    font-family: 'Segoe UI', 'Cascadia Mono', 'Microsoft YaHei UI', sans-serif;
    font-size: 14px;
}}

QMainWindow, QDialog {{
    background: #0d0e1a;
}}

/* ================= Top navigation ================= */
QWidget#TopNav {{
    background: rgba(10, 11, 22, 235);
    border-bottom: 1px solid #23244a;
}}

QToolButton#NavButton {{
    background: transparent;
    color: {MUTED};
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 600;
}}
QToolButton#NavButton:hover {{
    background: #22233f;
    color: {TEXT};
}}
QToolButton#NavButton:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {VIOLET}, stop:1 #4a3fc0);
    color: white;
}}

QLabel#AppTitle {{
    color: white;
    font-size: 17px;
    font-weight: 800;
}}
QLabel#AppTitle span {{ color: {CYAN}; }}

/* ================= Hero banner ================= */
QFrame#Hero {{
    background: rgba(20, 20, 40, 150);
    border: 1px solid #2c2d55;
    border-radius: 18px;
}}
QLabel#HeroTitle {{
    color: white;
    font-size: 26px;
    font-weight: 800;
    background: transparent;
}}
QLabel#HeroSub {{
    color: #dcdcf5;
    background: transparent;
}}

/* ================= Cards ================= */
QFrame#Card {{
    background: rgba(22, 23, 40, 235);
    border: 1px solid #26274a;
    border-radius: 16px;
}}
QFrame#Card:hover {{ border: 1px solid #383a70; }}

QLabel#CardTitle {{
    color: white;
    font-size: 16px;
    font-weight: 700;
    background: transparent;
}}
QLabel#CardSub {{
    color: {MUTED};
    background: transparent;
}}
QLabel#SectionLabel {{
    color: {MUTED};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    background: transparent;
}}

/* ================= Buttons ================= */
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {VIOLET}, stop:1 #4f43c8);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 11px 20px;
    font-weight: 700;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #7a6ae8, stop:1 #5a4dd6);
}}
QPushButton:pressed {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #5a4bcc, stop:1 #3f37a8);
}}
QPushButton:disabled {{
    background: #26273f;
    color: #555a82;
}}

QPushButton[accent="pink"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {PINK}, stop:1 #b93278);
}}
QPushButton[accent="cyan"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #0f6f8c, stop:1 {CYAN});
    color: #04181f;
}}
QPushButton[accent="lime"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #14964a, stop:1 {LIME});
    color: #05160a;
}}
QPushButton[accent="amber"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #b87a0b, stop:1 {AMBER});
    color: #1e1100;
}}
QPushButton[accent="ghost"] {{
    background: rgba(30, 31, 55, 220);
    color: {TEXT};
    border: 1px solid #34365f;
}}
QPushButton[accent="ghost"]:hover {{
    background: #23243f;
    border: 1px solid #4a4c8a;
}}
QPushButton[accent="danger"] {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #c0392b, stop:1 #d35440);
}}

/* ================= Inputs ================= */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background: rgba(18, 19, 34, 235);
    border: 1px solid #2c2d55;
    border-radius: 10px;
    padding: 9px 12px;
    selection-background-color: {VIOLET};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
    border: 1px solid {VIOLET};
}}
QLineEdit:hover, QComboBox:hover {{
    border: 1px solid #42446f;
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    border: 6px solid transparent;
    border-top: 7px solid {MUTED};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: #14152a;
    color: {TEXT};
    border: 1px solid #2c2d55;
    selection-background-color: {VIOLET};
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: #22233f;
    border: none;
    width: 20px;
}}

/* ================= Checkboxes ================= */
QCheckBox {{
    spacing: 9px;
    color: #d7d9f2;
}}
QCheckBox::indicator {{
    width: 20px; height: 20px;
    border-radius: 6px;
    border: 2px solid #3a3c68;
    background: #14152a;
}}
QCheckBox::indicator:hover {{ border: 2px solid {VIOLET}; }}
QCheckBox::indicator:checked {{
    background: {VIOLET};
    border: 2px solid {VIOLET};
    image: none;
}}

/* ================= List / Grid gallery ================= */
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background: rgba(22, 23, 40, 230);
    border: 1px solid #27284a;
    border-radius: 14px;
    padding: 8px;
    margin: 6px;
    color: #d7d9f2;
}}
QListWidget::item:hover {{
    border: 1px solid #484a82;
    background: #23243f;
}}
QListWidget::item:selected {{
    border: 2px solid {VIOLET};
    background: #2b2c50;
    color: white;
}}

/* ================= Scrollbars ================= */
QScrollBar:vertical {{
    background: transparent; width: 11px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #2e2f55; border-radius: 5px; min-height: 34px;
}}
QScrollBar::handle:vertical:hover {{ background: {VIOLET}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 11px; margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: #2e2f55; border-radius: 5px; min-width: 34px;
}}
QScrollBar::handle:horizontal:hover {{ background: {VIOLET}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ================= Progress ================= */
QProgressBar {{
    background: rgba(18, 19, 34, 235);
    border: 1px solid #2c2d55;
    border-radius: 9px;
    text-align: center;
    color: white;
    min-height: 20px;
    font-weight: 700;
}}
QProgressBar::chunk {{
    border-radius: 9px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0f6f8c, stop:0.5 {VIOLET}, stop:1 {PINK});
}}

/* ================= Slider ================= */
QSlider::groove:horizontal {{
    height: 8px; background: #22233f; border-radius: 4px;
}}
QSlider::sub-page:horizontal {{
    background: {VIOLET}; border-radius: 4px;
}}
QSlider::handle:horizontal {{
    width: 20px; height: 20px; margin: -7px 0;
    border-radius: 10px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f6f8c, stop:1 {VIOLET});
}}

/* ================= Status bar ================= */
QStatusBar {{
    background: #0c0d18;
    color: {MUTED};
    border-top: 1px solid #22234a;
}}
QStatusBar::item {{ border: none; }}

/* ================= Message / Dialog ================= */
QMessageBox {{ background: #151627; }}
"""


def make_icon(color: str, glyph: str = "", size: int = 20) -> "QIcon":
    """Render a simple rounded-square icon with a gradient blob.

    Falls back to a plain symbol glyph if provided; otherwise draws a
    gradient rounded square circle.
    """
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPixmap

    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    if glyph:
        p.setPen(QColor("#ffffff"))
        font = p.font()
        font.setBold(True)
        font.setPixelSize(int(size * 0.7))
        p.setFont(font)
        p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, glyph)
        p.end()
        return QIcon(pm)

    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(color))
    c2 = QColor(color)
    c2.setAlpha(160)
    grad.setColorAt(1, c2)
    p.setBrush(grad)
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, size, size, size * 0.3, size * 0.3)
    p.end()
    return QIcon(pm)
