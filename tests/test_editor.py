import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QApplication

from src.core.settings_storage import DEFAULT_SETTINGS
from src.ui.layout import DEFAULT_LAYOUT

# Keep the QApplication wrapper referenced for the whole module: pytest discards
# the return value of helper calls, and destroying the Python wrapper tears down
# the C++ QApplication while qApp still points at it, crashing the next Qt use.
app = QApplication.instance() or QApplication([])


def _make_hud(monkeypatch, saved_layouts=None):
    import src.ui.hud as hud_module

    monkeypatch.setattr(hud_module, "load_settings", lambda: dict(DEFAULT_SETTINGS))
    monkeypatch.setattr(hud_module, "save_settings", lambda settings: settings)
    monkeypatch.setattr(hud_module, "load_layout", lambda *a, **k: DEFAULT_LAYOUT)
    if saved_layouts is None:
        saved_layouts = []
    monkeypatch.setattr(hud_module, "save_layout", lambda *a: saved_layouts.append(a))
    hud = hud_module.GlassHUD()
    return hud, saved_layouts


def _stop(hud):
    hud.sensor_worker.stop()
    hud.sensor_worker.wait(5000)


def test_hit_test_regions(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    # Default cpu widget sits at (22, 30, 236, 38).
    assert editor.hit(QPoint(30, 40)) == (0, "move")
    assert editor.hit(QPoint(250, 60)) == (0, "resize")  # bottom-right handle
    assert editor.hit(QPoint(140, 300)) == (-1, "")  # empty area below widgets
    assert editor.hit(QPoint(276, 286)) == (-1, "window_resize")  # HUD corner
    _stop(hud)


def test_drag_moves_and_clamps(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.press(QPoint(30, 40))  # grab cpu
    editor.move(QPoint(130, 120))
    assert (hud.widgets[0].bounds.x(), hud.widgets[0].bounds.y()) == (36, 110)
    editor.move(QPoint(2, 2))  # clamp to the HUD edge
    assert (hud.widgets[0].bounds.x(), hud.widgets[0].bounds.y()) == (8, 8)
    editor.release(QPoint(2, 2))
    _stop(hud)


def test_resize_handle_resizes_and_clamps(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.press(QPoint(250, 60))  # cpu resize handle
    editor.move(QPoint(400, 400))
    bounds = hud.widgets[0].bounds
    assert bounds.width() == 280 - 22 - 8  # clamped to hub minus margin
    assert bounds.height() == 290 - 30 - 8
    editor.release(QPoint(400, 400))
    _stop(hud)


def test_window_corner_resizes_hud(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.press(QPoint(276, 286))
    editor.move(QPoint(320, 320))
    assert (hud.width(), hud.height()) == (324, 324)
    editor.release(QPoint(320, 320))
    _stop(hud)


def test_discard_restores_snapshot(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    hud.enter_edit_mode()
    editor = hud.editor
    editor.press(QPoint(30, 40))
    editor.move(QPoint(130, 120))
    editor.release(QPoint(130, 120))
    assert (hud.widgets[0].bounds.x(), hud.widgets[0].bounds.y()) == (36, 110)
    hud.exit_edit_mode(save=False)
    assert (hud.widgets[0].bounds.x(), hud.widgets[0].bounds.y()) == (22, 30)
    assert (hud.width(), hud.height()) == (280, 290)
    _stop(hud)


def test_save_persists_edited_layout(monkeypatch):
    hud, saved = _make_hud(monkeypatch)
    hud.enter_edit_mode()
    hud.editor.press(QPoint(30, 40))
    hud.editor.move(QPoint(130, 120))
    hud.editor.release(QPoint(130, 120))
    hud.exit_edit_mode(save=True)
    assert len(saved) == 1
    widgets, width, height, _ = saved[0]
    assert (width, height) == (280, 290)
    assert (widgets[0].bounds.x(), widgets[0].bounds.y()) == (36, 110)
    _stop(hud)


def test_add_widget_places_and_themes(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.add("network", QPoint(50, 100))
    added = hud.widgets[-1]
    assert added.widget_type == "network"
    assert added.theme == hud.theme
    assert (added.bounds.x(), added.bounds.y()) == (8, 81)  # centered then clamped
    _stop(hud)


def test_remove_widget(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    hud.editor.remove(0)
    assert [widget.widget_type for widget in hud.widgets] == ["ram", "disk", "gpu_usage", "gpu_temp", "network"]
    _stop(hud)


def test_set_disk_option(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    hud.editor.set_disk(2, "E:")
    assert hud.widgets[2].options["disk"] == "E:"
    _stop(hud)


def test_reset_restores_default_layout(monkeypatch):
    hud, saved = _make_hud(monkeypatch)
    hud.enter_edit_mode()
    hud.editor.remove(0)
    hud.reset_layout()
    assert [widget.widget_type for widget in hud.widgets] == ["cpu", "ram", "disk", "gpu_usage", "gpu_temp", "network"]
    assert (hud.width(), hud.height()) == (280, 290)
    assert len(saved) == 1  # reset persists immediately
    _stop(hud)


def test_edit_bar_visibility(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    assert hud.edit_bar.isHidden()
    hud.enter_edit_mode()
    assert not hud.edit_bar.isHidden()
    hud.exit_edit_mode(save=True)
    assert hud.edit_bar.isHidden()
    _stop(hud)


def test_snap_aligns_moved_widgets(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.snap_enabled = True
    editor.press(QPoint(30, 40))  # grab cpu
    editor.move(QPoint(29, 31))  # raw (21, 21) snaps to (24, 24)
    assert (hud.widgets[0].bounds.x(), hud.widgets[0].bounds.y()) == (24, 24)
    editor.release(QPoint(29, 31))
    _stop(hud)


def test_snap_resize_snaps_dimensions(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.snap_enabled = True
    editor.press(QPoint(250, 60))  # cpu resize handle
    editor.move(QPoint(240, 71))  # 226x49 snaps to 224x48
    assert (hud.widgets[0].bounds.width(), hud.widgets[0].bounds.height()) == (224, 48)
    editor.release(QPoint(240, 71))
    _stop(hud)


def test_snap_window_resize(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.snap_enabled = True
    editor.press(QPoint(278, 288))  # HUD corner grip
    editor.move(QPoint(300, 300))  # 302x302 snaps to 304x304
    assert (hud.width(), hud.height()) == (304, 304)
    editor.release(QPoint(300, 300))
    _stop(hud)


def test_snap_add_places_aligned(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    editor.snap_enabled = True
    editor.add("cpu", QPoint(37, 60))  # raw (-71, 41) snaps toward (8, 40)
    assert (hud.widgets[-1].bounds.x(), hud.widgets[-1].bounds.y()) == (8, 40)
    _stop(hud)


def test_resize_grab_extends_beyond_corner(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    # A few pixels outside network's bottom-right still resizes it, not the window.
    assert editor.hit(QPoint(262, 276)) == (5, "resize")
    _stop(hud)


def test_window_grab_beats_whole_app_but_widget_wins(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    editor = hud.editor
    # Overlapping a widget's corner, the widget wins.
    assert editor.hit(QPoint(264, 270)) == (5, "resize")
    # Off the widgets but inside the big HUD corner zone -> resize the window.
    assert editor.hit(QPoint(262, 286)) == (-1, "window_resize")
    assert editor.hit(QPoint(270, 286)) == (-1, "window_resize")
    _stop(hud)


def test_edit_bar_snap_checkbox_toggles(monkeypatch):
    hud, _ = _make_hud(monkeypatch)
    hud.edit_bar.snap.setChecked(True)
    assert hud.editor.snap_enabled is True
    hud.edit_bar.snap.setChecked(False)
    assert hud.editor.snap_enabled is False
    _stop(hud)
