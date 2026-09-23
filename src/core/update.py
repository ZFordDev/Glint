"""Opt-in update notification lookups. Glint never self-updates; it only reports."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from src.core.version import PYPROJECT, glint_version

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 support
    import tomli as tomllib  # type: ignore[no-redef]


def repo_url() -> str | None:
    """Resolve the repository URL from the source tree or packaged metadata.

    Users never need pyproject.toml at runtime; installed wheels and frozen
    bundles carry the URL inside their dist-info metadata generated at build.
    """
    try:
        with PYPROJECT.open("rb") as source:
            return tomllib.load(source)["project"]["urls"]["Repository"]
    except (OSError, KeyError):
        pass
    try:
        from importlib.metadata import PackageNotFoundError, metadata

        project_urls = metadata("glint-monitor").get_all("Project-URL") or []
    except PackageNotFoundError:
        return None
    for entry in project_urls:
        if entry.startswith("Repository, "):
            return entry.split("Repository, ", 1)[1].strip()
    return None


def latest_release_url() -> str | None:
    url = repo_url()
    if not url or "github.com/" not in url:
        return None
    owner_repo = url.split("github.com/", 1)[1].strip("/")
    return f"https://api.github.com/repos/{owner_repo}/releases/latest"


def releases_page_url() -> str | None:
    url = repo_url()
    if not url or "github.com/" not in url:
        return None
    owner_repo = url.split("github.com/", 1)[1].strip("/")
    return f"https://github.com/{owner_repo}/releases/latest"


def _version_tuple(version: str) -> tuple[int, ...] | None:
    parts = tuple(part for part in version.split(".") if part.isdigit())
    if not parts:
        return None
    return tuple(int(part) for part in parts)


def is_newer(latest: str | None, current: str | None) -> bool:
    """True only when ``latest`` is strictly newer than ``current``.

    Equal versions and older releases (including malformed input) report up to
    date so the app never nags about a downgrade or an unparseable tag.
    """
    if not latest or not current:
        return False
    latest_tuple = _version_tuple(latest)
    current_tuple = _version_tuple(current)
    if latest_tuple is None or current_tuple is None:
        return False
    return latest_tuple > current_tuple


def _fetch_json(url: str, timeout: float = 5.0) -> dict[str, Any] | None:
    request = urllib.request.Request(url, headers={"User-Agent": "Glint/" + glint_version()})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload if isinstance(payload, dict) else None
    except (OSError, ValueError):  # network, timeout, HTTP, and parse failures
        return None


def latest_version() -> str | None:
    url = latest_release_url()
    if url is None:
        return None
    payload = _fetch_json(url)
    if payload is None:
        return None
    tag = payload.get("tag_name")
    return tag.lstrip("v") if isinstance(tag, str) and tag else None