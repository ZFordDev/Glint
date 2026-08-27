"""Glint application entry point."""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.core.compat import is_low_spec
from src.ui.hud import GlassHUD
from src.ui.tray import TrayManager


def main() -> int:
    # Must be set before QApplication is constructed; on legacy hardware the
    # GPU/DWM recomposition of the translucent HUD causes refresh/focus loops.
    if sys.platform == "win32" and is_low_spec():
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableHardwareAcceleration)
    app = QApplication(sys.argv)
    app.setApplicationName("Glint")
    app.setOrganizationName("ZFordDev")
    app.setQuitOnLastWindowClosed(False)
    hud = GlassHUD()
    hud.show()
    tray = TrayManager(app, hud)
    app._glint_objects = (hud, tray)  # Keep Python wrappers alive.
    return app.exec()
