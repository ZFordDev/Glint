# Glint Privacy Statement

**Effective date:** v1.0.4 (September 2026)

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
- an optional update checker that contacts GitHub only when you enable it in Settings.

When update checking is enabled, Glint makes a background request to the GitHub Releases API to see whether a newer release tag exists. The request is made without an account or Glint-specific identifier. GitHub may process the request's normal network metadata under [GitHub's privacy terms](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement). Glint does not send sensor readings, preferences, layouts, usernames, hostnames, or other application data in that request.

Update checking is disabled by default. You can turn it off at any time in Settings. Glint never downloads or installs updates itself; selecting an available update opens the GitHub release page in your browser. You can also download releases manually from [GitHub Releases](https://github.com/ZFordDev/Glint/releases).

## Questions

For privacy questions, open an issue at [github.com/ZFordDev/Glint/issues](https://github.com/ZFordDev/Glint/issues) or inspect the source code in this repository.
