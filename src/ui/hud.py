"""Cross-platform, painter-rendered Glint HUD shell."""

from __future__ import annotations

import threading

from PyQt6.QtCore import QRectF, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QMenu, QWidget

from src.core.settings_storage import load_settings, save_settings
from src.core.theme import color, load_theme
from src.core.update import is_newer, latest_version
from src.core.version import glint_version
from src.ui.editor import EDGE, WINDOW_GRAB, EditBar, LayoutEditor
from src.ui.layout import DEFAULT_LAYOUT, create_widgets, load_layout, save_layout


class SensorWorker(QThread):
    """Samples metrics off the GUI thread so slow probes never block painting."""

    ready = pyqtSignal(dict)

    def __init__(self, interval_ms: int) -> None:
        super().__init__()
        self.interval_ms = max(int(interval_ms), 50)
        self._stop = threading.Event()

    def run(self) -> None:
        from src.core.sensors import SensorReader  # imported in the worker thread; owns its COM objects

        reader = SensorReader()
        while True:
            data = reader.get_all(stop=self._stop)
            if self._stop.is_set():
                break
            self.ready.emit(data)
            if self._stop.wait(self.interval_ms / 1000):
                break

    def stop(self) -> None:
        self._stop.set()


class UpdateChecker(QThread):
    """Polls the latest release tag off the GUI thread when updates are opted in."""

    checked = pyqtSignal(bool)

    CHECK_INTERVAL_MS = 60 * 60 * 1000

    def __init__(self) -> None:
        super().__init__()
        self._stop = threading.Event()

    def run(self) -> None:
        while True:
            self.checked.emit(is_newer(latest_version(), glint_version()))
            if self._stop.wait(self.CHECK_INTERVAL_MS / 1000):
                break

    def stop(self) -> None:
        self._stop.set()


