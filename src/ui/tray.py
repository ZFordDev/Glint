from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
import os
import sys

class TrayManager:
    def __init__(self, app, hud):
        self.app = app
        self.hud = hud

        # -------------------------------------------------
        # ICON
        # -------------------------------------------------
        icon_path = os.path.join(os.path.dirname(__file__),"..", "..", "assets", "icon.svg")
        self.tray = QSystemTrayIcon(QIcon(icon_path), app)
        self.tray.setVisible(True)

        # -------------------------------------------------
        # MENU
        # -------------------------------------------------
        self.menu = QMenu()

        # Run on startup
        self.startup_action = QAction("Run on Startup", self.menu)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.is_in_startup())
        self.startup_action.triggered.connect(self.toggle_startup)
        self.menu.addAction(self.startup_action)

        # Exit
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(exit_action)

        self.tray.setContextMenu(self.menu)

        # -------------------------------------------------
        # DOUBLE CLICK = SHOW HUD
        # -------------------------------------------------
        self.tray.activated.connect(self.on_activated)

    # -----------------------------------------------------
    # STARTUP MANAGEMENT (Windows)
    # -----------------------------------------------------
    def startup_shortcut_path(self):
        import winreg
        import pathlib

        # Startup folder
        return os.path.join(
            os.environ["APPDATA"],
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
            "Startup",
            "Glint.lnk"
        )

    def is_in_startup(self):
        return os.path.exists(self.startup_shortcut_path())

    def toggle_startup(self):
        if self.startup_action.isChecked():
            self.add_to_startup()
        else:
            self.remove_from_startup()

    def add_to_startup(self):
        try:
            import winshell
            from win32com.client import Dispatch

            shortcut_path = self.startup_shortcut_path()
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = sys.executable
            shortcut.Arguments = ""
            shortcut.WorkingDirectory = os.getcwd()
            shortcut.IconLocation = sys.executable
            shortcut.save()
        except Exception as e:
            print("Failed to add startup:", e)

    def remove_from_startup(self):
        try:
            os.remove(self.startup_shortcut_path())
        except Exception:
            pass

    # -----------------------------------------------------
    # TRAY BEHAVIOR
    # -----------------------------------------------------
    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.hud.show()
            self.hud.raise_()

    def exit_app(self):
        self.tray.setVisible(False)
        self.app.quit()
