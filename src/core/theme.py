"""Theme loading and color conversion."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from PyQt6.QtGui import QColor

THEME_FILE = Path(__file__).parents[1] / "themes.json"


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


def color(theme: dict[str, Any], name: str, fallback: str) -> QColor:
    return QColor(theme.get("colors", {}).get(name, fallback))
