"""Cross-platform, painter-rendered Glint HUD shell."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QMenu, QWidget

from src.core.sensors import SensorReader
from src.core.settings_storage import load_settings, save_settings
from src.core.theme import color, load_theme
from src.ui.layout import create_widgets, load_layout, save_layout


class GlassHUD(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.theme = load_theme(self.settings["theme"])
        self.layout_data = load_layout(self.settings["layout"])
        self.widgets = create_widgets(self.layout_data)
        self.sensor_reader = SensorReader()
        self.drag_pos = None
        self.settings_window = None
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        bottom_hint = getattr(Qt.WindowType, "WindowStaysOnBottomHint", None)
        if bottom_hint is not None:
            flags |= bottom_hint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(int(self.layout_data.get("width", 280)), int(self.layout_data.get("height", 290)))
        self.setWindowOpacity(self.settings["opacity"])
        for widget in self.widgets:
            widget.set_theme(self.theme)
        position = self.settings["window"]
        if position["x"] is not None and position["y"] is not None:
            self.move(position["x"], position["y"])
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(self.settings["refresh_interval_ms"])
        self.update_stats()

    def update_stats(self) -> None:
        data = self.sensor_reader.get_all()
        for widget in self.widgets:
            widget.update(data)
        self.update()

    def apply_settings(self, settings: dict) -> None:
        self.settings = save_settings(settings)
        self.theme = load_theme(self.settings["theme"])
        self.setWindowOpacity(self.settings["opacity"])
        self.timer.setInterval(self.settings["refresh_interval_ms"])
        for widget in self.widgets:
            widget.set_theme(self.theme)
        self.update()

    def open_settings(self) -> None:
        from src.ui.settings import SettingsWindow

        if self.settings_window is None:
            # Retain it in Python without assigning a native parent. Parented
            # widgets are presented as tool panels on several desktops.
            self.settings_window = SettingsWindow(self.settings)
            self.settings_window.settings_changed.connect(self.apply_settings)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = int(self.theme.get("radius", 18))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color(self.theme, "background", "#B4121212"))
        painter.drawRoundedRect(rect, radius, radius)
        overlay = QLinearGradient(0, 0, 0, self.height())
        overlay.setColorAt(0, color(self.theme, "overlay_top", "#28FFFFFF"))
        overlay.setColorAt(1, color(self.theme, "overlay_bottom", "#0CFFFFFF"))
        painter.setBrush(overlay)
        painter.drawRoundedRect(rect, radius, radius)
        painter.setPen(QPen(color(self.theme, "border", "#2DFFFFFF"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
        for widget in self.widgets:
            widget.draw(painter)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            # Wayland rejects application-driven top-level positioning. Let
            # the window manager perform the drag, retaining manual movement
            # below as a fallback for backends that do not support this call.
            handle = self.windowHandle()
            if handle is not None and handle.startSystemMove():
                self.drag_pos = None
                event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            menu.addAction("Settings", self.open_settings)
            menu.addSeparator()
            menu.addAction("Exit", self._quit)
            menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if self.drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        self.drag_pos = None
        self.settings["window"] = {"x": self.x(), "y": self.y()}
        save_settings(self.settings)

    def _quit(self) -> None:
        save_layout(self.widgets, self.width(), self.height(), self.settings["layout"])
        QApplication.instance().quit()
