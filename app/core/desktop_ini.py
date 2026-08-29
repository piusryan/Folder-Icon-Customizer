"""Windows folder-icon customization via desktop.ini + IconResource.

How it works on Windows:
  * A ``desktop.ini`` is placed inside the target folder.
  * It sets ``IconResource=path,index`` which points to the image (usually an
    .ico file, but any image file Windows can render also works).
  * Both the folder and the ``desktop.ini`` must have the ``+S`` (System) and
    ``+H`` (Hidden) attributes set for Explorer to honour the file, and the
    folder itself needs ``+R`` (ReadOnly) or ``+S`` for desktop.ini to apply.
"""

from __future__ import annotations

import ctypes
import shutil
from dataclasses import dataclass
from pathlib import Path

# ---- Win32 attribute flags ------------------------------------------------
FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4
FILE_ATTRIBUTE_DIRECTORY = 0x10

INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


def _get_attributes(path: str) -> int:
    attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
    if attrs == INVALID_FILE_ATTRIBUTES:
        raise OSError(f"Could not read attributes for: {path}")
    return int(attrs)


def _set_attributes(path: str, attrs: int) -> None:
    if not ctypes.windll.kernel32.SetFileAttributesW(path, attrs):
        raise OSError(f"Could not set attributes for: {path}")


@dataclass
class CustomizeResult:
    folder: Path
    icon_file: Path
    desktop_ini_written: bool
    attributes_applied: bool
    folders_customized: int = 1


def _fresh_attributes(existing: int, attr: int) -> int:
    """Return ``existing`` with ``attr`` bit turned off (clean base)."""
    return existing & ~attr


def customize_folder_icon(
    folder: str | Path,
    icon_file: str | Path,
    index: int = 0,
    recursive: bool = False,
) -> CustomizeResult:
    """Apply an icon to a folder (optionally recursing into sub-folders).

    The chosen icon is **copied into each target folder** and `desktop.ini`
    references that local copy by name only — so the customization is fully
    self-contained and never depends on the app's project directory. Explorer
    can relocate, delete or rename the project and the icon still works.
    """
    folder = Path(folder).resolve()
    icon_file = Path(icon_file).resolve()

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")
    if not icon_file.is_file():
        raise FileNotFoundError(f"Icon file not found: {icon_file}")

    targets = [folder]
    if recursive:
        targets = [folder, *sorted(p for p in folder.rglob("*") if p.is_dir())]

    copied = False
    for target in targets:
        # Bring the icon into the folder so desktop.ini can point at a local
        # copy instead of an absolute path into the project directory.
        local_icon = _copy_icon_into(target, icon_file)
        if local_icon != icon_file:
            copied = True
        content = (
            "[.ShellClassInfo]\r\n"
            f"IconResource={local_icon.name},{index}\r\n"
        )
        _write_desktop_ini(target / "desktop.ini", content)
        _apply_attributes(target)

    return CustomizeResult(
        folder=folder,
        icon_file=icon_file,
        desktop_ini_written=True,
        attributes_applied=True,
        folders_customized=len(targets),
    )


