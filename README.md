# Glint

Glint is a lightweight, painter-rendered desktop system monitor for Windows, macOS, and Linux. It displays CPU, memory, disk, GPU, temperature, and live network metrics without a browser or Electron runtime.

## Highlights

- Native PyQt 6 HUD and system tray
- Portable CPU, RAM, disk, temperature, and network sensors through `psutil`
- NVIDIA GPU usage and temperature through `nvidia-smi`, with graceful fallback on other hardware
- JSON-backed settings and user-defined widget layouts
- Built-in themes and serializable painter-rendered widgets
- Native autostart entries for Windows, macOS, and freedesktop Linux desktops

Unavailable hardware metrics display as “Unavailable”; they do not prevent Glint from starting.

## Requirements

- Python 3.10 or later
- Windows 10+, a current macOS release, or a Linux desktop with a system tray
- A graphical desktop session

Linux packages may require Qt system libraries supplied by the distribution. Wayland desktop-shell rules can prevent applications from forcing a window below every other window; the HUD remains frameless and behaves normally in that case.

## Install and run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install .
glint
```

For development:

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
python main.py
```

## Controls

- Left-click and drag moves the HUD.
- Right-click opens Settings or exits.
- Double-clicking the tray icon restores the HUD.
- The tray menu controls autostart.

Settings and layouts use the operating system's application configuration directory. A generated `default_layout.json` can contain multiple disk widgets; set each widget's `disk` field to its device label.

## Sensor support

| Metric | Windows | macOS | Linux |
| --- | --- | --- | --- |
| CPU, RAM, disk, network | `psutil` | `psutil` | `psutil` |
| CPU temperature | WMI when exposed | `psutil` when exposed | hwmon through `psutil` |
| GPU usage | `nvidia-smi`, then WMI for AMD/Intel | `nvidia-smi` when supported | `nvidia-smi` |
| Other GPU temperature | unavailable fallback | platform sensor when exposed | hwmon when exposed |

Hardware and driver vendors expose sensors inconsistently, so temperature and GPU metrics are optional by design.

## Project layout

```text
src/
  core/       sensors, settings, themes
  ui/         HUD, tray, settings, layouts
    widgets/  independent painter widgets
  app.py      application entry point
tests/        core behavior tests
```

## License

MIT

## Releases

Glint is distributed exclusively through GitHub Releases as minimal standalone archives—there are no Microsoft Store, Snap Store, or other store packages.

The archives are currently unsigned. Windows SmartScreen and macOS Gatekeeper may therefore ask users to confirm that they trust the download. Code signing can be added later without changing the GitHub-only distribution model.

Maintainers publish a release by updating `project.version` in `pyproject.toml`, merging the tested change to `main`, and pushing a matching tag such as `v1.0.0`. GitHub Actions then:

1. verifies formatting, lint, tests, and the tag/version match;
2. builds native Windows, macOS, and Linux bundles with PyInstaller;
3. creates SHA-256 checksums; and
4. publishes the archives and generated notes to the tagged GitHub Release.

The workflow can also be started manually in rehearsal mode, which validates and builds without publishing. Enabling its `publish` input requires an existing matching tag and creates the release after all builds succeed.
