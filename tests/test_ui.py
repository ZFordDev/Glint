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


def test_settings_window_emits_custom_title():
    app = QApplication.instance() or QApplication([])
    window = SettingsWindow(DEFAULT_SETTINGS)
    emitted = []
    window.settings_changed.connect(emitted.append)
    window.title.setText("My Rig")
    assert emitted[-1]["title"] == "My Rig"
    window.title.setText("")
    assert emitted[-1]["title"] == "Glint"
    window.close()
    app.processEvents()


def test_settings_window_emits_check_updates():
    app = QApplication.instance() or QApplication([])
    window = SettingsWindow(DEFAULT_SETTINGS)
    emitted = []
    window.settings_changed.connect(emitted.append)
    window.update_notify.setChecked(True)
    assert emitted[-1]["check_updates"] is True
    window.update_notify.setChecked(False)
    assert emitted[-1]["check_updates"] is False
    window.close()
    app.processEvents()


def test_settings_window_custom_theme_populates_rows():
    from PyQt6.QtGui import QColor

    app = QApplication.instance() or QApplication([])
    window = SettingsWindow({**DEFAULT_SETTINGS, "custom_theme": {"text": "#80ABCDEF"}})
    for key, _swatch, hex_label in window._rows:
        if key == "text":
            assert QColor(hex_label.text()).name(QColor.NameFormat.HexArgb) == "#80abcdef"
            break
    else:
        raise AssertionError("text color row missing")
    window.close()
    app.processEvents()


def test_settings_window_apply_override_emits_custom_theme():
    from PyQt6.QtGui import QColor

    app = QApplication.instance() or QApplication([])
    window = SettingsWindow(DEFAULT_SETTINGS)
    emitted = []
    window.settings_changed.connect(emitted.append)
    window.apply_override("warning", QColor("#80FFC850"))
    assert window.overrides == {"warning": "#80ffc850"}
    assert emitted[-1]["custom_theme"] == {"warning": "#80ffc850"}
    window.close()
    app.processEvents()


def test_settings_window_reset_restores_theme_defaults():
    app = QApplication.instance() or QApplication([])
    window = SettingsWindow({**DEFAULT_SETTINGS, "custom_theme": {"text": "#FF123456", "border": "#FFFF0000"}})
    emitted = []
    window.settings_changed.connect(emitted.append)
    window._reset_override("text")
    assert window.overrides == {"border": "#FFFF0000"}
    window._reset_all()
    assert window.overrides == {}
    assert emitted[-1]["custom_theme"] == {}
    window.close()
    app.processEvents()


def test_hud_builds_theme_with_overrides(monkeypatch):
    app = QApplication.instance() or QApplication([])
    hud, _ = _make_hud(
        monkeypatch,
        {**DEFAULT_SETTINGS, "custom_theme": {"warning": "#FF123456", "bogus": "#ABCDEF"}},
    )
    assert hud.theme["colors"]["warning"] == "#ff123456"
    assert "bogus" not in hud.theme["colors"]
    assert hud.theme["colors"]["border"] == "#2DFFFFFF"  # untouched base value stays raw
    app.processEvents()


def test_hud_apply_settings_merges_custom_theme(monkeypatch):
    from PyQt6.QtGui import QColor

    app = QApplication.instance() or QApplication([])
    hud, _ = _make_hud(monkeypatch)
    updated = {**DEFAULT_SETTINGS, "custom_theme": {"track": "#FF654321"}}
    hud.apply_settings(updated)
    assert hud.theme["colors"]["track"] == QColor("#FF654321").name(QColor.NameFormat.HexArgb)
    app.processEvents()


def test_tray_get_update_visibility(monkeypatch):
    from src.ui.tray import TrayManager

    app = QApplication.instance() or QApplication([])
    hud = _fake_hud_hooks()
    tray = TrayManager(app, hud)
    tray.set_update_available(False)
    assert not tray.get_update_action.isVisible()
    tray.set_update_available(True)
    assert tray.get_update_action.isVisible()
    app.processEvents()


def test_open_releases_uses_github_page(monkeypatch):
    from src.ui.tray import TrayManager

    app = QApplication.instance() or QApplication([])
    calls = []
    monkeypatch.setattr("src.ui.tray.webbrowser.open", lambda url: calls.append(url))
    tray = TrayManager(app, Mock())
    tray.open_releases()
    assert calls == ["https://github.com/ZFordDev/Glint/releases/latest"]
    app.processEvents()


def _make_hud(monkeypatch, settings=None):
    """Build a real GlassHUD with storage redirected away from the user config."""
    import src.ui.hud as hud_module

    baseline = dict(settings) if settings is not None else dict(DEFAULT_SETTINGS)
    monkeypatch.setattr(hud_module, "load_settings", lambda: dict(baseline))
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
    assert not hud.sensor_worker.isRunning()  # Sampling must stop before quit.
    app.processEvents()


def _fake_hud_hooks():
    return SimpleNamespace(open_settings=lambda: None, enter_edit_mode=lambda: None, shutdown=Mock())


def test_tray_exit_routes_through_hud_shutdown(monkeypatch):
    from src.ui.tray import TrayManager

    app = QApplication.instance() or QApplication([])
    hud = _fake_hud_hooks()
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


def test_hardware_acceleration_disabled_when_low_spec(monkeypatch):
    import src.app as app_module

    calls = []
    monkeypatch.setattr(app_module, "is_low_spec", lambda: True)
    monkeypatch.setattr(
        app_module.QApplication,
        "setAttribute",
        staticmethod(lambda attribute: calls.append(attribute)),
    )
    app_module._maybe_disable_hardware_acceleration()
    assert calls == [app_module.Qt.ApplicationAttribute.AA_UseSoftwareOpenGL]


def test_hardware_acceleration_kept_when_not_low_spec(monkeypatch):
    import src.app as app_module

    calls = []
    monkeypatch.setattr(app_module, "is_low_spec", lambda: False)
    monkeypatch.setattr(
        app_module.QApplication,
        "setAttribute",
        staticmethod(lambda attribute: calls.append(attribute)),
    )
    app_module._maybe_disable_hardware_acceleration()
    assert calls == []
