"""System tray integration with portable autostart support."""

import os
import platform
import sys
from pathlib import Path

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class TrayManager:
    def __init__(self, app, hud) -> None:
        self.app, self.hud = app, hud
        icon = Path(__file__).parents[2] / "assets" / "icon.svg"
        self.tray = QSystemTrayIcon(QIcon(str(icon)), app)
        menu = QMenu()
        menu.addAction("Show Glint", self.show_hud)
        menu.addAction("Settings", hud.open_settings)
        self.startup_action = QAction("Run on Startup", menu, checkable=True)
        self.startup_action.setChecked(self.startup_path().exists())
        self.startup_action.triggered.connect(self.toggle_startup)
        menu.addAction(self.startup_action)
        menu.addSeparator()
        menu.addAction("Exit", self.exit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_activated)
        self.tray.show()

    @staticmethod
    def startup_path() -> Path:
        if platform.system() == "Windows":
            return (
                Path(os.environ.get("APPDATA", Path.home())) / "Microsoft/Windows/Start Menu/Programs/Startup/Glint.cmd"
            )
        if platform.system() == "Darwin":
            return Path.home() / "Library/LaunchAgents/dev.zford.glint.plist"
        return (
            Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.ConfigLocation))
            / "autostart/glint.desktop"
        )

    def toggle_startup(self, enabled: bool) -> None:
        path = self.startup_path()
        try:
            if not enabled:
                path.unlink(missing_ok=True)
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            executable = Path(sys.executable)
            if platform.system() == "Windows":
                content = f'@start "" "{executable}" -m src\n'
            elif platform.system() == "Darwin":
                content = (
                    f'<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict>'
                    f"<key>Label</key><string>dev.zford.glint</string><key>ProgramArguments</key><array>"
                    f"<string>{executable}</string><string>-m</string><string>src</string></array>"
                    f"<key>RunAtLoad</key><true/></dict></plist>"
                )
            else:
                content = f"[Desktop Entry]\nType=Application\nName=Glint\nExec={executable} -m src\nX-GNOME-Autostart-enabled=true\n"
            path.write_text(content, encoding="utf-8")
        except OSError:
            self.startup_action.setChecked(not enabled)

    def show_hud(self) -> None:
        self.hud.show()
        self.hud.raise_()
        self.hud.activateWindow()

    def on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_hud()

    def exit_app(self) -> None:
        # Route through the HUD's shutdown so the layout is saved exactly as
        # with the HUD context menu's Exit action.
        self.tray.hide()
        self.hud.shutdown()
