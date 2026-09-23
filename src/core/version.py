"""Glint version resolution for source, installed, and frozen environments."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 support
    import tomli as tomllib  # type: ignore[no-redef]

PYPROJECT = Path(__file__).parents[2] / "pyproject.toml"


def _from_pyproject() -> str | None:
    try:
        with PYPROJECT.open("rb") as source:
            return tomllib.load(source)["project"]["version"]
    except (OSError, KeyError):
        return None


def _from_metadata() -> str | None:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("glint-monitor")
    except PackageNotFoundError:
        return None


@lru_cache(maxsize=1)
def glint_version() -> str:
    """Return the version string, preferring the source tree over installed metadata."""
    return _from_pyproject() or _from_metadata() or "dev"