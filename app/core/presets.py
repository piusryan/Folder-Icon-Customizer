"""Preset library: save, load and apply named icon looks (theme packs).

A "preset" bundles an :class:`app.core.effects.IconSpec` (colour, pattern,
effects, text overlay) with a name and description. Presets are stored as tiny
JSON files in the ``presets/`` folder next to the app, so users can:

  * save their current Icon Studio look for reuse,
  * load a built-in theme pack instantly,
  * share presets by copying the JSON (or via import/export packs).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.core.effects import IconSpec

PRESETS_DIR_NAME = "presets"


def presets_dir() -> Path:
    """The directory where user presets live (created on demand)."""
    base = Path(__file__).resolve().parent.parent.parent
    d = base / PRESETS_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class Preset:
    name: str
    spec: IconSpec
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "spec": self.spec.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Preset":
        return cls(
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            spec=IconSpec.from_dict(data.get("spec", {})),
        )


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip().replace(" ", "_")


def save_preset(preset: Preset) -> Path:
    """Write ``preset`` to the presets folder and return its path."""
    path = presets_dir() / f"{_slug(preset.name) or 'preset'}.json"
    path.write_text(
        json.dumps(preset.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def list_presets() -> list[Preset]:
    """Return every user preset, sorted by name."""
    out: list[Preset] = []
    for p in sorted(presets_dir().glob("*.json")):
        try:
            out.append(Preset.from_dict(json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, ValueError, TypeError):
            continue
    return out


# --------------------------------------------------------------------------
# Built-in theme packs
# --------------------------------------------------------------------------
# A small curated starter set so users get instant results. Each theme is a
# named colour scheme that renders nicely as a folder icon.
BUILTIN_THEMES: list[Preset] = [
    Preset(
        "Neon Glow",
        IconSpec(
            pattern="radial",
            colors=["#6c5ce7", "#0abde3"],
            corner_radius=32,
            shadow=55,
            glow=70,
            glow_color="#00ffff",
            border=2,
            border_color="#ffffff",
        ),
        "Vibrant radial violet with an electric cyan halo.",
    ),
    Preset(
        "Sunset",
        IconSpec(
            pattern="diagonal",
            colors=["#ff9a9e", "#fad0c4", "#fbc2eb"],
            corner_radius=32,
            shadow=50,
            glow=55,
            glow_color="#ff6b6b",
        ),
        "Warm pink-to-peach diagonal with a red glow.",
    ),
    Preset(
        "Ocean",
        IconSpec(
            pattern="linear",
            colors=["#0f4c81", "#0abde3", "#d4f1ff"],
            corner_radius=28,
            shadow=50,
            glow=45,
            glow_color="#0abde3",
            border=1,
            border_color="#ffffff",
        ),
        "Calm blue-to-cyan vertical gradient.",
    ),
    Preset(
        "Forest",
        IconSpec(
            pattern="waves",
            colors=["#1b4d3e", "#20c966"],
            corner_radius=28,
            shadow=45,
            glow=40,
            glow_color="#20c966",
        ),
        "Green waves with a soft lime glow.",
    ),
    Preset(
        "Neon Stripes",
        IconSpec(
            pattern="stripes",
            colors=["#1a1a2e", "#e84393", "#f39c12"],
            corner_radius=26,
            shadow=50,
            glow=60,
            glow_color="#e84393",
            border=2,
            border_color="#f39c12",
        ),
        "Dark base with bold pink stripes and amber border.",
    ),
    Preset(
        "Minimal Slate",
        IconSpec(
            pattern="solid",
            colors=["#2f3640"],
            corner_radius=0,
            shadow=30,
            border=0,
            opacity=95,
        ),
        "Understated flat square for a clean look.",
    ),
    Preset(
        "Cherry",
        IconSpec(
            pattern="dots",
            colors=["#ff6b81", "#f39c12"],
            corner_radius=32,
            shadow=45,
            glow=40,
            glow_color="#ff6b81",
        ),
        "Playful red dots on a soft warm base.",
    ),
    Preset(
        "Cyber Grid",
        IconSpec(
            pattern="grid",
            colors=["#120f1f", "#6c5ce7"],
            corner_radius=24,
            shadow=55,
            glow=65,
            glow_color="#6c5ce7",
            border=2,
            border_color="#6c5ce7",
            overlay_text="⌬",
            text_color="#ffffff",
        ),
        "Retro grid with a violet border and a chemical glyph.",
    ),
]


def builtin_presets() -> list[Preset]:
    """Return a deep-copy of the built-in theme packs."""
    return [_deepcopy_preset(p) for p in BUILTIN_THEMES]


def _deepcopy_preset(p: Preset) -> Preset:
    import copy

    return Preset(
        name=p.name,
        description=p.description,
        spec=IconSpec.from_dict(copy.deepcopy(p.spec.to_dict())),
    )
