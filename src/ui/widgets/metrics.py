from __future__ import annotations

from PyQt6.QtGui import QFont, QPainter

from src.core.theme import color

from .base import BaseWidget


class CpuWidget(BaseWidget):
    widget_type = "cpu"

    def draw(self, painter: QPainter) -> None:
        self.draw_bar(painter, "CPU", self.data.get("cpu"))


class RamWidget(BaseWidget):
    widget_type = "ram"

    def draw(self, painter: QPainter) -> None:
        self.draw_bar(painter, "RAM", self.data.get("ram"))


class DiskWidget(BaseWidget):
    widget_type = "disk"

    def draw(self, painter: QPainter) -> None:
        disks = self.data.get("disks", {})
        selected = self.options.get("disk")
        if selected not in disks:
            selected = next(iter(disks), None)
        self.draw_bar(painter, selected or "Disk", disks.get(selected) if selected else None)


class GpuTempWidget(BaseWidget):
    widget_type = "gpu_temp"

    def draw(self, painter: QPainter) -> None:
        self.draw_bar(painter, "GPU temp", self.data.get("temps", {}).get("gpu"), "°C")


class GpuUsageWidget(BaseWidget):
    widget_type = "gpu_usage"

    def draw(self, painter: QPainter) -> None:
        self.draw_bar(painter, "GPU", self.data.get("gpu", {}).get("usage"))


def _rate(value: float) -> str:
    units = ("B/s", "KB/s", "MB/s", "GB/s")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return "0 B/s"


class NetworkWidget(BaseWidget):
    widget_type = "network"

    def draw(self, painter: QPainter) -> None:
        network = self.data.get("network", {})
        painter.setPen(color(self.theme, "text", "#F0F0F0"))
        painter.setFont(QFont(self.theme.get("font", "Sans Serif"), 9))
        painter.drawText(
            int(self.bounds.x()),
            int(self.bounds.y() + 17),
            f"Network   ↓ {_rate(network.get('download', 0))}   ↑ {_rate(network.get('upload', 0))}",
        )
