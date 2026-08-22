<div align="center">

<img src="src/assets/icon.svg" width="112" alt="Glint icon">

# Glint

### A lightweight system-monitor HUD for Windows, macOS, and Linux

[Documentation](https://docs.zford.dev/zforddev/glint/) · [Downloads](https://github.com/ZFordDev/Glint/releases/latest) · [Report a bug](https://github.com/ZFordDev/Glint/issues/new)

[![Release](https://img.shields.io/github/v/release/ZFordDev/Glint?label=release)](https://github.com/ZFordDev/Glint/releases/latest)
[![Checks](https://github.com/ZFordDev/Glint/actions/workflows/python-app.yml/badge.svg)](https://github.com/ZFordDev/Glint/actions/workflows/python-app.yml)
![Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-6b8afd)
[![License](https://img.shields.io/github/license/ZFordDev/Glint)](LICENSE)

</div>

Glint keeps essential system information visible in a compact, translucent desktop HUD. It is built with PyQt 6 and drawn directly with `QPainter`, keeping the application small and avoiding a browser or Electron runtime.

CPU, memory, disk, GPU, temperature, and network readings are collected locally. Hardware-specific readings degrade gracefully: when a sensor is not exposed by the operating system or driver, Glint shows it as unavailable and continues running.

## Highlights

- Native, frameless PyQt 6 HUD with persistent positioning
- CPU, RAM, disk, GPU, temperature, upload, and download widgets
- Independent Settings window with live refresh-rate, opacity, and theme controls
- Default and Midnight themes with JSON-backed custom layouts
- System tray controls for showing Glint, opening Settings, autostart, and exit
- Native autostart entries for Windows, macOS, and freedesktop Linux desktops
- Standalone GitHub Release archives that do not require Python

## Download

Download the archive for your system from the [latest GitHub Release](https://github.com/ZFordDev/Glint/releases/latest):

| Platform | Release asset |
| --- | --- |
| Windows x86-64 | `glint-windows-x86_64.zip` |
| macOS Apple silicon | `glint-macos-arm64.zip` |
| macOS Intel | `glint-macos-x86_64.zip` |
| Linux x86-64 | `glint-linux-x86_64.tar.gz` |

Extract the archive and launch `Glint` (`Glint.exe` on Windows). Release checksums are published in `SHA256SUMS`.

> [!NOTE]
> Glint's standalone archives are currently unsigned. Windows SmartScreen or macOS Gatekeeper may ask you to confirm that you trust the download. Official builds are published only through this repository's GitHub Releases.

## Use Glint

| Action | Result |
| --- | --- |
| Left-click and drag the HUD | Move it and remember the new position |
| Right-click the HUD | Open Settings or exit Glint |
| Double-click the tray icon | Show and raise the HUD |
| Open the tray menu | Show Glint, open Settings, manage autostart, or exit |

Settings and layouts are stored in the operating system's application configuration directory. The generated `default_layout.json` can be edited to change the HUD size, widget order, positions, and disk selection. See the [Glint documentation](https://docs.zford.dev/zforddev/glint/) for examples and platform notes.

## Sensor support

| Metric | Windows | macOS | Linux |
| --- | --- | --- | --- |
| CPU, RAM, disk, network | `psutil` | `psutil` | `psutil` |
| CPU temperature | WMI when exposed | `psutil` when exposed | hwmon through `psutil` |
| NVIDIA GPU usage and temperature | `nvidia-smi` | `nvidia-smi` when supported | `nvidia-smi` |
| AMD/Intel GPU usage | Windows performance counters | Unavailable fallback | Unavailable fallback |
| Other GPU temperatures | Platform sensor when exposed | Platform sensor when exposed | hwmon when exposed |

Temperature and GPU availability varies by hardware, driver, permissions, and operating system. Wayland compositors may also prevent applications from forcing the HUD below other windows; Glint remains frameless and usable when that hint is ignored.

## Run from source

Glint requires Python 3.10 or later and a graphical desktop session.

```bash
git clone https://github.com/ZFordDev/Glint.git
cd Glint
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install .
glint
```

For development:

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
python -m pytest
python main.py
```

The test workflow runs on Windows, macOS, and Linux for every pull request and push to `main`.

## Data and privacy

Glint has no accounts, analytics, telemetry, advertising, or cloud service. System readings are displayed locally and are not written to history or transmitted. Only preferences, the HUD position, and layout files are saved on the device. Read the full [privacy statement](PRIVACY.md).

## Project status

Glint v1.0.0 is the first stable, cross-platform release. Distribution is intentionally minimal and GitHub-exclusive: there are no Microsoft Store, Mac App Store, Snap Store, or other store packages, and there is no in-application updater; new versions are downloaded manually from GitHub Releases.

Releases are built by GitHub Actions from matching `v*` tags. The workflow verifies formatting, lint, tests, and version consistency before creating native archives and SHA-256 checksums. Maintainer details are documented in [architecture and maintenance notes](https://docs.zford.dev/zforddev/glint/maintenance/).

## Contributing and support

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before preparing a change.
- Use the [issue tracker](https://github.com/ZFordDev/Glint/issues) for reproducible bugs and focused feature requests.
- Report vulnerabilities privately using [SECURITY.md](SECURITY.md).
- Review release history in [CHANGELOG.md](CHANGELOG.md).

## License

Glint is open-source software released under the [MIT License](LICENSE).
