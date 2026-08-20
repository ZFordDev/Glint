"""Versioned JSON settings with validation and platform-native storage."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QStandardPaths

DEFAULT_SETTINGS: dict[str, Any] = {
    "schema_version": 1,
    "refresh_interval_ms": 1000,
    "opacity": 1.0,
    "theme": "default",
    "layout": "default",
    "window": {"x": None, "y": None},
}


def config_dir() -> Path:
    root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    path = Path(root or Path.home() / ".config" / "Glint")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _validated(data: object) -> dict[str, Any]:
    result = deepcopy(DEFAULT_SETTINGS)
    if not isinstance(data, dict):
        return result
    interval = data.get("refresh_interval_ms")
    if isinstance(interval, int) and 250 <= interval <= 60_000:
        result["refresh_interval_ms"] = interval
    opacity = data.get("opacity")
    if isinstance(opacity, (int, float)) and 0.2 <= opacity <= 1:
        result["opacity"] = float(opacity)
    for key in ("theme", "layout"):
        if isinstance(data.get(key), str) and data[key]:
            result[key] = data[key]
    window = data.get("window")
    if isinstance(window, dict):
        for coordinate in ("x", "y"):
            value = window.get(coordinate)
            if value is None or isinstance(value, int):
                result["window"][coordinate] = value
    return result


def load_settings(path: Path | None = None) -> dict[str, Any]:
    target = path or config_dir() / "settings.json"
    try:
        return _validated(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    target = path or config_dir() / "settings.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    clean = _validated(settings)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return clean
