"""Explorer right-click menu integration (Windows only).

Adds a "Customize with Folder Icon Studio…" entry to the right-click menu of
folders (both the folder itself and its background). When clicked, Explorer
launches the app with the chosen folder pre-filled so the user can style it
immediately.

This writes to the per-machine ``HKEY_CLASSES_ROOT`` and therefore needs
administrator rights. ``install_context_menu`` returns a friendly error message
if elevation is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

MENU_NAME = "Customize with Folder Icon Studio…"
KEY_BASE = r"Directory\shell\FolderIconStudio"
KEY_BG = r"Directory\Background\shell\FolderIconStudio"

MENU_ICON = (
    r"C:\Windows\System32\imageres.dll,3"
)


def _command_line() -> str:
    """Build the command that launches this app with a folder argument."""
    exe = Path(sys.executable).resolve()
    root = Path(__file__).resolve().parent.parent.parent
    main_py = root / "main.py"
    # When frozen (PyInstaller), main.py sits next to the exe.
    if not main_py.exists():
        main_py = root / "main.py"
    cmd = f'"{exe}" "{main_py}" "%1"'
    return cmd


def _registered_keys() -> list[str]:
    return [KEY_BASE, KEY_BG]


def _write_menu(root_key, sub_key: str, command: str) -> None:
    import winreg

    with winreg.CreateKeyEx(root_key, sub_key, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_NAME)
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, MENU_ICON)
    command_key = sub_key + r"\command"
    with winreg.CreateKeyEx(root_key, command_key, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)


def install_context_menu() -> str | None:
    """Register the menu entries. Returns an error message or ``None`` on success."""
    if sys.platform != "win32":
        return "Explorer integration is Windows-only."
    import winreg

    command = _command_line()
    try:
        for sub in _registered_keys():
            _write_menu(winreg.HKEY_CLASSES_ROOT, sub, command)
    except PermissionError:
        return (
            "Administrator rights are required to add the Explorer menu. "
            "Rerun the app as Administrator."
        )
    except OSError as exc:
        return f"Could not register the menu: {exc}"
    return None


def uninstall_context_menu() -> str | None:
    """Remove the menu entries. Returns an error message or ``None`` on success."""
    if sys.platform != "win32":
        return "Explorer integration is Windows-only."
    import winreg

    try:
        for sub in _registered_keys():
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, sub + r"\command")
            except FileNotFoundError:
                pass
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, sub)
            except FileNotFoundError:
                pass
    except PermissionError:
        return "Administrator rights are required to remove the Explorer menu."
    except OSError as exc:
        return f"Could not remove the menu: {exc}"
    return None


def is_installed() -> bool:
    """True if the Explorer menu is currently registered."""
    if sys.platform != "win32":
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, KEY_BASE):
            return True
    except FileNotFoundError:
        return False
