"""Load, validate, instantiate, and save user widget layouts."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.core.settings_storage import config_dir
from src.ui.widgets import WIDGET_TYPES, BaseWidget

GEOMETRY_FIELDS = ("x", "y", "width", "height")

DEFAULT_LAYOUT: dict[str, Any] = {
    "schema_version": 1,
    "width": 280,
    "height": 290,
    "widgets": [
        {"type": "cpu", "x": 22, "y": 30, "width": 236, "height": 38},
        {"type": "ram", "x": 22, "y": 72, "width": 236, "height": 38},
        {"type": "disk", "x": 22, "y": 114, "width": 236, "height": 38},
        {"type": "gpu_usage", "x": 22, "y": 156, "width": 236, "height": 38},
        {"type": "gpu_temp", "x": 22, "y": 198, "width": 236, "height": 38},
        {"type": "network", "x": 22, "y": 244, "width": 236, "height": 28},
    ],
}


def layout_path(name: str = "default") -> Path:
    safe_name = "".join(character for character in name if character.isalnum() or character in "-_") or "default"
    return config_dir() / f"{safe_name}_layout.json"


def _is_number(value: object) -> bool:
    # bool is an int subclass but is never valid geometry.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _valid_widget(definition: object) -> bool:
    """Accept only widget entries whose geometry fields will not crash QRectF."""
    if not isinstance(definition, dict) or definition.get("type") not in WIDGET_TYPES:
        return False
    for field in GEOMETRY_FIELDS:
        if field in definition and not _is_number(definition[field]):
            return False
    disk = definition.get("disk")
    return disk is None or isinstance(disk, str)


def load_layout(name: str = "default", path: Path | None = None) -> dict[str, Any]:
    target = path or layout_path(name)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("widgets"), list):
            raise TypeError  # caught below so wrong shapes fall back instead of escaping
        data["widgets"] = [item for item in data["widgets"] if _valid_widget(item)]
        return data
    except (OSError, json.JSONDecodeError, ValueError, TypeError):  # TypeError: malformed shape above
        return deepcopy(DEFAULT_LAYOUT)


def create_widgets(layout: dict[str, Any]) -> list[BaseWidget]:
    widgets = []
    for definition in layout.get("widgets", []):
        widget_type = definition.get("type")
        if widget_type in WIDGET_TYPES:
            options = {key: value for key, value in definition.items() if key != "type"}
            widgets.append(WIDGET_TYPES[widget_type](**options))
    return widgets


def save_layout(
    widgets: list[BaseWidget], width: int, height: int, name: str = "default", path: Path | None = None
) -> None:
    target = path or layout_path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "width": width,
        "height": height,
        "widgets": [widget.serialize() for widget in widgets],
    }
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
