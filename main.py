from PyQt6.QtWidgets import QApplication
from src.ui.hud import GlassHUD
from src.ui.tray import TrayManager
import sys

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

hud = GlassHUD()
hud.show()

tray = TrayManager(app, hud)

sys.exit(app.exec())
