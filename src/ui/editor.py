"""WYSIWYG layout editing on the live HUD."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from PyQt6.QtCore import QPoint, QPointF, QRectF, QSize, Qt
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QMenu, QPushButton, QWidget

from src.ui.widgets import WIDGET_TYPES

EDGE = 8
GRID = 8
MIN_WIDTH = 60
MIN_HEIGHT = 20
WIDGET_WIDTH = 216
WIDGET_HEIGHT = 38
# Corner grab boxes are deliberately generous: a miss that lands a few pixels
# outside a corner should still resize instead of dragging the whole HUD.
RESIZE_HANDLE = 24
WINDOW_GRAB = 24

FRIENDLY: dict[str, str] = {
    "cpu": "CPU",
    "ram": "RAM",
    "disk": "Disk",
    "gpu_temp": "GPU temp",
    "gpu_usage": "GPU",
    "network": "Network",
}


class LayoutEditor:
    """Hit-testing and gesture state for editing the live HUD widgets.

    The editor mutates the HUD's widgets directly so the translucent window
    stays live; ``save`` persists them and ``discard`` restores the snapshot
    taken when editing started.
    """

    def __init__(self, hud) -> None:
        self.hud = hud
        self.active = False
        self.snap_enabled = False
        self.snapshot: dict[str, Any] | None = None
        self._drag: tuple[int, QPoint] | None = None
        self._widget_resize: tuple[int, QRectF, QPoint] | None = None
        self._window_resize: tuple[QSize, QPoint] | None = None

    def start(self) -> None:
        self.snapshot = {
            "width": self.hud.width(),
            "height": self.hud.height(),
            "widgets": [deepcopy(widget.serialize()) for widget in self.hud.widgets],
        }
        self.active = True

    def stop(self) -> None:
        self.active = False
        self.snapshot = None
        self._drag = None
        self._widget_resize = None
        self._window_resize = None

    def set_snap(self, enabled: bool) -> None:
        """Turn grid snapping on or off (widget moves and resizes align to GRID)."""
        self.snap_enabled = bool(enabled)

    @staticmethod
    def _snap(enabled: bool, value: int) -> int:
        if not enabled:
            return value
        return round(value / GRID) * GRID

    def hit(self, pos: QPoint) -> tuple[int, str]:
        """Return ``(widget index, region)``; region is move/resize/empty space/window_resize."""
        point = QPointF(pos)
        for index in range(len(self.hud.widgets) - 1, -1, -1):
            bounds = self.hud.widgets[index].bounds
            # Sized beyond the corner by EDGE so near-misses still resize.
            handle = QRectF(
                bounds.right() - RESIZE_HANDLE,
                bounds.bottom() - RESIZE_HANDLE,
                RESIZE_HANDLE + EDGE,
                RESIZE_HANDLE + EDGE,
            )
            if handle.contains(point):
                return index, "resize"
            if bounds.adjusted(-4, -4, 4, 4).contains(point):
                return index, "move"
        if QRectF(
            self.hud.width() - WINDOW_GRAB, self.hud.height() - WINDOW_GRAB, WINDOW_GRAB, WINDOW_GRAB
        ).contains(point):
            return -1, "window_resize"
        return -1, ""

    def press(self, pos: QPoint) -> str:
        index, region = self.hit(pos)
        if region == "resize":
            bounds = self.hud.widgets[index].bounds
            self._widget_resize = (index, QRectF(bounds), pos)
        elif region == "move":
            self._drag = (index, pos - self.hud.widgets[index].bounds.topLeft().toPoint())
        elif region == "window_resize":
            self._window_resize = (QSize(self.hud.width(), self.hud.height()), pos)
        elif region == "":
            # Empty space drags the whole window, matching normal HUD behavior.
            self.hud.drag_pos = self.hud.mapToGlobal(pos) - self.hud.frameGeometry().topLeft()
        return region

    def move(self, pos: QPoint) -> None:
        hud = self.hud
        if self._drag is not None:
            index, offset = self._drag
            bounds = hud.widgets[index].bounds
            max_x = max(1, hud.width() - int(bounds.width()) - EDGE)
            max_y = max(1, hud.height() - int(bounds.height()) - EDGE)
            new_x = min(max(self._snap(self.snap_enabled, int(pos.x() - offset.x())), EDGE), max_x)
            new_y = min(max(self._snap(self.snap_enabled, int(pos.y() - offset.y())), EDGE), max_y)
            bounds.moveTopLeft(QPointF(new_x, new_y))
        elif self._widget_resize is not None:
            index, start, origin = self._widget_resize
            bounds = hud.widgets[index].bounds
            new_width = self._snap(self.snap_enabled, max(MIN_WIDTH, int(start.width()) + pos.x() - origin.x()))
            new_height = self._snap(self.snap_enabled, max(MIN_HEIGHT, int(start.height()) + pos.y() - origin.y()))
            bounds.setWidth(min(new_width, max(MIN_WIDTH, hud.width() - int(bounds.x()) - EDGE)))
            bounds.setHeight(min(new_height, max(MIN_HEIGHT, hud.height() - int(bounds.y()) - EDGE)))
        elif self._window_resize is not None:
            start, origin = self._window_resize
            width = self._snap(self.snap_enabled, max(120, start.width() + pos.x() - origin.x()))
            height = self._snap(self.snap_enabled, max(150, start.height() + pos.y() - origin.y()))
            hud.resize(width, height)
        elif hud.drag_pos is not None:
            hud.move(hud.mapToGlobal(pos) - hud.drag_pos)
        hud.update()

    def release(self, pos: QPoint) -> None:
        self._drag = None
        self._widget_resize = None
        self._window_resize = None
        self.hud.drag_pos = None
        self.hud.update()

    def add(self, widget_type: str, pos: QPoint) -> None:
        max_x = max(EDGE, self.hud.width() - WIDGET_WIDTH - EDGE)
        max_y = max(EDGE, self.hud.height() - WIDGET_HEIGHT - EDGE)
        options: dict[str, Any] = {
            "x": min(max(self._snap(self.snap_enabled, int(pos.x()) - WIDGET_WIDTH // 2), EDGE), max_x),
            "y": min(max(self._snap(self.snap_enabled, int(pos.y()) - WIDGET_HEIGHT // 2), EDGE), max_y),
            "width": WIDGET_WIDTH,
            "height": WIDGET_HEIGHT,
        }
        if widget_type == "disk":
            options["disk"] = None
        widget = WIDGET_TYPES[widget_type](**options)
        widget.set_theme(self.hud.theme)
        self.hud.widgets.append(widget)
        self.hud.update()

    def remove(self, index: int) -> None:
        if 0 <= index < len(self.hud.widgets):
            del self.hud.widgets[index]
            self.hud.update()

    def set_disk(self, index: int, name: str | None) -> None:
        if 0 <= index < len(self.hud.widgets):
            self.hud.widgets[index].options["disk"] = name
            self.hud.update()

    def _disk_options(self) -> list[str]:
        for widget in self.hud.widgets:
            disks = widget.data.get("disks", {})
            if disks:
                return sorted(disks)
        return []

    def context_menu(self, pos: QPoint) -> QMenu:
        menu = QMenu(self.hud)
        index, _ = self.hit(pos)
        if index >= 0:
            widget = self.hud.widgets[index]
            label = FRIENDLY.get(widget.widget_type, widget.widget_type)
            remove = menu.addAction(f"Remove {label}")
            remove.triggered.connect(lambda _, i=index: self.remove(i))
            if widget.widget_type == "disk":
                disk_menu = menu.addMenu("Disk")
                disks = self._disk_options() or ["Default"]
                for name in disks:
                    action = disk_menu.addAction(name)
                    action.triggered.connect(lambda _, n=name: self.set_disk(index, None if n == "Default" else n))
            menu.addSeparator()
        add = menu.addMenu("Add widget")
        for widget_type, label in FRIENDLY.items():
            action = add.addAction(label)
            action.triggered.connect(lambda _, t=widget_type: self.add(t, pos))
        reset = menu.addAction("Reset to defaults")
        reset.triggered.connect(self.hud.reset_layout)
        menu.addSeparator()
        save = menu.addAction("Save & exit")
        save.triggered.connect(lambda: self.hud.exit_edit_mode(save=True))
        discard = menu.addAction("Discard & exit")
        discard.triggered.connect(lambda: self.hud.exit_edit_mode(save=False))
        return menu


class EditBar(QWidget):
    """Small pinned toolbar shown at the top of the HUD while editing."""

    def __init__(self, hud) -> None:
        super().__init__(hud)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(6)
        self.hint = QLabel("Editing layout")
        self.hint.setStyleSheet("color: #E0E0E0; font-size: 10px;")
        layout.addWidget(self.hint, 1)
        self.snap = QCheckBox("Snap to grid")
        self.snap.setChecked(hud.editor.snap_enabled)
        self.snap.toggled.connect(hud.editor.set_snap)
        self.snap.setStyleSheet("color: #E0E0E0; font-size: 10px;")
        layout.addWidget(self.snap, 0)
        for text, slot in (
            ("Save", lambda: hud.exit_edit_mode(save=True)),
            ("Reset", hud.reset_layout),
            ("Discard", lambda: hud.exit_edit_mode(save=False)),
        ):
            button = QPushButton(text)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(slot)
            layout.addWidget(button)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "EditBar { background: rgba(24, 26, 36, 200); border: 1px solid #3D5A7A; border-radius: 8px; }"
        )
        self.setToolTip("Drag widgets to move them, drag a corner to resize, right-click for options. Esc discards.")