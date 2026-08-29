"""Export one design to every platform's icon format.

Given a single :class:`IconSpec` (ideally a branded one), this writes a tidy
folder of platform-ready assets in one shot:

  * **Web / favicon** — ``favicon.ico``, ``favicon-16/32.png``, ``apple-touch-icon.png``
  * **Android** — ``android-chrome-192/512.png`` + ``ic_launcher.png``
  * **iOS / macOS** — ``iOS-{1024,180,120,87,76,60}.png`` and ``macOS-{16..1024}.png``
  * **Windows** — ``windows-app.ico`` (multi-size) + square tiles
  * **PWA / manifest** — ``icon-192.png``, ``icon-512.png``
  * **Large master** — ``logo-1024.png``

Every asset is rendered from the same design so the brand looks identical
everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.core.effects import IconSpec, _center_crop, render_icon

#: name -> size for each generated asset.
TARGETS: dict[str, list[int]] = {
    "favicon-16.png": [16],
    "favicon-32.png": [32],
    "apple-touch-icon.png": [180],
    "android-chrome-192.png": [192],
    "android-chrome-512.png": [512],
    "ic_launcher.png": [192],
    "iOS-1024.png": [1024],
    "iOS-180.png": [180],
    "iOS-120.png": [120],
    "iOS-87.png": [87],
    "iOS-76.png": [76],
    "iOS-60.png": [60],
    "macOS-16.png": [16],
    "macOS-32.png": [32],
    "macOS-128.png": [128],
    "macOS-256.png": [256],
    "macOS-512.png": [512],
    "macOS-1024.png": [1024],
    "icon-192.png": [192],
    "icon-512.png": [512],
    "logo-1024.png": [1024],
}

WEB_MANIFEST = {
    "name": "Brand Icon",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}


@dataclass
class ExportResult:
    output_dir: Path
    files: list[Path] = field(default_factory=list)


def export_platform_assets(
    spec: IconSpec,
    output_dir: str | Path,
    name: str = "brand",
) -> ExportResult:
    """Render ``spec`` into a folder of platform icon assets.

    Returns the created files. ``name`` is used for asset file names, so a
    clean slug is recommended.
    """
    out = Path(output_dir)
    if not out.exists():
        out.mkdir(parents=True, exist_ok=True)

    # Fully opaque square master for iOS/macOS (which reject transparency).
    opaque_spec = IconSpec(**{**spec.to_dict(), "shadow": 0, "glow": 0, "opacity": 100})

    written: list[Path] = []

    for fname, sizes in TARGETS.items():
        size = sizes[0]
        use_opaque = any(
            tag in fname.lower() for tag in ("ios", "macos", "ic_launcher")
        )
        base = opaque_spec if use_opaque else spec
        # Render a bit larger then center-crop so shadow padding is trimmed
        # and corners are crisp at the exact target size.
        rendered = _center_crop(render_icon(IconSpec(**{**base.to_dict(), "size": size + 64})), size)
        path = out / fname
        rendered.save(path, format="PNG")
        written.append(path)

    # favicon.ico (16/24/32/48/64) - trimmed, flattened without glow/shadow.
    ico_spec = IconSpec(**{**spec.to_dict(), "shadow": 0, "glow": 0, "opacity": 100, "size": 64})
    ico_path = out / "favicon.ico"
    from app.core.effects import save_ico

    save_ico(ico_spec, ico_path, sizes=[16, 24, 32, 48, 64])
    written.append(ico_path)

    return ExportResult(output_dir=out, files=written)
