#!/usr/bin/env python3
"""Package Bamboo export templates into an installable `.tpz` file.

The `.tpz` layout follows what the editor expects in
`ExportTemplateManager::_install_file_selected()`:

    templates/version.txt          -> Godot base version, e.g. "4.8.dev"
                                      (also the install folder name: export_templates/4.8.dev/)
    templates/bamboo_version.txt   -> Bamboo version, e.g. "0.1.0-alpha.1"
    templates/windows_debug_x86_64.exe, templates/linux_release.x86_64, templates/macos.zip, ...

Usage:
    python3 misc/scripts/package_templates.py [--bin-dir bin] [--output FILE.tpz] [--dry-run]
                                              [--input TEMPLATE_NAME=PATH ...] [--strict]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bamboo_versioning import REPO_ROOT, VersionInfo, load_version  # noqa: E402

# Expected template file names (as looked up by the export plugins) for the desktop platforms.
EXPECTED_TEMPLATES = [
    "windows_debug_x86_64.exe",
    "windows_release_x86_64.exe",
    "linux_debug.x86_64",
    "linux_release.x86_64",
    "macos.zip",
]

# `bin/<prefix>.windows.template_debug.x86_64[.llvm].exe` -> `windows_debug_x86_64.exe`
# `bin/<prefix>.windows.template_debug.x86_64[.llvm].console.exe` -> `windows_debug_x86_64_console.exe`
# (the console wrapper the exporter copies next to the game, see editor_export_platform_pc.cpp).
_WINDOWS_RE = re.compile(r"^[a-z]+\.windows\.template_(debug|release)\.([a-z0-9_]+)(\.llvm)?(\.console)?\.exe$")
# `bin/<prefix>.linuxbsd.template_debug.x86_64[.llvm]` -> `linux_debug.x86_64`
_LINUX_RE = re.compile(r"^[a-z]+\.linuxbsd\.template_(debug|release)\.([a-z0-9_]+)(\.llvm)?$")
# `bin/<prefix>_macos.zip` (created by `generate_bundle=yes`) -> `macos.zip`
_MACOS_RE = re.compile(r"^[a-z]+_macos\.zip$")


def template_name_for(filename: str) -> Optional[str]:
    """Map a build output file name in `bin/` to its export template name, or None."""
    match = _WINDOWS_RE.match(filename)
    if match:
        console = "_console" if match.group(4) else ""
        return f"windows_{match.group(1)}_{match.group(2)}{console}.exe"
    match = _LINUX_RE.match(filename)
    if match:
        return f"linux_{match.group(1)}.{match.group(2)}"
    if _MACOS_RE.match(filename):
        return "macos.zip"
    return None


def discover_templates(bin_dir: str) -> Dict[str, str]:
    """Return {template_name: source_path} for the templates found in `bin_dir`."""
    found: Dict[str, str] = {}
    if not os.path.isdir(bin_dir):
        return found
    for filename in sorted(os.listdir(bin_dir)):
        name = template_name_for(filename)
        if name and name not in found:
            found[name] = os.path.join(bin_dir, filename)
    return found


def parse_inputs(values: Sequence[str]) -> Dict[str, str]:
    inputs = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --input '{value}', expected TEMPLATE_NAME=PATH")
        name, path = value.split("=", 1)
        inputs[name.strip()] = path.strip()
    return inputs


def plan_package(
    version: VersionInfo, templates: Dict[str, str]
) -> Tuple[List[Tuple[str, Optional[str], Optional[bytes]]], List[str]]:
    """Return (entries, missing). Each entry is (archive_path, source_path, inline_data)."""
    entries: List[Tuple[str, Optional[str], Optional[bytes]]] = [
        ("templates/version.txt", None, (version.godot_full_config + "\n").encode("utf-8")),
        ("templates/bamboo_version.txt", None, (version.bamboo_string + "\n").encode("utf-8")),
    ]
    for name in sorted(templates):
        entries.append((f"templates/{name}", templates[name], None))
    missing = [name for name in EXPECTED_TEMPLATES if name not in templates]
    return entries, missing


def write_package(output: str, entries: Sequence[Tuple[str, Optional[str], Optional[bytes]]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_path, source, data in entries:
            if data is not None:
                archive.writestr(archive_path, data)
            else:
                archive.write(source, archive_path)


def default_output(version: VersionInfo, bin_dir: str) -> str:
    return os.path.join(bin_dir, f"Bamboo_v{version.bamboo_string}_templates.tpz")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Package Bamboo export templates into a .tpz file.")
    parser.add_argument("--bin-dir", default=os.path.join(REPO_ROOT, "bin"))
    parser.add_argument("--output", help="Output .tpz path (default: <bin-dir>/Bamboo_v<version>_templates.tpz)")
    parser.add_argument("--input", action="append", default=[], help="Explicit TEMPLATE_NAME=PATH (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be packaged.")
    parser.add_argument("--strict", action="store_true", help="Fail if any expected desktop template is missing.")
    parser.add_argument("--version-file", default=os.path.join(REPO_ROOT, "version.py"))
    args = parser.parse_args(argv)

    version = load_version(args.version_file)
    try:
        explicit = parse_inputs(args.input)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    templates = discover_templates(args.bin_dir)
    templates.update(explicit)

    for name, path in list(templates.items()):
        if not os.path.isfile(path):
            print(f"WARNING: Template '{name}' source not found: {path}", file=sys.stderr)
            del templates[name]

    entries, missing = plan_package(version, templates)
    output = args.output or default_output(version, args.bin_dir)

    print(f"Bamboo {version.bamboo_string} (Godot base {version.godot_full_config}) -> {output}")
    for archive_path, source, _ in entries:
        print(f"  {archive_path}" + (f"  <- {source}" if source else ""))
    for name in missing:
        print(f"WARNING: Missing template '{name}' (not found in {args.bin_dir}).", file=sys.stderr)

    if not templates:
        print("ERROR: No export template binaries found; nothing to package.", file=sys.stderr)
        return 1
    if args.strict and missing:
        print("ERROR: Missing templates with --strict.", file=sys.stderr)
        return 1
    if args.dry_run:
        print("Dry run: no file written.")
        return 0

    write_package(output, entries)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
