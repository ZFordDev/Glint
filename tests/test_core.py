import json
from unittest.mock import Mock, patch

from src.core.sensors import SensorReader
from src.core.settings_storage import DEFAULT_SETTINGS, load_settings, save_settings
from src.core.theme import load_theme
from src.ui.layout import create_widgets, load_layout, save_layout


def test_settings_round_trip_and_validation(tmp_path):
    target = tmp_path / "settings.json"
    saved = save_settings({**DEFAULT_SETTINGS, "opacity": 0.7, "refresh_interval_ms": 500}, target)
    assert load_settings(target) == saved
    target.write_text('{"opacity": 4, "refresh_interval_ms": 2}', encoding="utf-8")
    assert load_settings(target)["opacity"] == DEFAULT_SETTINGS["opacity"]


def test_invalid_json_uses_defaults(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text("not json", encoding="utf-8")
    assert load_settings(target) == DEFAULT_SETTINGS


def test_layout_round_trip(tmp_path):
    widgets = create_widgets(load_layout(path=tmp_path / "missing.json"))
    target = tmp_path / "layout.json"
    save_layout(widgets, 300, 400, path=target)
    loaded = load_layout(path=target)
    assert (loaded["width"], loaded["height"]) == (300, 400)
    assert [item["type"] for item in loaded["widgets"]] == [widget.widget_type for widget in widgets]


def test_wrong_shape_layout_falls_back_to_defaults(tmp_path):
    # Regression: a valid-JSON layout with a non-list "widgets" used to raise
    # an uncaught TypeError instead of falling back.
    target = tmp_path / "layout.json"
    target.write_text('{"widgets": 3}', encoding="utf-8")
    assert load_layout(path=target) == load_layout(path=tmp_path / "missing.json")


def test_malformed_widget_entries_are_dropped(tmp_path):
    # Regression: non-numeric geometry crashed QRectF during instantiation.
    target = tmp_path / "layout.json"
    target.write_text(
        json.dumps(
            {
                "width": 280,
                "height": 290,
                "widgets": [
                    {"type": "cpu", "x": "abc", "y": 30, "width": 236, "height": 38},
                    {"type": "ram", "x": 22, "y": True, "width": 236, "height": 38},
                    {"type": "disk", "x": 22, "y": 72, "width": 236, "height": 38, "disk": 7},
                    {"type": "network", "x": 22, "y": 244, "width": 236, "height": 28},
                ],
            }
        ),
        encoding="utf-8",
    )
    widgets = create_widgets(load_layout(path=target))
    assert [widget.widget_type for widget in widgets] == ["network"]


def test_network_throughput_is_delta_per_second():
    first = Mock(bytes_sent=100, bytes_recv=200)
    second = Mock(bytes_sent=1124, bytes_recv=2248)
    with (
        patch("src.core.sensors.psutil.net_io_counters", side_effect=[first, second]),
        patch("src.core.sensors.time.monotonic", side_effect=[10.0, 12.0]),
    ):
        reader = SensorReader()
        assert reader._network_rates() == {"upload": 512.0, "download": 1024.0}


def test_sensor_schema_is_stable_without_optional_hardware():
    reader = SensorReader()
    with (
        patch.object(reader, "_gpu", return_value={"usage": None, "temperature": None}),
        patch.object(reader, "_temperatures", return_value={"cpu": None, "gpu": None}),
        patch.object(reader, "_disks", return_value={}),
    ):
        result = reader.get_all()
    assert set(result) == {"cpu", "ram", "disks", "temps", "gpu", "network"}


def test_bundled_default_theme_loads():
    assert load_theme()["colors"]["text"]
