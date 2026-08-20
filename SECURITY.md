# Security Policy

Glint welcomes responsible reports that help keep its users and systems safe.

## Supported versions

Security fixes target the latest stable release and the current development branch. Older releases, forks, modified builds, and unofficial distributions may not receive fixes. Users should update to the latest stable GitHub Release when a security update is published.

## Report a vulnerability privately

Use [GitHub's private vulnerability reporting](https://github.com/ZFordDev/Glint/security/advisories/new) whenever possible.

If that form is unavailable, email [zforddev@gmail.com](mailto:zforddev@gmail.com) with `Glint security report` in the subject line.

Do not open a public issue, discussion, or pull request for an unpatched vulnerability. Include the affected version and platform, potential impact, reproduction steps or a minimal proof of concept, and any useful logs with personal information removed.

Reports made in good faith should avoid accessing data that is not yours, disrupting other systems, or causing harm. The maintainer will review the report, attempt to reproduce it, prepare a fix or mitigation when appropriate, and coordinate disclosure through the original private channel.

## Scope

This policy covers Glint's source code and official GitHub Release archives, including sensor collection, configuration and layout file handling, autostart integration, packaging, and bundled dependencies.

The following are generally outside scope unless they create a vulnerability in an official release:

- Unsupported versions, forks, and modified or unofficial builds
- Vulnerabilities that require an already-compromised operating system
- Hardware or driver behavior that only makes a metric unavailable or inaccurate
- Reports that identify an outdated dependency without demonstrating relevant impact

## Security characteristics

Glint reads local operating-system metrics and may call locally installed facilities such as WMI or `nvidia-smi`. It does not require administrator privileges, expose a network service, collect telemetry, or transmit sensor readings. Preferences and layouts are stored locally in the platform application configuration directory.

Official archives are currently unsigned. Verify downloads against the `SHA256SUMS` file attached to the same GitHub Release and obtain releases only from `github.com/ZFordDev/Glint`.
