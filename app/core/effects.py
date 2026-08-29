"""Pillow-based icon compositing: fills, patterns, text overlays and effects.

This module turns a simple description (``IconSpec``) into a finished RGBA
pixel image that can be saved as PNG or multi-resolution ICO. It powers the
"Icon Studio" tab and the preset/pack system.

Rendering order (bottom → top):
  1. base fill   — solid colour, linear gradient or pattern
  2. rounded mask (``corner_radius``)
  3. shadow       — soft drop shadow behind the shape
  4. glow         — soft coloured halo behind the shape
  5. border       — stroke around the shape
  6. text/emoji   — optional centered overlay
  7. transparency — overall opacity
  8. blur         — optional Gaussian blur of the whole result
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Sizes emitted into a generated .ico by default (mirrors ico_converter).
DEFAULT_SIZES = [16, 24, 32, 48, 64, 128, 256]

#: Named patterns: each is a function(size, *colors) -> RGBA Image.
PATTERNS: dict[str, str] = {
    "solid": "Single flat colour",
    "linear": "Linear gradient (top → bottom)",
    "diagonal": "Diagonal gradient (corner → corner)",
    "radial": "Radial gradient (centre → edge)",
    "stripes": "Diagonal stripes",
    "dots": "Dotted texture",
    "grid": "Checkerboard grid",
    "waves": "Soft waves",
}


def _rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    """Parse ``#rrggbb`` (or ``#rrggbbaa``) into an RGBA tuple."""
    h = hex_color.lstrip("#")
    if not h:
        return (255, 255, 255, alpha)
    if len(h) == 6:
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        return (r, g, b, alpha)
    if len(h) == 8:
        r, g, b, a = (int(h[i : i + 2], 16) for i in (0, 2, 4, 6))
        return (r, g, b, a)
    return (255, 255, 255, alpha)


def _lerp(a: tuple[int, ...], b: tuple[int, ...], t: float) -> tuple[int, ...]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


# --------------------------------------------------------------------------
# Fills
# --------------------------------------------------------------------------
def _fill_solid(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size), _rgba(colors[0]))
    return img


def _fill_linear(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)
    cx, cy, cr = colors[0], colors[-1], _rgba
    for y in range(size):
        t = y / max(size - 1, 1)
        d.line([(0, y), (size, y)], fill=_lerp(cr(cx), cr(cy), t))
    return img


def _fill_diagonal(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)
    s = size * math.sqrt(2)
    cx, cy, cr = colors[0], colors[-1], _rgba
    for i in range(int(s) + 1):
        t = i / max(s, 1)
        c = _lerp(cr(cx), cr(cy), t)
        pt = i - size
        d.line([(pt, 0), (size, size - pt)], fill=c, width=3)
    return img


def _fill_radial(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)
    cx, cy, cr = colors[0], colors[-1], _rgba
    half = size / 2
    max_r = half * math.sqrt(2)
    for r in range(int(max_r) + 1):
        t = r / max(max_r, 1)
        c = _lerp(cr(cx), cr(cy), t)
        # draw concentric rounded outlines then flood-fill inner area with end colour
        d.ellipse([half - r, half - r, half + r, half + r], outline=c, width=4)
    d.ellipse([0, 0, size, size], fill=_rgba(colors[-1]))
    return img


