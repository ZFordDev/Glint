"""
hud.py
------
main UI for windows runtime.
"""

import sys

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMenu,
)

from PyQt6.QtGui import (
    QPainter,
    QColor,
    QAction,
    QFont,
    QLinearGradient,
    QPen,
)

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QRectF,
)

from src.core.stats import get_basic_stats
from src.core.sensors import get_all_sensors


# ---------------------------------------------------------
# GLASS HUD
# ---------------------------------------------------------
class GlassHUD(QWidget):
    def __init__(self):
        super().__init__()

        # -------------------------------------------------
        # WINDOW CONFIG
        # -------------------------------------------------
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnBottomHint
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Compact modern sizing
        self.resize(260, 180)

        # -------------------------------------------------
        # STATE
        # -------------------------------------------------
        self.drag_pos = None

        self.cpu = 0
        self.ram = 0
        self.disks = {}

        # -------------------------------------------------
        # FONT
        # -------------------------------------------------
        self.title_font = QFont("Segoe UI", 10)
        self.value_font = QFont("Segoe UI", 9)

        # -------------------------------------------------
        # TIMER
        # -------------------------------------------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        self.update_stats()

    # ---------------------------------------------------------
    # UPDATE STATS
    # ---------------------------------------------------------
    def update_stats(self):
        basic = get_basic_stats()

        self.cpu = basic["cpu"]
        self.ram = basic["ram"]
        self.disks = basic["disks"]

        self.update()

    # ---------------------------------------------------------
    # BAR COLOR
    # ---------------------------------------------------------
    def get_bar_color(self, percent):
        if percent < 50:
            return QColor(80, 220, 120)
        elif percent < 80:
            return QColor(255, 200, 80)
        else:
            return QColor(255, 100, 100)

    # ---------------------------------------------------------
    # DRAW BAR
    # ---------------------------------------------------------
    def draw_bar(self, painter, x, y, width, percent):
        height = 10

        # Background track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))

        painter.drawRoundedRect(
            QRectF(x, y, width, height),
            5,
            5
        )

        # Filled amount
        fill_width = max(8, int(width * (percent / 100)))

        gradient = QLinearGradient(x, y, x + fill_width, y)

        color = self.get_bar_color(percent)

        gradient.setColorAt(0, color.lighter(120))
        gradient.setColorAt(1, color)

        painter.setBrush(gradient)

        painter.drawRoundedRect(
            QRectF(x, y, fill_width, height),
            5,
            5
        )

    # ---------------------------------------------------------
    # DRAW STAT BLOCK
    # ---------------------------------------------------------
    def draw_stat(
        self,
        painter,
        label,
        percent,
        x,
        y
    ):
        # Text
        painter.setPen(QColor(240, 240, 240))

        painter.setFont(self.title_font)

        painter.drawText(
            x,
            y,
            f"{label}  {percent}%"
        )

        # Bar
        self.draw_bar(
            painter,
            x,
            y + 10,
            180,
            percent
        )

    # ---------------------------------------------------------
    # PAINT EVENT
    # ---------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        rect = self.rect().adjusted(1, 1, -1, -1)

        # -------------------------------------------------
        # GLASS BACKGROUND
        # -------------------------------------------------
        glass = QLinearGradient(0, 0, 0, self.height())

        glass.setColorAt(
            0,
            QColor(255, 255, 255, 40)
        )

        glass.setColorAt(
            1,
            QColor(255, 255, 255, 12)
        )

        # Base dark tint
        painter.setBrush(QColor(18, 18, 18, 150))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRoundedRect(rect, 18, 18)

        # Glass overlay
        painter.setBrush(glass)

        painter.drawRoundedRect(rect, 18, 18)

        # -------------------------------------------------
        # BORDER
        # -------------------------------------------------
        pen = QPen(QColor(255, 255, 255, 45))
        pen.setWidth(1)

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawRoundedRect(rect, 18, 18)

        # -------------------------------------------------
        # INNER HIGHLIGHT
        # -------------------------------------------------
        painter.setPen(QPen(QColor(255, 255, 255, 18)))

        painter.drawLine(
            20,
            14,
            self.width() - 20,
            14
        )

        # -------------------------------------------------
        # CONTENT
        # -------------------------------------------------
        start_x = 22
        start_y = 38
        spacing = 38

        self.draw_stat(
            painter,
            "CPU",
            self.cpu,
            start_x,
            start_y
        )

        self.draw_stat(
            painter,
            "RAM",
            self.ram,
            start_x,
            start_y + spacing
        )

        # Draw first 2 disks only
        disk_y = start_y + spacing * 2

        for i, (disk, usage) in enumerate(
            list(self.disks.items())[:2]
        ):
            self.draw_stat(
                painter,
                disk,
                usage,
                start_x,
                disk_y + (i * spacing)
            )

    # ---------------------------------------------------------
    # MOUSE EVENTS
    # ---------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

        elif event.button() == Qt.MouseButton.RightButton:
            self.open_context_menu(event)

    def mouseMoveEvent(self, event):
        if (
            self.drag_pos is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint()
                - self.drag_pos
            )

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    # ---------------------------------------------------------
    # CONTEXT MENU
    # ---------------------------------------------------------
    def open_context_menu(self, event):
        menu = QMenu(self)

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.close)

        menu.addAction(quit_action)

        menu.exec(
            event.globalPosition().toPoint()
        )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    hud = GlassHUD()
    hud.show()

    sys.exit(app.exec())