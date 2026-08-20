"""Painter-rendered widget primitives."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QLinearGradient, QPainter

from src.core.theme import color


class BaseWidget:
    widget_type = "base"

    def __init__(self, x: int = 22, y: int = 22, width: int = 216, height: int = 38, **options: Any) -> None:
        self.bounds = QRectF(x, y, width, height)
        self.options = options
        self.theme: dict[str, Any] = {}
        self.data: dict[str, Any] = {}

    def update(self, data: dict[str, Any]) -> None:
        self.data = data

    def set_theme(self, theme: dict[str, Any]) -> None:
        self.theme = theme

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.widget_type,
            "x": int(self.bounds.x()),
            "y": int(self.bounds.y()),
            "width": int(self.bounds.width()),
            "height": int(self.bounds.height()),
            **self.options,
        }

    def draw(self, painter: QPainter) -> None:
        raise NotImplementedError

    def draw_bar(self, painter: QPainter, label: str, value: float | None, suffix: str = "%") -> None:
        x, y, width = self.bounds.x(), self.bounds.y(), self.bounds.width()
        shown = "Unavailable" if value is None else f"{value:.0f}{suffix}"
        painter.setPen(color(self.theme, "text", "#F0F0F0"))
        painter.setFont(QFont(self.theme.get("font", "Sans Serif"), 9))
        painter.drawText(int(x), int(y + 11), f"{label}  {shown}")
        track = QRectF(x, y + 18, width, 10)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color(self.theme, "track", "#14FFFFFF"))
        painter.drawRoundedRect(track, 5, 5)
        if value is None:
            return
        bounded = min(100.0, max(0.0, float(value)))
        fill_width = width * bounded / 100
        if fill_width <= 0:
            return
        key = "good" if bounded < 50 else "warning" if bounded < 80 else "critical"
        bar_color = color(self.theme, key, "#50DC78")
        gradient = QLinearGradient(x, y, x + fill_width, y)
        gradient.setColorAt(0, bar_color.lighter(120))
        gradient.setColorAt(1, bar_color)
        painter.setBrush(gradient)
        painter.drawRoundedRect(QRectF(x, y + 18, fill_width, 10), 5, 5)