def _fill_stripes(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size), _rgba(colors[0]))
    d = ImageDraw.Draw(img)
    c = _rgba(colors[-1])
    step = max(size // 8, 4)
    for x in range(-size, size, step):
        d.line([(x, 0), (x + size, size)], fill=c, width=max(size // 16, 2))
    return img


def _fill_dots(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size), _rgba(colors[0]))
    d = ImageDraw.Draw(img)
    c = _rgba(colors[-1])
    step = max(size // 8, 4)
    r = max(size // 10, 1)
    for y in range(step // 2, size, step):
        for x in range(step // 2, size, step):
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    return img


def _fill_grid(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size), _rgba(colors[0]))
    d = ImageDraw.Draw(img)
    c = _rgba(colors[-1])
    step = max(size // 8, 4)
    for x in range(0, size, step):
        d.line([(x, 0), (x, size)], fill=c, width=2)
    for y in range(0, size, step):
        d.line([(0, y), (size, y)], fill=c, width=2)
    return img


def _fill_waves(size: int, colors: list[str]) -> Image.Image:
    img = Image.new("RGBA", (size, size), _rgba(colors[0]))
    d = ImageDraw.Draw(img)
    c1, c2 = _rgba(colors[-1]), _rgba(colors[0])
    amp = size * 0.08
    freq = max(size * 0.12, 4)
    step = max(size // 24, 1)
    for y in range(size):
        prev_x = -amp
        for x in range(0, size, step):
            t = y / max(size - 1, 1)
            xx = x + amp * math.sin((x / freq) + (y * 0.4))
            c = _lerp(c1, c2, t)
            d.line([(prev_x, y), (xx, y)], fill=c, width=step)
            prev_x = xx
    return img


_FILL_FUNCS: dict[str, callable] = {
    "solid": _fill_solid,
    "linear": _fill_linear,
    "diagonal": _fill_diagonal,
    "radial": _fill_radial,
    "stripes": _fill_stripes,
    "dots": _fill_dots,
    "grid": _fill_grid,
    "waves": _fill_waves,
}


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def _drop_shadow(base: Image.Image, amount: int) -> Image.Image:
    """Return a padded image with a soft drop shadow behind ``base``."""
    pad = max(base.size[0] // 6, 4)
    canvas = Image.new("RGBA", (base.size[0] + pad * 2, base.size[1] + pad * 2), (0, 0, 0, 0))
    off = pad + max(base.size[0] // 24, 2)
    canvas.paste(base, (pad, pad + max(base.size[1] // 40, 1)), base)
    shadow = canvas.filter(ImageFilter.GaussianBlur(radius=max(pad * amount / 100, 1)))
    # blacken but keep same alpha silhouette
    alpha = shadow.split()[3]
    black = Image.new("RGBA", shadow.size, (0, 0, 0, 255))
    black.putalpha(alpha)
    black.alpha_composite(canvas)
    return black


def _glow(base: Image.Image, color: str, amount: int, size: int) -> Image.Image:
    """Return a padded image with a coloured halo behind ``base``."""
    pad = max(size // 6, 4)
    canvas = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    canvas.paste(base, (pad, pad), base)
    halo = canvas.filter(ImageFilter.GaussianBlur(radius=max(pad * amount / 100, 1)))
    c = _rgba(color)
    rc = Image.new("RGBA", halo.size, (c[0], c[1], c[2], c[3]))
    rc.putalpha(halo.split()[3])
    rc.alpha_composite(canvas)
    return rc


# --------------------------------------------------------------------------
# Public spec + renderer
# --------------------------------------------------------------------------
@dataclass
class IconSpec:
    """Everything needed to render one icon.

    ``pattern`` values are keys of :data:`PATTERNS`. When ``base_image`` is set
    it overrides the pattern/color fill. ``overlay_text`` may contain emoji —
    rendered into the centre of the icon if a usable font is found.
    """

    pattern: str = "gradient"
    colors: list[str] = field(default_factory=lambda: ["#6c5ce7", "#e84393"])
    base_image: str = ""
    corner_radius: int = 28
    shadow: int = 40
    glow: int = 0
    glow_color: str = "#0abde3"
    border: int = 0
    border_color: str = "#ffffff"
    opacity: int = 100
    blur: int = 0
    overlay_text: str = ""
    text_color: str = "#ffffff"
    size: int = 256

    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "colors": list(self.colors),
            "base_image": self.base_image,
            "corner_radius": self.corner_radius,
            "shadow": self.shadow,
            "glow": self.glow,
            "glow_color": self.glow_color,
            "border": self.border,
            "border_color": self.border_color,
            "opacity": self.opacity,
            "blur": self.blur,
            "overlay_text": self.overlay_text,
            "text_color": self.text_color,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IconSpec":
        known = cls.__dataclass_fields__.keys()
        clean = {k: v for k, v in (data or {}).items() if k in known}
        if not isinstance(clean.get("colors", []), list) or not clean.get("colors"):
            clean["colors"] = ["#6c5ce7", "#e84393"]
        return cls(**clean)


def _best_font(pixel_size: int) -> ImageFont.ImageFont | None:
    """Pick a usable proportional font for the overlay text, or None."""
    candidates = [
        "C:/Windows/Fonts/segoeuiemoji.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, pixel_size)
            except OSError:
                continue
    try:
        return ImageFont.load_default()
    except Exception:  # noqa: BLE001
        return None


def render_icon(spec: IconSpec) -> Image.Image:
    """Render ``spec`` into a square RGBA image of ``spec.size`` px."""
    size = max(1, spec.size)

    if spec.base_image and Path(spec.base_image).exists():
        with Image.open(spec.base_image) as src:
            base = src.convert("RGBA").resize((size, size), Image.LANCZOS)
    else:
        fill = _FILL_FUNCS.get(spec.pattern, _fill_linear)(size, spec.colors or ["#6c5ce7"])
        base = fill

    radius = max(0, min(int(spec.corner_radius), size // 2))
    if radius:
        mask = _rounded_mask(size, radius)
        base.putalpha(mask)

    canvas_size = size
    padding = 0

    shadowed = None
    if spec.shadow > 0:
        shadowed = _drop_shadow(base.copy(), spec.shadow)
        padding = max((shadowed.size[0] - size) // 2, 0)
        canvas_size = shadowed.size[0]

    glow_img = None
    if spec.glow > 0:
        glow_img = _glow(base.copy(), spec.glow_color, spec.glow, size)

    # Compose onto the largest canvas.
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    if glow_img is not None:
        # center glow behind base (glow already has its own padding)
        gx = (canvas_size - glow_img.size[0]) // 2
        gy = (canvas_size - glow_img.size[1]) // 2
        canvas.alpha_composite(glow_img, (gx, gy))
    if shadowed is not None:
        canvas.alpha_composite(shadowed, (0, 0))
    # draw base on top (offset slightly up to look like it sits above shadow)
    bx = (canvas_size - size) // 2
    by = (canvas_size - size) // 2 - padding
    canvas.alpha_composite(base, (bx, by))

    current = canvas

    if spec.border > 0:
        current = _apply_border(current, size, spec.border, spec.border_color, (bx, by, size, size))

    if spec.overlay_text:
        current = _apply_text(current, spec, (bx, by, size, size))

    if spec.opacity < 100:
        a = current.split()[3].point(lambda v: int(v * spec.opacity / 100))
        current.putalpha(a)

    if spec.blur > 0:
        current = current.filter(ImageFilter.GaussianBlur(radius=spec.blur))

    return current.crop((0, 0, canvas_size, canvas_size))


def _apply_border(img: Image.Image, size: int, width: int, color: str, box: tuple) -> Image.Image:
    r = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x, y, w, h = box
    d = ImageDraw.Draw(r)
    d.rounded_rectangle(
        [x, y, x + w - 1, y + h - 1],
        radius=max(0, min(size // 2, 16)),
        outline=_rgba(color),
        width=max(1, width),
    )
    img.alpha_composite(r)
    return img


def _apply_text(img: Image.Image, spec: IconSpec, box: tuple) -> Image.Image:
    x, y, w, h = box
    font = _best_font(max(w // 4, 18))
    if font is None:
        return img
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    text = spec.overlay_text
    fill = _rgba(spec.text_color)
    try:
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:  # noqa: BLE001
        tw = th = w // 2
    tx = x + (w - tw) // 2 - bbox[0]
    ty = y + (h - th) // 2 - bbox[1]
    try:
        d.text((tx, ty), text, font=font, fill=fill)
    except Exception:  # noqa: BLE001
        return img
    img.alpha_composite(overlay)
    return img


def save_png(spec: IconSpec, path: str | Path) -> Path:
    path = Path(path)
    render_icon(spec).save(path, format="PNG")
    return path


def read_ico_frames(path: str | Path) -> list[tuple[int, int, Image.Image]]:
    """Return ``[(size, width, image)]`` for every frame embedded in an .ico.

    The .ico container is parsed directly (Pillow only exposes one size), each
    embedded image is extracted into its own single-frame .ico and decoded. The
    first integer is the pixel size (used as the icon index selector value).
    """
    import io
    import struct

    path = Path(path)
    try:
        data = path.read_bytes()
    except OSError:
        return []

    if len(data) < 6 or data[:4] != b"\x00\x00\x01\x00":
        return []

    count = struct.unpack("<H", data[4:6])[0]
    entries = []
    for i in range(count):
        off = 6 + i * 16
        if off + 16 > len(data):
            break
        b, h, colors, _r, planes, bitcount, size, img_off = struct.unpack(
            "<BBBBHHII", data[off : off + 16]
        )
        width = b or 256
        height = h or 256
        if img_off + size > len(data):
            continue
        blob = data[img_off : img_off + size]
        entries.append((width, height, blob))

    frames: list[tuple[int, int, Image.Image]] = []
    for width, height, blob in entries:
        try:
            if not blob:
                continue
            # Wrap in a minimal single-image ICO so Pillow can decode it.
            wb = width if width < 256 else 0
            hb = height if height < 256 else 0
            entry = struct.pack("<BBBBHHII", wb, hb, 0, 0, 1, 32, len(blob), 6 + 16)
            wrapped = b"\x00\x00\x01\x00\x01\x00" + entry + blob
            img = Image.open(io.BytesIO(wrapped))
            img.load()
            img = img.convert("RGBA")
            frames.append((width, width, img))
        except Exception:  # noqa: BLE001
            continue

    # Deduplicate by size, preferring the first (typically highest quality).
    by_size: dict[int, tuple[int, Image.Image]] = {}
    for size, width, img in frames:
        by_size.setdefault(size, (width, img))
    sizes = sorted(by_size)
    return [(s, by_size[s][0], by_size[s][1]) for s in sizes]


def save_ico(spec: IconSpec, path: str | Path, sizes: list[int] | None = None) -> Path:
    """Render a multi-resolution .ico from ``spec``."""
    path = Path(path)
    sizes = sorted({s for s in (sizes or DEFAULT_SIZES) if 1 <= s <= 256})
    max_size = max(sizes)
    # Render the largest frame once and let Pillow thumbnail it down to every
    # requested size (same proven pattern as the image converter).
    rendered = render_icon(IconSpec(**{**spec.to_dict(), "size": max_size}))
    rendered = _center_crop(rendered, max_size)
    rendered.save(path, format="ICO", sizes=[(s, s) for s in sizes])
    return path


def brand_initials(name: str, max_letters: int = 2) -> str:
    """Return up to ``max_letters`` initials for a brand/company name.

    "Acme Co" -> "AC", "Open AI" -> "OA", "nova" -> "N".
    """
    words = [w for w in name.strip().split() if w]
    if not words:
        return ""
    if len(words) >= max_letters:
        return "".join(w[0] for w in words[:max_letters]).upper()
    # Few words: take first letter(s) repeated enough or use full short word
    return "".join(w[0] for w in words).upper() or name[0].upper()


def _center_crop(img: Image.Image, target: int) -> Image.Image:
    w, h = img.size
    if w == target and h == target:
        return img
    left = (w - target) // 2
    top = (h - target) // 2
    return img.crop((left, top, left + target, top + target))
