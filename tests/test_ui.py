import os
from types import SimpleNamespace
from unittest.mock import Mock

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


def _make_hud(monkeypatch):
    """Build a real GlassHUD with storage redirected away from the user config."""
    import src.ui.hud as hud_module

    monkeypatch.setattr(hud_module, "load_settings", lambda: dict(DEFAULT_SETTINGS))
    monkeypatch.setattr(hud_module, "save_settings", lambda settings: settings)
    monkeypatch.setattr(hud_module, "load_layout", lambda *a, **k: {"width": 280, "height": 290, "widgets": []})
    saved_layouts = []
    monkeypatch.setattr(hud_module, "save_layout", lambda *a: saved_layouts.append(a))
    return hud_module.GlassHUD(), saved_layouts


def test_hud_shutdown_saves_layout(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr("src.ui.hud.QApplication.instance", staticmethod(lambda: Mock()))
    hud, saved = _make_hud(monkeypatch)
    hud.shutdown()
    assert len(saved) == 1  # Regression: every exit path must persist the layout.
    app.processEvents()


def test_tray_exit_routes_through_hud_shutdown(monkeypatch):
    from src.ui.tray import TrayManager

    app = QApplication.instance() or QApplication([])
    hud = SimpleNamespace(open_settings=lambda: None, shutdown=Mock())
    tray = TrayManager(app, hud)
    tray.exit_app()
    hud.shutdown.assert_called_once()  # Regression: tray Exit used to quit without saving.
    app.processEvents()


def test_startup_launch_arguments_frozen_vs_source(monkeypatch):
    import sys

    from src.ui.tray import TrayManager

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert TrayManager._launch_arguments() == [sys.executable]  # Frozen builds must not pass -m src.
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert TrayManager._launch_arguments() == [sys.executable, "-m", "src"]


def test_autostart_content_quotes_executable_paths(monkeypatch):
    from src.ui.tray import TrayManager

    spaced = "C:\\Program Files\\Glint.exe"
    monkeypatch.setattr(TrayManager, "_launch_arguments", staticmethod(lambda: [spaced]))

    monkeypatch.setattr("src.ui.tray.platform.system", lambda: "Windows")
    assert TrayManager._startup_content() == f'@start "" "{spaced}"\n'

    monkeypatch.setattr("src.ui.tray.platform.system", lambda: "Linux")
    assert f'Exec="{spaced}"' in TrayManager._startup_content()

    monkeypatch.setattr("src.ui.tray.platform.system", lambda: "Darwin")
    assert f"<string>{spaced}</string>" in TrayManager._startup_content()
