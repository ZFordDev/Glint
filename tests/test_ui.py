import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.core.settings_storage import DEFAULT_SETTINGS
from src.ui.settings import SettingsWindow


def test_settings_is_an_independent_window():
    app = QApplication.instance() or QApplication([])
    window = SettingsWindow(DEFAULT_SETTINGS)
    assert window.parentWidget() is None
    assert window.isWindow()
    window.close()
    app.processEvents()
