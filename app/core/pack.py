"""Import/export icon packs.

A "pack" is a single ``.zip`` containing:

  * ``manifest.json`` — the :class:`Preset` (name, description, IconSpec),
  * ``icons/icon.png``   — a high-res rendered preview (512 px),
  * ``icons/icon.ico``   — a ready-to-use multi-size Windows icon.

Exporting lets a user share or archive a look they designed in Icon Studio;
importing installs the icon into the library and the preset into the presets
folder so it shows up immediately in the app.
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.core.effects import IconSpec, save_ico, save_png
from app.core.presets import Preset

PACK_EXPORT_SIZE = 512


@dataclass
class PackResult:
    path: Path
    preset: Preset


def export_pack(preset: Preset, target: str | Path | None = None) -> PackResult:
    """Render a preset into a shareable ``.zip`` pack.

    If ``target`` is omitted the pack is written to the ``exports/`` folder
    next to the app, named after the preset.
    """
    from app.core.presets import presets_dir

    if target is None:
        exports = presets_dir().parent / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        slug = "".join(c if c.isalnum() else "_" for c in preset.name).strip("_") or "icon"
        target = exports / f"{slug}.icp"

    target = Path(target)
    if not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)

    spec = IconSpec(**{**preset.spec.to_dict(), "size": PACK_EXPORT_SIZE})

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "icons").mkdir(parents=True)
        png_path = save_png(spec, tmp / "icons" / "icon.png")
        ico_path = save_ico(spec, tmp / "icons" / "icon.ico")
        manifest = tmp / "manifest.json"
        manifest.write_text(
            json.dumps(preset.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(manifest, "manifest.json")
            zf.write(png_path, "icons/icon.png")
            zf.write(ico_path, "icons/icon.ico")

    return PackResult(path=target, preset=preset)


def import_pack(source: str | Path) -> tuple[Preset, Path]:
    """Install a pack: copy its icon into the library and register its preset.

    Returns ``(preset, icon_path)``.
    """
    from app.core.presets import save_preset, presets_dir

    source = Path(source)
    lib = presets_dir().parent / "icons"
    lib.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source) as zf:
        manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
        preset = Preset.from_dict(manifest_data)
        # Copy the .ico into the library under the preset's name.
        ico_bytes = None
        for name in zf.namelist():
            lower = name.lower()
            if lower.endswith(".ico") or lower.endswith(".png"):
                ico_bytes = zf.read(name)
                break
        preset_path = save_preset(preset)

        icon_target = lib / f"{preset.name}.ico"
        if ico_bytes is not None:
            icon_target.write_bytes(ico_bytes)

    return preset, icon_target
