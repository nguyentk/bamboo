#!/usr/bin/env python3
"""Assemble the Bamboo release artifacts and their SHA-256 checksums.

Collects, from `bin/`:
    Bamboo_v<version>_macOS.dmg              (misc/scripts/package_macos.sh)
    Bamboo_v<version>_win64.zip              (bamboo.windows.editor.x86_64[.llvm][.console].exe)
    Bamboo_v<version>_win64_setup.exe        (optional, misc/scripts/package_windows.sh)
    Bamboo_v<version>_linux.x86_64.tar.xz    (bamboo.linuxbsd.editor.x86_64)
    Bamboo_v<version>_export_templates.tpz   (misc/scripts/package_templates.py)
into `bin/release/<version>/` and writes `SHA256SUMS.txt` (same format as `sha256sum`).

Usage:
    python3 misc/scripts/package_release.py [--bin-dir bin] [--output-dir bin/release/<version>]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import os
import shutil
import sys
import tarfile
import zipfile
from typing import Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bamboo_versioning import REPO_ROOT, load_version  # noqa: E402


def artifact_names(version: str) -> dict[str, str]:
    return {
        "macos": f"Bamboo_v{version}_macOS.dmg",
        "windows": f"Bamboo_v{version}_win64.zip",
        "linux": f"Bamboo_v{version}_linux.x86_64.tar.xz",
        "templates": f"Bamboo_v{version}_export_templates.tpz",
    }


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(directory: str, names: Sequence[str]) -> str:
    path = os.path.join(directory, "SHA256SUMS.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for name in sorted(names):
            f.write(f"{sha256_file(os.path.join(directory, name))}  {name}\n")
    return path


def read_checksums(path: str) -> dict[str, str]:
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                digest, name = line.rstrip("\n").split("  ", 1)
                result[name] = digest
    return result


def _first(patterns: Sequence[str]) -> Optional[str]:
    for pattern in patterns:
        matches = sorted(p for p in glob.glob(pattern) if os.path.isfile(p))
        if matches:
            return matches[0]
    return None


def collect(bin_dir: str, output_dir: str, version: str) -> tuple[list[str], list[str]]:
    names = artifact_names(version)
    os.makedirs(output_dir, exist_ok=True)
    produced, missing = [], []

    dmg = _first([os.path.join(bin_dir, names["macos"]), os.path.join(bin_dir, "Bamboo_v*_macOS.dmg")])
    if dmg:
        shutil.copyfile(dmg, os.path.join(output_dir, names["macos"]))
        produced.append(names["macos"])
    else:
        missing.append(f"{names['macos']} (run misc/scripts/package_macos.sh)")

    windows = [
        p for p in sorted(glob.glob(os.path.join(bin_dir, "bamboo.windows.editor.x86_64*.exe"))) if ".dev." not in p
    ]
    if windows:
        with zipfile.ZipFile(os.path.join(output_dir, names["windows"]), "w", zipfile.ZIP_DEFLATED) as archive:
            for path in windows:
                archive.write(path, os.path.basename(path))
        produced.append(names["windows"])
    else:
        missing.append(f"{names['windows']} (no bamboo.windows.editor.x86_64*.exe in {bin_dir})")

    # Optional: the NSIS installer is shipped next to the portable .zip when it has been built.
    setup_name = f"Bamboo_v{version}_win64_setup.exe"
    setup = _first([os.path.join(bin_dir, setup_name), os.path.join(bin_dir, "Bamboo_v*_win64_setup.exe")])
    if setup:
        shutil.copyfile(setup, os.path.join(output_dir, setup_name))
        produced.append(setup_name)

    linux = _first([os.path.join(bin_dir, "bamboo.linuxbsd.editor.x86_64")])
    if linux:
        with tarfile.open(os.path.join(output_dir, names["linux"]), "w:xz") as archive:
            archive.add(linux, os.path.basename(linux))
        produced.append(names["linux"])
    else:
        missing.append(f"{names['linux']} (no bamboo.linuxbsd.editor.x86_64 in {bin_dir})")

    tpz = _first([
        os.path.join(bin_dir, f"Bamboo_v{version}_templates.tpz"),
        os.path.join(bin_dir, "Bamboo_v*_templates.tpz"),
    ])
    if tpz:
        shutil.copyfile(tpz, os.path.join(output_dir, names["templates"]))
        produced.append(names["templates"])
    else:
        missing.append(f"{names['templates']} (run misc/scripts/package_templates.py)")

    if produced:
        write_checksums(output_dir, produced)
    return produced, missing


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble Bamboo release artifacts with SHA-256 checksums.")
    parser.add_argument("--bin-dir", default=os.path.join(REPO_ROOT, "bin"))
    parser.add_argument("--output-dir")
    parser.add_argument("--strict", action="store_true", help="Fail when any platform artifact is missing.")
    args = parser.parse_args(argv)

    version = load_version().bamboo_string
    output_dir = args.output_dir or os.path.join(args.bin_dir, "release", version)
    produced, missing = collect(args.bin_dir, output_dir, version)
    for name in produced:
        print(f"  {name}")
    for item in missing:
        print(f"WARNING: missing {item}", file=sys.stderr)
    if not produced:
        print("ERROR: no release artifact found.", file=sys.stderr)
        return 1
    print(f"Wrote {os.path.join(output_dir, 'SHA256SUMS.txt')}")
    return 1 if (args.strict and missing) else 0


if __name__ == "__main__":
    sys.exit(main())