def _copy_icon_into(folder: Path, icon_file: Path) -> Path:
    """Copy ``icon_file`` into ``folder`` and return the local copy path.

    If the icon already lives inside ``folder`` it is referenced in place
    (no copy). The copied icon is marked Hidden+System so it carries the icon
    without cluttering the folder view.
    """
    try:
        icon_file.relative_to(folder)
        return icon_file
    except ValueError:
        pass

    dest = folder / icon_file.name
    # Let a previous read-only/system copy be overwritten cleanly.
    if dest.exists():
        try:
            _set_attributes(str(dest), 0)
        except OSError:
            pass
    try:
        shutil.copy2(icon_file, dest)
    except PermissionError as exc:
        raise PermissionError(
            f"Could not copy '{icon_file.name}' into '{folder}': {exc}"
        ) from exc
    try:
        _set_attributes(str(dest), FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
    except OSError:
        pass
    return dest


def _write_desktop_ini(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    _set_attributes(
        str(path),
        FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM,
    )


def _apply_attributes(folder: Path) -> None:
    """Ensure the folder has the System (+ ReadOnly) bits desktop.ini needs.

    NOTE: we deliberately do NOT set Hidden on the folder itself — Explorer
    would hide it from the user (that attribute belongs on desktop.ini only).
    """
    attrs = _get_attributes(str(folder))
    needed = FILE_ATTRIBUTE_SYSTEM | FILE_ATTRIBUTE_READONLY
    if attrs & needed != needed:
        _set_attributes(str(folder), attrs | needed)
    _notify_shell(folder)


def _notify_shell(folder: Path) -> None:
    """Tell Explorer to re-read the folder and refresh icons immediately.

    Sends two notifications:
      * ``SHCNE_UPDATEDIR`` — make Explorer re-read this folder's contents so
        it detects the new ``desktop.ini``.
      * ``SHCNE_ASSOCCHANGED`` — force the shell to rebuild its icon cache,
        which is what actually makes the new folder icon appear.
    """
    SHCNE_UPDATEDIR = 0x00000010
    SHCNE_ASSOCCHANGED = 0x08000000
    SHCNF_PATHW = 0x0005
    SHCNF_FLUSH = 0x1000
    shell32 = ctypes.windll.shell32
    try:
        # NOTE: the exported function is "SHChangeNotify", NOT "SHChangeNotifyW"
        # (it always takes wide strings). Using the W-suffixed name silently
        # fails on most systems, which is why folder icons never refreshed.
        shell32.SHChangeNotify(
            SHCNE_UPDATEDIR, SHCNF_PATHW, str(folder), None
        )
        shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_FLUSH, None, None)
    except Exception:  # noqa: BLE001 - refresh is cosmetic
        pass


def read_folder_icon(folder: str | Path) -> tuple[Path, int] | None:
    """Read a customized folder's icon from its ``desktop.ini``.

    Returns ``(resolved_icon_path, index)`` or ``None`` if the folder has no
    IconResource entry.
    """
    folder = Path(folder).resolve()
    ini = folder / "desktop.ini"
    if not ini.exists():
        return None
    try:
        indata = ini.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    for raw in indata.splitlines():
        line = raw.strip()
        if line.lower().startswith("iconresource="):
            value = line.split("=", 1)[1]
            path_part, _, idx_part = value.partition(",")
            path_part = path_part.strip().strip('"')
            icon = Path(path_part)
            if not icon.is_absolute():
                icon = (folder / icon).resolve()
            else:
                icon = icon.resolve()
            if not icon.exists():
                return None
            try:
                idx = int(idx_part) if idx_part.strip() else 0
            except ValueError:
                idx = 0
            return icon, idx
    return None


def copy_folder_style(source: str | Path, targets: list[str | Path]) -> tuple[int, list[str]]:
    """Clone one customized folder's icon onto many others.

    Returns ``(folders_customized, errors)``. The source folder must already
    be customized (have a ``desktop.ini`` with ``IconResource``); its icon file
    is copied into each target just like a normal apply.
    """
    source = Path(source).resolve()
    icon_info = read_folder_icon(source)
    if icon_info is None:
        raise FileNotFoundError(
            f"‘{source.name}’ has no customized icon. Style a source folder first."
        )
    icon, index = icon_info

    customized = 0
    errors: list[str] = []
    for t in targets:
        t = Path(t)
        try:
            customize_folder_icon(t, icon, index=index)
            customized += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{t}: {exc}")
    return customized, errors


def reset_folder_icon(folder: str | Path) -> bool:
    """Remove desktop.ini and its attributes, returning to the default icon."""
    folder = Path(folder).resolve()
    ini = folder / "desktop.ini"
    removed = False
    if ini.exists():
        try:
            ini.unlink()
            removed = True
        except OSError:
            try:
                ini.chmod(0o600)
                ini.unlink()
                removed = True
            except OSError:
                removed = False
    return removed


def repair_folder_visibility(folder: str | Path) -> bool:
    """Un-hide a folder that the old buggy code marked Hidden/System.

    The ``Hidden`` attribute on a folder hides it from Explorer (that bit is
    only meant for ``desktop.ini``). This clears ``Hidden`` — and, when no
    ``desktop.ini`` is present, ``System`` too — so a previously customized
    folder is visible again. Returns True if any attribute changed.
    """
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    attrs = _get_attributes(str(folder))
    clean = attrs & ~FILE_ATTRIBUTE_HIDDEN

    # Only drop System if there's no desktop.ini relying on it.
    if not (folder / "desktop.ini").exists():
        clean &= ~FILE_ATTRIBUTE_SYSTEM

    if clean != attrs:
        _set_attributes(str(folder), clean)
        _notify_shell(folder)
        return True
    return False
