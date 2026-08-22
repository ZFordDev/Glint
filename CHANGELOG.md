# Changelog

All notable user-facing changes to Glint are recorded here.

## v1.0.1 (2026-08-22)

Stability and performance release for the 1.0 series.

### Fixed

- Malformed or wrong-shaped widget layout files fall back to defaults instead of preventing startup
- Exiting from the tray menu now saves the HUD layout, matching the HUD context-menu Exit
- Autostart entries launch frozen builds correctly and quote install paths containing spaces
- Standalone wheel installs show the tray icon again (icon now ships inside the package)
- Empty Windows GPU counter sets display Unavailable instead of 0%

### Changed

- Sensor sampling moved off the GUI thread so dragging and painting never wait on probes
- Slow Windows GPU-counter providers throttle automatically instead of consuming a CPU core
- Removed the unsupported legacy updater prototype

[v1.0.1 release](https://github.com/ZFordDev/Glint/releases/tag/v1.0.1)

## v1.0.0 (2026-08-20)

Glint's first stable release turns the original Windows prototype into a tested, cross-platform desktop monitor.

### Added

- Cross-platform application and system tray support for Windows, macOS, and Linux
- CPU, RAM, disk, GPU usage, GPU temperature, and live network widgets
- Portable sensor collection through `psutil`, optional Windows WMI, and `nvidia-smi`
- Independent Settings window with live refresh interval, opacity, and theme controls
- Default and Midnight themes
- Versioned JSON preferences, persistent HUD position, and editable widget layouts
- Native autostart entries for Windows, macOS, and freedesktop Linux desktops
- Tests and formatting checks across all three supported operating systems
- Automated native GitHub Release archives and SHA-256 checksums

### Fixed

- Restored HUD dragging, including compositor-assisted movement on Wayland
- Prevented Settings from behaving like a panel attached to the frameless HUD
- Made unavailable hardware readings fail gracefully instead of blocking startup
- Corrected Python packaging, console entry points, dependencies, and macOS application bundles

### Changed

- Consolidated project dependencies in `pyproject.toml`
- Replaced the old Windows-only implementation with shared platform-aware modules
- Adopted GitHub Releases as the only official distribution channel

[v1.0.0 release](https://github.com/ZFordDev/Glint/releases/tag/v1.0.0)
