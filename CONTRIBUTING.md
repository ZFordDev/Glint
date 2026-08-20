# Contributing to Glint

Thank you for helping improve Glint. Bug reports, platform testing, documentation, design feedback, and focused code contributions are all welcome.

Please report security vulnerabilities through the private process in [SECURITY.md](SECURITY.md). Glint also follows the broader [ZFordDev project standards](https://github.com/ZFordDev/ZFordDev/blob/main/STANDARDS.md).

## Before you begin

- Search the [issue tracker](https://github.com/ZFordDev/Glint/issues) for an existing report.
- Open an issue before starting a substantial feature or architectural change.
- Keep changes aligned with Glint's lightweight, local-only system-monitoring role.
- Never include private machine information, usernames, hostnames, or unrelated logs in a report.

## Development setup

Glint requires Python 3.10 or later and a graphical desktop session.

```bash
git clone https://github.com/YOUR-USERNAME/Glint.git
cd Glint
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
python main.py
```

Create a focused branch from the latest `main` branch:

```bash
git switch -c fix/short-description
```

## Making changes

- Keep pull requests limited to one logical change.
- Preserve graceful fallbacks when a metric, platform feature, or system tray is unavailable.
- Keep platform-specific imports and behavior isolated behind runtime checks.
- Avoid heavy dependencies unless the benefit clearly justifies the download and maintenance cost.
- Keep drawing logic in the UI layer and sensor collection in `src/core/`.
- Update the README and DocsHub pages when behavior, packaging, or platform support changes.
- Do not turn sensor readings into persistent history, telemetry, or network traffic without prior discussion.

## Testing

Run the automated checks before opening a pull request:

```bash
ruff format --check .
ruff check .
python -m pytest
```

Also launch Glint and manually exercise the changed workflow. Platform-sensitive changes should be tested on Windows, macOS, and Linux when possible. If you cannot test a platform, say so clearly in the pull request.

For UI changes, check HUD dragging, the independent Settings window, tray restoration, opacity, both built-in themes, and behavior when optional sensor values are unavailable. For release changes, use the GitHub Release workflow's non-publishing rehearsal mode or run the equivalent release-script validation locally.

## Pull requests

1. Push your branch and open a pull request against `main`.
2. Explain what changed, why it changed, and how it was tested.
3. Link related issues with a keyword such as `Fixes #123` when appropriate.
4. Include screenshots for visible HUD or Settings changes.
5. Keep unrelated formatting and refactoring out of the pull request.

Clear, present-tense commit messages are appreciated.

## Good bug reports

Please include:

- Glint version and whether it came from a release archive or source
- Operating system, version, architecture, desktop environment, and display server where relevant
- CPU/GPU model and driver when the problem involves sensors
- Clear reproduction steps and expected versus actual behavior
- Relevant logs or screenshots with personal information removed

Thank you for contributing to Glint.
