"""Glint application entry point."""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.core.compat import is_low_spec
from src.ui.hud import GlassHUD
from src.ui.tray import TrayManager


def _maybe_disable_hardware_acceleration() -> None:
    """Degrade the renderer on low-spec hosts before QApplication exists.

    Must be called before ``QApplication`` is constructed, because on legacy
    hardware the GPU/DWM recomposition of the translucent HUD causes
    refresh/focus loops. Applied on every platform so behavior is consistent
    regardless of the compositor or graphics stack in use.
    """
    if is_low_spec():
        # Qt 6 removed AA_DisableHardwareAcceleration; AA_UseSoftwareOpenGL is
        # its replacement and routes rendering through the software rasterizer.
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)


def main() -> int:
    _maybe_disable_hardware_acceleration()
    app = QApplication(sys.argv)
    app.setApplicationName("Glint")
    app.setOrganizationName("ZFordDev")
    app.setQuitOnLastWindowClosed(False)
    hud = GlassHUD()
    hud.show()
    tray = TrayManager(app, hud)
    app._glint_objects = (hud, tray)  # Keep Python wrappers alive.
    return app.exec()
