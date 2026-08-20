# Glint Privacy Statement

**Effective date:** v1.0.0 (August 2026)

## Local-only monitoring

Glint is a local desktop system monitor. It reads operating-system and hardware metrics to render the HUD on your device. Glint does not upload, synchronise, sell, or otherwise transmit those readings.

## What Glint reads

- CPU and memory utilisation
- Mounted-disk labels and utilisation
- Network byte counters used to calculate current upload and download rates
- Temperature and GPU utilisation when exposed by the operating system, driver, WMI, or `nvidia-smi`

These readings are held only long enough to update the display. Glint does not maintain a monitoring history or write sensor values to disk.

## What Glint stores

Glint stores a small local configuration containing the refresh interval, opacity, selected theme, layout name, and HUD position. It also stores JSON layout files describing the HUD size and widget placement. These files remain in the operating system's application configuration directory.

Glint has:

- no accounts or sign-in;
- no analytics or telemetry;
- no advertising or tracking;
- no cloud storage or synchronisation; and
- no built-in network update checker.

Updates are downloaded manually from [GitHub Releases](https://github.com/ZFordDev/Glint/releases). Visiting GitHub is governed by GitHub's own privacy terms; the Glint application itself does not contact GitHub.

## Questions

For privacy questions, open an issue at [github.com/ZFordDev/Glint/issues](https://github.com/ZFordDev/Glint/issues) or inspect the source code in this repository.
