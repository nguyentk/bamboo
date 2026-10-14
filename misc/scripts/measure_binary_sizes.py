#!/usr/bin/env python3
"""Measure Bamboo binary sizes and compare build profiles against the reference build.

Finds `bamboo.<platform>.<target>.<arch>[.<suffix>]` binaries in `--bin-dir`, measures the
uncompressed and compressed (zip deflate, gzip -9) sizes, and writes a Markdown table comparing
each profile build (`.2d`, `.mobile`, `.pc`, ...) with the build of the same platform/target/arch
without a suffix (or the `.pc` profile when the plain build is missing).

Usage:
    python3 misc/scripts/measure_binary_sizes.py [--bin-dir bin] [--output docs/reports/binary_size_benchmark.md]
"""

from __future__ import annotations

import argparse
import gzip
import io
import os
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from typing import Optional, Sequence

# bamboo.macos.template_release.arm64[.2d]   (Windows: ... .exe, optional .llvm / .console)
BINARY_RE = re.compile(
    r"^(?P<prefix>[a-z]+)\.(?P<platform>[a-z]+)\.(?P<target>editor|template_debug|template_release)"
    r"(?P<dev>\.dev)?(?P<double>\.double)?\.(?P<arch>x86_64|x86_32|arm64|arm32|universal|rv64|wasm32)"
    r"(?P<llvm>\.llvm)?(?:\.(?P<suffix>[a-z0-9_]+))?(?P<ext>\.exe)?$"
)
REFERENCE_SUFFIXES = ("", "pc")


@dataclass
class BinaryInfo:
    name: str
    path: str
    key: str  # platform.target.arch (+dev/double)
    suffix: str
    size: int
    zip_size: int
    gzip_size: int


def compressed_sizes(path: str) -> tuple[int, int]:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(path, os.path.basename(path))
    gz_buffer = io.BytesIO()
    with open(path, "rb") as src, gzip.GzipFile(fileobj=gz_buffer, mode="wb", compresslevel=9, mtime=0) as dst:
        shutil.copyfileobj(src, dst, 1 << 20)
    return zip_buffer.tell(), gz_buffer.tell()


def find_binaries(bin_dir: str, compress: bool = True) -> list[BinaryInfo]:
    if not os.path.isdir(bin_dir):
        raise FileNotFoundError(f"Binary directory not found: {bin_dir}")
    found = []
    for name in sorted(os.listdir(bin_dir)):
        match = BINARY_RE.match(name)
        path = os.path.join(bin_dir, name)
        if not match or not os.path.isfile(path) or match.group("suffix") == "console":
            continue
        key = ".".join(
            p
            for p in (
                match.group("platform"),
                match.group("target"),
                match.group("dev") and "dev",
                match.group("double") and "double",
                match.group("arch"),
            )
            if p
        )
        size = os.path.getsize(path)
        zip_size, gzip_size = compressed_sizes(path) if compress else (0, 0)
        found.append(BinaryInfo(name, path, key, match.group("suffix") or "", size, zip_size, gzip_size))
    return found


def reduction(reference: int, value: int) -> float:
    return 0.0 if reference == 0 else (reference - value) / reference * 100.0


def build_table(binaries: Sequence[BinaryInfo]) -> str:
    groups: dict[str, list[BinaryInfo]] = {}
    for b in binaries:
        groups.setdefault(b.key, []).append(b)

    mb = 1024 * 1024
    lines = [
        "| Binary | Profile | Size (MB) | Zip (MB) | Gzip -9 (MB) | vs. reference |",
        "| :--- | :--- | ---: | ---: | ---: | ---: |",
    ]
    for key in sorted(groups):
        items = sorted(groups[key], key=lambda b: (b.suffix not in REFERENCE_SUFFIXES, b.suffix))
        reference = next((b for s in REFERENCE_SUFFIXES for b in items if b.suffix == s), None)
        for b in items:
            if reference is None or b is reference:
                delta = "reference" if b is reference else "-"
            else:
                delta = f"{-reduction(reference.size, b.size):+.1f}%"
            lines.append(
                f"| `{b.name}` | {b.suffix or 'default'} | {b.size / mb:.1f} | {b.zip_size / mb:.1f} | "
                f"{b.gzip_size / mb:.1f} | {delta} |"
            )
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Measure Bamboo binary sizes per build profile.")
    parser.add_argument("--bin-dir", default="bin")
    parser.add_argument("--output", help="Write the Markdown report to this file.")
    parser.add_argument("--no-compress", action="store_true", help="Skip compressed size measurement.")
    args = parser.parse_args(argv)

    try:
        binaries = find_binaries(args.bin_dir, compress=not args.no_compress)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if not binaries:
        print(f"ERROR: No Bamboo binaries found in {args.bin_dir}; build them first.", file=sys.stderr)
        return 1

    table = build_table(binaries)
    print(table)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(table + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
