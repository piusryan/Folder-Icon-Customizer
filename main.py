"""Entry point - launches the Folder & Icon Customizer GUI."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow
from app.ui.theme import APP_STYLESHEET

APP_DIR = Path(__file__).resolve().parent


def _seed_icon_library() -> None:
    """Place the bundled .ico files from the project into the icons/ library."""
    icons_dir = APP_DIR / "icons"
    icons_dir.mkdir(exist_ok=True)
    for p in APP_DIR.glob("*.ico"):
        target = icons_dir / p.name
        if not target.exists():
            try:
                target.write_bytes(p.read_bytes())
            except OSError:
                pass


def main() -> int:
    _seed_icon_library()

    app = QApplication(sys.argv)
    app.setApplicationName("Folder & Icon Customizer")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()

    if sys.platform != "win32":
        QMessageBox.warning(
            window,
            "Windows Only",
            "Folder-icon customization (desktop.ini) only works on Windows. "
            "The converter and library still work on other platforms.",
        )

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
