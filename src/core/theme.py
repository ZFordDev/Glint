"""Theme loading and color conversion."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from PyQt6.QtGui import QColor

THEME_FILE = Path(__file__).parents[1] / "themes.json"

# Single source of truth for the paintable color slots, shared by theme
# merging and settings validation.
THEME_COLOR_KEYS = (
    "background",
    "overlay_top",
    "overlay_bottom",
    "border",
    "text",
    "track",
    "good",
    "warning",
    "critical",
    "header",
    "footer",
)


def load_themes(path: Path = THEME_FILE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "default" in data:
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"default": {"font": "Sans Serif", "colors": {}}}


def load_theme(name: str = "default") -> dict[str, Any]:
    themes = load_themes()
    return deepcopy(themes.get(name, themes["default"]))


def build_theme(name: str = "default", overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return ``load_theme(name)`` with valid color overrides merged in.

    Unknown keys and values that cannot be parsed by QColor are ignored, and
    the base theme is never mutated.
    """
    theme = load_theme(name)
    colors = theme.setdefault("colors", {})
    for key, value in (overrides or {}).items():
        if key not in THEME_COLOR_KEYS or not isinstance(value, str):
            continue
        parsed = QColor(value)
        if not parsed.isValid():
            continue
        colors[key] = parsed.name(QColor.NameFormat.HexArgb)
    return theme


def color(theme: dict[str, Any], name: str, fallback: str) -> QColor:
    return QColor(theme.get("colors", {}).get(name, fallback))
