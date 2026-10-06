# Changelog

## v1.0.4 (2026-10-06)

### Info
> Glint dosnt need updates, if it works for you in its current form i wouldn't force a update just to be on the latest build, version `1.0.3` should work for most systems so updates after that will mostly be cosmetic and customisable options. 

### Plan
- ~~add version in footer pulled from meta on build~~
- ~~add name to header (still small and non invasive )~~
- ~~add a optinable notify for updates in the menu~~
- ~~building settings/layout~~
- ~~adding custom theme otions in settings/appearance~~

### Added

- Version number in the HUD footer, resolved from `pyproject.toml` in source checkouts and from bundled package metadata in release builds
- Customizable Title Name in the HUD header, set from the Settings window (defaults to Glint)
- Opt-in update notifications: when enabled, a yellow dot appears on the HUD and a Get update item appears in the tray menu pointing to the release page (Glint never self-updates)
- Live on-HUD layout editor (Edit Layout in the tray or Settings): drag widgets, resize them from their corner grip, resize the HUD from the window corner, and remove or add widgets from the right-click menu — Save persists, Discard and Esc revert, Reset restores the defaults. An optional Snap to grid toggle in the edit bar aligns widget positions and sizes, and the corner grips are sized to be forgiving of near-misses
- Per-color theme overrides in Settings → Appearance: pick any of the 11 theme colors (alpha included) for the HUD, layered on top of the selected theme and persisted in settings — Reset buttons restore the theme default per color, and a live Preview applies changes to the HUD immediately

### Fixed

### Docs

- Documented the opt-in update notification behavior and its privacy implications.
- Updated the privacy statement for GitHub release metadata checks.
- Updated the security policy for optional outbound requests, unsigned archives, and checksum verification.
- Updated contributor guidance for 1.0.4 UI, testing, and release workflows.

## v1.0.3 (2026-09-22)

Small but crucial maintenance patch for the 1.0 series.

### Fixed

- Systems with NVIDIA GPUs no longer spawn a repeated visible console window while metrics refresh, which rendered the app unusable [#21]

## v1.0.2 (2026-09-04)

### Info
> **Release Cadence Update:** Planned releases are shifting from weekly to fortnightly (targeting Wednesdays) as we transition toward a monthly release cycle. Critical fixes will still be released immediately as emergency patches.

### Plan

### Added

### Fixed

- Aggressive window refresh loop and focus-stealing on Windows [#19]
- Legacy hardware (≤4 cores and ≤8 GiB RAM) falls back to software rendering on every platform, sidestepping the GPU/DWM recomposition loop behind the flicker
- Software-rendering fallback uses Qt's `AA_UseSoftwareOpenGL` (Qt 6 removed `AA_DisableHardwareAcceleration`)

### Docs

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
