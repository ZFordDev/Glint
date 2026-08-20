"""Build and validate Glint's minimal GitHub Release bundles."""

from __future__ import annotations

import argparse
import hashlib
import platform
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 support
    import tomli as tomllib

ROOT = Path(__file__).parents[1]


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as source:
        return tomllib.load(source)["project"]["version"]


def verify_tag(tag: str) -> None:
    expected = f"v{project_version()}"
    if tag != expected:
        raise SystemExit(f"Release tag {tag!r} does not match pyproject.toml version {expected!r}")


def build(asset_name: str, archive: str) -> Path:
    """Create a native PyInstaller onedir bundle and archive it."""
    build_root = ROOT / "build" / "release"
    bundle_root = ROOT / "dist" / "Glint"
    output_root = ROOT / "dist-release"
    shutil.rmtree(build_root, ignore_errors=True)
    shutil.rmtree(ROOT / "dist", ignore_errors=True)
    output_root.mkdir(exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        "Glint",
        "--workpath",
        str(build_root),
        "--specpath",
        str(build_root),
        "--add-data",
        f"{ROOT / 'src' / 'themes.json'}:src",
        "--add-data",
        f"{ROOT / 'assets'}:assets",
        str(ROOT / "main.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    # Put the macOS .app and documentation inside the same simple top-level
    # folder used by Windows and Linux.
    if platform.system() == "Darwin":
        application = ROOT / "dist" / "Glint.app"
        if not application.exists():
            raise SystemExit(f"PyInstaller did not create expected bundle: {application}")
        # A windowed onedir macOS build emits both Glint/ and the complete
        # Glint.app. The former is only an intermediate COLLECT output; reuse
        # its name for the human-friendly release folder.
        shutil.rmtree(bundle_root)
        bundle_root.mkdir()
        shutil.move(application, bundle_root / application.name)
    elif not bundle_root.exists():
        raise SystemExit(f"PyInstaller did not create expected bundle: {bundle_root}")
    bundle = bundle_root
    for document in ("README.md", "LICENSE"):
        shutil.copy2(ROOT / document, bundle / document)

    base = output_root / asset_name
    if archive == "zip":
        if platform.system() == "Darwin":
            # ditto preserves macOS bundle metadata and framework symlinks.
            result = base.with_suffix(".zip")
            subprocess.run(
                ["/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", bundle, result], check=True
            )
        else:
            result = Path(shutil.make_archive(str(base), "zip", bundle.parent, bundle.name))
    else:
        result = Path(shutil.make_archive(str(base), "gztar", bundle.parent, bundle.name))
    print(result)
    return result


def checksums(directory: Path) -> Path:
    assets = sorted(path for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    target = directory / "SHA256SUMS"
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in assets]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify-tag")
    verify.add_argument("tag")
    package = commands.add_parser("build")
    package.add_argument("--asset-name", required=True)
    package.add_argument("--archive", choices=("zip", "gztar"), required=True)
    sums = commands.add_parser("checksums")
    sums.add_argument("directory", type=Path)
    arguments = parser.parse_args()
    if arguments.command == "verify-tag":
        verify_tag(arguments.tag)
    elif arguments.command == "build":
        build(arguments.asset_name, arguments.archive)
    else:
        checksums(arguments.directory)


if __name__ == "__main__":
    main()
