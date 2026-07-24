from PyQt6.QtWidgets import QApplication
from src.ui.hud import GlassHUD
import sys

app = QApplication(sys.argv)
hud = GlassHUD()
hud.show()
sys.exit(app.exec())
