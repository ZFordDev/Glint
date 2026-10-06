import json
import time
from unittest.mock import Mock, patch

from src.core.sensors import SensorReader
from src.core.settings_storage import DEFAULT_SETTINGS, load_settings, save_settings
from src.core.theme import build_theme, load_theme
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


def test_old_settings_default_to_glint_title(tmp_path):
    # Regression: settings written by earlier builds lack the "title" field.
    target = tmp_path / "settings.json"
    target.write_text('{"theme": "default"}', encoding="utf-8")
    assert load_settings(target)["title"] == "Glint"


def test_empty_title_falls_back_to_glint(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text('{"title": ""}', encoding="utf-8")
    assert load_settings(target)["title"] == "Glint"


def test_custom_title_round_trips(tmp_path):
    target = tmp_path / "settings.json"
    save_settings({**DEFAULT_SETTINGS, "title": "My Rig"}, target)
    assert load_settings(target)["title"] == "My Rig"


def test_check_updates_defaults_off(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text("{}", encoding="utf-8")
    assert load_settings(target)["check_updates"] is False


def test_check_updates_requires_boolean(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text('{"check_updates": "yes"}', encoding="utf-8")
    assert load_settings(target)["check_updates"] is False


def test_check_updates_round_trips(tmp_path):
    target = tmp_path / "settings.json"
    save_settings({**DEFAULT_SETTINGS, "check_updates": True}, target)
    assert load_settings(target)["check_updates"] is True


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


class _FakeGpuConnection:
    def __init__(self, engines):
        self.engines = engines
        self.queries = []

    def query(self, wql):
        self.queries.append(wql)
        return self.engines


class _FakeEngine:
    Name = "pid_1_eng_0_engtype_3D"
    UtilizationPercentage = 40


def test_slow_windows_gpu_probe_backs_off(monkeypatch):
    # Regression: probing the GPU counter set every tick pegged a CPU core on
    # machines where the provider is slow; slow probes must now be throttled.
    import src.core.sensors as sensors_module

    reader = SensorReader()
    connection = _FakeGpuConnection([_FakeEngine()])

    class SlowConnection:
        def query(self, wql):
            time.sleep(0.25)  # above the 0.2 s backoff threshold
            return connection.query(wql)

    monkeypatch.setattr(sensors_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(SensorReader, "_cimv2", lambda self: SlowConnection())
    first = reader._gpu()
    second = reader._gpu()  # inside the backoff window -> served from cache
    assert first == {"usage": 40.0, "temperature": None}
    assert second == first
    assert len(connection.queries) == 1


def test_windows_gpu_query_filters_and_handles_empty_counters(monkeypatch):
    import src.core.sensors as sensors_module

    reader = SensorReader()
    connection = _FakeGpuConnection([])
    monkeypatch.setattr(sensors_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(SensorReader, "_cimv2", lambda self: connection)
    assert reader._gpu() == {"usage": None, "temperature": None}
    assert "engtype_3D" in connection.queries[0]  # filtering happens server-side


def test_nvidia_smi_path_is_resolved_once(monkeypatch):
    # Regression: the PATH was rescanned on every sample.
    import src.core.sensors as sensors_module

    calls = []
    monkeypatch.setattr(sensors_module.shutil, "which", lambda name: calls.append(name) or "/usr/bin/nvidia-smi")
    reader = SensorReader()
    monkeypatch.setattr(sensors_module.platform, "system", lambda: "Linux")  # skip Windows fallback
    reader._gpu()
    reader._gpu()
    assert len(calls) == 1


def test_nvidia_smi_suppresses_console_only_on_windows(monkeypatch):
    import src.core.sensors as sensors_module

    reader = SensorReader()
    reader._nvidia_smi = "nvidia-smi"
    completed = Mock(stdout="40, 55\n")
    run = Mock(return_value=completed)
    monkeypatch.setattr(sensors_module.subprocess, "run", run)
    monkeypatch.setattr(sensors_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(sensors_module.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    assert reader._gpu() == {"usage": 40.0, "temperature": 55.0}
    assert run.call_args.kwargs["creationflags"] == 0x08000000

    run.reset_mock()
    monkeypatch.setattr(sensors_module.platform, "system", lambda: "Linux")
    assert reader._gpu() == {"usage": 40.0, "temperature": 55.0}
    assert "creationflags" not in run.call_args.kwargs


def test_get_all_skips_heavy_probes_after_stop():
    import threading

    reader = SensorReader()
    stop = threading.Event()
    stop.set()
    with (
        patch.object(reader, "_gpu") as gpu_mock,
        patch.object(reader, "_temperatures") as temps_mock,
        patch.object(reader, "_disks") as disks_mock,
    ):
        result = reader.get_all(stop=stop)
    gpu_mock.assert_not_called()
    temps_mock.assert_not_called()
    disks_mock.assert_not_called()
    assert set(result) == {"cpu", "ram", "disks", "temps", "gpu", "network"}  # schema stays stable
    assert result["gpu"] == {"usage": None, "temperature": None}


def test_bundled_default_theme_loads():
    assert load_theme()["colors"]["text"]


def test_custom_theme_defaults_to_empty(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text('{"theme": "default"}', encoding="utf-8")
    assert load_settings(target)["custom_theme"] == {}


def test_custom_theme_round_trips(tmp_path):
    target = tmp_path / "settings.json"
    overrides = {"text": "#FFABCDEF", "warning": "#80FFC850"}
    save_settings({**DEFAULT_SETTINGS, "custom_theme": overrides}, target)
    assert load_settings(target)["custom_theme"] == {"text": "#ffabcdef", "warning": "#80ffc850"}


def test_custom_theme_filters_invalid_entries(tmp_path):
    target = tmp_path / "settings.json"
    target.write_text(
        '{"custom_theme": {"text": "#FFABCDEF", "bogus": "#112233", "border": "not-a-color", "track": 7}}',
        encoding="utf-8",
    )
    assert load_settings(target)["custom_theme"] == {"text": "#ffabcdef"}


def test_build_theme_merges_overrides_and_ignores_junk():
    merged = build_theme("default", {"text": "#ABCDEF", "bogus": "#112233", "border": "nope"})
    assert merged["colors"]["text"] == "#ffabcdef"  # canonical #aarrggbb, alpha preserved
    assert "bogus" not in merged["colors"]
    assert merged["colors"]["border"] == load_theme("default")["colors"]["border"]


def test_build_theme_does_not_mutate_base_theme():
    base = load_theme("default")
    build_theme("default", {"warning": "#FFFF0000"})
    assert load_theme("default")["colors"]["warning"] == base["colors"]["warning"]


def test_glint_version_matches_pyproject():
    from src.core import version as version_module

    with version_module.PYPROJECT.open("rb") as source:
        expected = version_module.tomllib.load(source)["project"]["version"]
    assert version_module.glint_version() == expected


def test_update_is_newer_matrix():
    from src.core.update import is_newer

    assert is_newer("1.0.5", "1.0.4") is True
    assert is_newer("1.0.4", "1.0.4") is False  # equal -> up to date
    assert is_newer("1.0.3", "1.0.4") is False  # older latest -> up to date
    assert is_newer("banana", "1.0.4") is False  # malformed -> up to date
    assert is_newer(None, "1.0.4") is False
    assert is_newer("2.0.0", "1.9.9") is True


def test_update_urls_derived_from_pyproject():
    from src.core import update as update_module

    assert update_module.latest_release_url() == "https://api.github.com/repos/ZFordDev/Glint/releases/latest"
    assert update_module.releases_page_url() == "https://github.com/ZFordDev/Glint/releases/latest"


def test_repo_url_falls_back_to_installed_metadata(monkeypatch, tmp_path):
    # Regression: shipped installs have no pyproject.toml; the repository URL
    # must come from the bundled dist-info metadata instead.
    from src.core import update as update_module

    monkeypatch.setattr(update_module, "PYPROJECT", tmp_path / "missing.toml")
    assert update_module.repo_url() == "https://github.com/ZFordDev/Glint"
    assert update_module.latest_release_url() == "https://api.github.com/repos/ZFordDev/Glint/releases/latest"


def test_repo_url_requires_repository_entry(monkeypatch, tmp_path):
    import importlib.metadata

    from src.core import update as update_module

    monkeypatch.setattr(update_module, "PYPROJECT", tmp_path / "missing.toml")

    class Meta:
        def get_all(self, key):
            return ["Source, https://example.invalid/glint"]

    monkeypatch.setattr(importlib.metadata, "metadata", lambda name: Meta())
    assert update_module.repo_url() is None


def test_repo_url_none_when_uninstalled(monkeypatch, tmp_path):
    import importlib.metadata

    from src.core import update as update_module

    monkeypatch.setattr(update_module, "PYPROJECT", tmp_path / "missing.toml")

    def no_metadata(name):
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(importlib.metadata, "metadata", no_metadata)
    assert update_module.repo_url() is None


def test_latest_version_strips_tag_prefix(monkeypatch):
    from src.core import update as update_module

    monkeypatch.setattr(update_module, "_fetch_json", lambda url: {"tag_name": "v1.0.5"})
    assert update_module.latest_version() == "1.0.5"


def test_latest_version_failure_never_nags(monkeypatch):
    from src.core import update as update_module
    from src.core.update import is_newer

    monkeypatch.setattr(update_module, "_fetch_json", lambda url: None)
    assert update_module.latest_version() is None
    # A malformed returned tag must still resolve to "up to date".
    monkeypatch.setattr(update_module, "_fetch_json", lambda url: {"tag_name": "latest"})
    assert is_newer(update_module.latest_version(), "1.0.4") is False


def test_fetch_json_failure_is_failsafe(monkeypatch):
    from src.core import update as update_module

    def offline(url, timeout=5.0):
        raise OSError("offline")

    monkeypatch.setattr(update_module.urllib.request, "urlopen", offline)
    assert update_module._fetch_json("https://example.invalid/") is None


def test_low_spec_falls_back_when_cores_and_ram_are_legacy(monkeypatch):
    from src.core import compat

    monkeypatch.setattr(compat, "_logical_cores", lambda: 4)
    monkeypatch.setattr(compat, "_total_memory", lambda: 6 * 1024**3)
    assert compat.is_low_spec() is True


def test_low_spec_requires_both_undersized_metrics(monkeypatch):
    from src.core import compat

    # Plenty of RAM but few cores -> not legacy enough to degrade rendering.
    monkeypatch.setattr(compat, "_logical_cores", lambda: 2)
    monkeypatch.setattr(compat, "_total_memory", lambda: 32 * 1024**3)
    assert compat.is_low_spec() is False


def test_low_spec_tolerates_missing_probes(monkeypatch):
    from src.core import compat

    monkeypatch.setattr(compat, "_logical_cores", lambda: None)
    monkeypatch.setattr(compat, "_total_memory", lambda: None)
    assert compat.is_low_spec() is False
