"""Glint application entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from src.ui.hud import GlassHUD
from src.ui.tray import TrayManager


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Glint")
    app.setOrganizationName("ZFordDev")
    app.setQuitOnLastWindowClosed(False)
    hud = GlassHUD()
    hud.show()
    tray = TrayManager(app, hud)
    app._glint_objects = (hud, tray)  # Keep Python wrappers alive.
    return app.exec()