class GlassHUD(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.theme = load_theme(self.settings["theme"])
        self.layout_data = load_layout(self.settings["layout"])
        self.widgets = create_widgets(self.layout_data)
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
        self.sensor_worker = SensorWorker(self.settings["refresh_interval_ms"])
        self.sensor_worker.ready.connect(self.apply_stats)  # queued across threads
        self.sensor_worker.start(QThread.Priority.LowPriority)
        self.tray = None
        self.update_available = False
        self.update_worker = None
        if self.settings.get("check_updates", False):
            self.start_update_checker()
        self.editor = LayoutEditor(self)
        self.edit_bar = EditBar(self)
        self.edit_bar.hide()

    def enter_edit_mode(self) -> None:
        if self.editor.active:
            return
        self.editor.start()
        self._place_edit_bar()
        self.edit_bar.show()
        self.edit_bar.raise_()
        self.update()

    def exit_edit_mode(self, save: bool) -> None:
        if not self.editor.active:
            return
        if save:
            save_layout(self.widgets, self.width(), self.height(), self.settings["layout"])
        else:
            self._restore_snapshot()
        self.editor.stop()
        self.edit_bar.hide()
        self.unsetCursor()
        self.update()

    def reset_layout(self) -> None:
        # Explicit, destructive action: default widgets are applied and
        # persisted immediately from either the Settings page or the editor.
        layout = DEFAULT_LAYOUT
        self.widgets = create_widgets(layout)
        for widget in self.widgets:
            widget.set_theme(self.theme)
        self.resize(layout["width"], layout["height"])
        save_layout(self.widgets, self.width(), self.height(), self.settings["layout"])
        self.update()

    def _restore_snapshot(self) -> None:
        snapshot = self.editor.snapshot
        if snapshot is None:
            return
        self.widgets = create_widgets({"width": snapshot["width"], "height": snapshot["height"], "widgets": snapshot["widgets"]})
        for widget in self.widgets:
            widget.set_theme(self.theme)
        self.resize(snapshot["width"], snapshot["height"])

    def _place_edit_bar(self) -> None:
        self.edit_bar.setGeometry(12, 3, max(120, self.width() - 24), 30)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.editor.active:
            self._place_edit_bar()

    def apply_stats(self, data: dict) -> None:
        for widget in self.widgets:
            widget.update(data)
        self.update()

    def apply_settings(self, settings: dict) -> None:
        self.settings = save_settings(settings)
        self.theme = load_theme(self.settings["theme"])
        self.setWindowOpacity(self.settings["opacity"])
        self.sensor_worker.interval_ms = self.settings["refresh_interval_ms"]
        for widget in self.widgets:
            widget.set_theme(self.theme)
        if self.settings.get("check_updates", False):
            self.start_update_checker()
        else:
            self.stop_update_checker()
            self.update_available = False
            if self.tray is not None:
                self.tray.set_update_available(False)
        self.update()

    def start_update_checker(self) -> None:
        if self.update_worker is not None:
            return
        self.update_worker = UpdateChecker()
        self.update_worker.checked.connect(self._on_update_check)
        self.update_worker.start(QThread.Priority.LowPriority)

    def stop_update_checker(self) -> None:
        if self.update_worker is None:
            return
        self.update_worker.stop()
        self.update_worker.wait(5000)
        self.update_worker = None

    def _on_update_check(self, available: bool) -> None:
        self.update_available = available
        if self.tray is not None:
            self.tray.set_update_available(available)
        self.update()

    def open_settings(self) -> None:
        from src.ui.settings import SettingsWindow

        if self.settings_window is None:
            # Retain it in Python without assigning a native parent. Parented
            # widgets are presented as tool panels on several desktops.
            self.settings_window = SettingsWindow(self.settings, self)
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
        title = self.settings.get("title", "Glint")
        painter.setFont(QFont(self.theme.get("font", "Sans Serif"), 8))
        painter.setPen(color(self.theme, "header", "#80F0F0F0"))
        title_width = painter.fontMetrics().horizontalAdvance(title)
        painter.drawText((self.width() - title_width) // 2, 13, title)
        if self.update_available:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color(self.theme, "warning", "#FFC850"))
            painter.drawEllipse(self.width() // 2 + title_width // 2 + 4, 8, 4, 4)
        for widget in self.widgets:
            widget.draw(painter)
        label = glint_version()
        painter.setFont(QFont(self.theme.get("font", "Sans Serif"), 7))
        painter.setPen(color(self.theme, "footer", "#66F0F0F0"))
        painter.drawText(int((self.width() - painter.fontMetrics().horizontalAdvance(label)) / 2), self.height() - 5, label)
        if self.editor.active:
            self._paint_editor_overlay(painter)

    def _paint_editor_overlay(self, painter: QPainter) -> None:
        painter.setPen(QPen(color(self.theme, "border", "#2DFFFFFF"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for widget in self.widgets:
            painter.drawRoundedRect(widget.bounds, 4, 4)
            # Visible grab affordance matching the (generous) resize hit box.
            grip = QRectF(widget.bounds.right() - 12, widget.bounds.bottom() - 12, 12, 12)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color(self.theme, "warning", "#FFC850"))
            painter.drawRoundedRect(grip, 3, 3)
            painter.setPen(color(self.theme, "text", "#F0F0F0"))
            for step in range(3):
                x0 = grip.left() + 3 + step * 3
                painter.drawLine(int(x0), int(grip.top() + 3), int(x0), int(grip.bottom() - 4))
        # Window-corner resize grip, painted in the same 24px zone hit() uses.
        corner = QRectF(
            self.width() - WINDOW_GRAB, self.height() - WINDOW_GRAB, WINDOW_GRAB - EDGE, WINDOW_GRAB - EDGE
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color(self.theme, "warning", "#FFC850"))
        painter.drawRoundedRect(corner, 6, 6)
        painter.setPen(color(self.theme, "text", "#F0F0F0"))
        for step in range(3):
            x0 = corner.left() + 4 + step * 4
            painter.drawLine(int(x0), int(corner.top() + 4), int(x0), int(corner.bottom() - 5))
        painter.setPen(color(self.theme, "border", "#2DFFFFFF"))
        painter.drawText(EDGE, self.height() - 8, "Editing — drag widgets, right-click, Esc discards")

    def mousePressEvent(self, event) -> None:
        pos = event.position().toPoint()
        if self.editor.active and event.button() == Qt.MouseButton.LeftButton:
            self.editor.press(pos)
            self.update()
            event.accept()
            return
        if self.editor.active and event.button() == Qt.MouseButton.RightButton:
            menu = self.editor.context_menu(pos)
            menu.exec(event.globalPosition().toPoint())
            event.accept()
            return
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
            menu.addAction("Exit", self.shutdown)
            menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if self.editor.active:
            self.editor.move(event.position().toPoint())
            index, region = self.editor.hit(event.position().toPoint())
            if region in ("resize", "window_resize"):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif index >= 0:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        if self.drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        if self.editor.active:
            self.editor.release(event.position().toPoint())
            return
        self.drag_pos = None
        self.settings["window"] = {"x": self.x(), "y": self.y()}
        save_settings(self.settings)

    def keyPressEvent(self, event) -> None:
        if self.editor.active and event.key() == Qt.Key.Key_Escape:
            self.exit_edit_mode(save=False)
            event.accept()
            return
        super().keyPressEvent(event)

    def shutdown(self) -> None:
        # Stop sampling first so exit never races an in-flight probe.
        self.sensor_worker.stop()
        self.sensor_worker.wait(5000)
        self.stop_update_checker()
        if self.editor.active:
            # Uncommitted edits must not leak into the layout on exit.
            self.exit_edit_mode(save=False)
        # Single exit path so the layout is saved whether the user exits from
        # the HUD context menu or the tray menu.
        save_layout(self.widgets, self.width(), self.height(), self.settings["layout"])
        if self.tray is not None:
            # Let the platform release the tray icon before the interpreter
            # teardown, matching the tray menu's exit path. QSystemTrayIcon's
            # Windows backend plays poorly with widget destruction at shutdown.
            self.tray.tray.hide()
        QApplication.instance().quit()
