"""PNG/JPG/BMP -> ICO conversion utilities built on Pillow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

# Sizes emitted into a generated .ico by default.
DEFAULT_SIZES = [16, 24, 32, 48, 64, 128, 256]

# Highest dimension a source image may have before we automatically downscale.
DEFAULT_MAX_SIZE = 256


@dataclass
class ConvertResult:
    output_path: Path
    sizes_written: list[int]
    source_size: tuple[int, int]
    was_downscaled: bool
    from_size: tuple[int, int]


def _ensure_rgba(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        return img.convert("RGBA")
    # Flatten onto an opaque background then promote to RGBA so JPGs keep
    # their shape without any unwanted transparency.
    base = Image.new("RGB", img.size, (255, 255, 255))
    base.paste(img.convert("RGBA"), (0, 0), img.convert("RGBA"))
    return base.convert("RGBA")


def _fit_within(img: Image.Image, max_size: int) -> tuple[Image.Image, tuple[int, int]]:
    """Downscale ``img`` so its largest dimension <= ``max_size``.

    Aspect ratio is preserved. Returns ``(resized, original_size)``. If the
    image already fits, it is returned untouched.
    """
    w, h = img.size
    long_edge = max(w, h)
    if long_edge <= max_size:
        return img, img.size
    scale = max_size / long_edge
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    return img.resize((new_w, new_h), Image.LANCZOS), (w, h)


def convert_image_to_ico(
    source: str | Path,
    output: str | Path | None = None,
    sizes: list[int] | None = None,
    background_fill: bool = True,
    max_size: int = DEFAULT_MAX_SIZE,
) -> ConvertResult:
    """Convert a PNG/JPG/BMP image into a multi-resolution .ico file.

    Oversized images are automatically downscaled so their longest side fits
    within ``max_size`` (default 256 px) while keeping their aspect ratio, so
    they can be used as standard Windows icons.

    ``output`` defaults to the source name with an ``.ico`` extension in the
    same directory. ``sizes`` defaults to :data:`DEFAULT_SIZES`.
    """
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(f"Image not found: {source}")

    sizes = sorted(set(sizes or DEFAULT_SIZES))
    sizes = [s for s in sizes if 1 <= s <= 256]
    max_size = max(1, min(max_size, 256))

    if output is None:
        output = source.with_suffix(".ico")
    output = Path(output)

    if not output.parent.exists():
        output.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as img:
        img.load()
        source_size = img.size
        if img.mode in ("P", "1"):
            img = img.convert("RGBA")
        rgba = _ensure_rgba(img) if background_fill or img.mode not in ("RGBA",) else img.convert("RGBA")

        rgba, original = _fit_within(rgba, max_size)
        was_downscaled = original != rgba.size

        rgba.save(
            output,
            format="ICO",
            sizes=[(s, s) for s in sizes],
        )

    return ConvertResult(
        output_path=output,
        sizes_written=sizes,
        source_size=rgba.size,
        was_downscaled=was_downscaled,
        from_size=source_size,
    )
