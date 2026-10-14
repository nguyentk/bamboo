#!/usr/bin/env python3
"""Smoke test a Bamboo binary (editor or export template).

Checks:
  1. `<binary> --version` exits with code 0 and prints the Godot base version.
  2. The binary boots a minimal project headless, exits with code 0 and prints the Bamboo startup
     header, e.g. "Bamboo Engine v0.1.0-alpha.1 (Godot 4.8.dev.<build>...".
     - Editor binaries run the project with `--path <project> --quit`.
     - Export templates are built with `disable_path_overrides=yes` (no `--path`/`--main-pack`), so
       the project is packed into `<name>.pck` with an editor binary (PCKPacker) and placed next to
       a copy of the template, exactly like an exported game.

Usage:
    python3 misc/scripts/smoke_test.py --binary bin/bamboo.macos.editor.arm64 [--timeout 120] [--json]
    python3 misc/scripts/smoke_test.py --binary bin/bamboo.macos.template_release.arm64 \
        [--editor-binary bin/bamboo.macos.editor.arm64]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from typing import Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bamboo_versioning import VersionInfo, load_version  # noqa: E402

PROJECT_GODOT = """config_version=5

[application]

config/name="BambooSmokeTest"
run/main_scene="res://main.tscn"
"""

MAIN_TSCN = """[gd_scene format=3]

[node name="Main" type="Node"]
"""

PACK_SCRIPT = """extends SceneTree

func _init() -> void:
	var output: String = OS.get_cmdline_user_args()[0]
	var packer := PCKPacker.new()
	var err := packer.pck_start(output)
	if err == OK:
		for file in ["project.godot", "main.tscn"]:
			err = packer.add_file("res://" + file, ProjectSettings.globalize_path("res://" + file))
			if err != OK:
				break
	if err == OK:
		err = packer.flush()
	quit(0 if err == OK else 1)
"""


@dataclass
class StepResult:
    name: str
    passed: bool
    detail: str


def create_smoke_project(directory: str) -> str:
    with open(os.path.join(directory, "project.godot"), "w", encoding="utf-8") as f:
        f.write(PROJECT_GODOT)
    with open(os.path.join(directory, "main.tscn"), "w", encoding="utf-8") as f:
        f.write(MAIN_TSCN)
    return directory


def is_template(binary: str) -> bool:
    return ".template_" in os.path.basename(binary)


def find_editor_binary(template: str) -> Optional[str]:
    """Find an editor binary for the same platform next to the template (e.g. bin/bamboo.macos.editor.*)."""
    parts = os.path.basename(template).split(".")
    if len(parts) < 2:
        return None
    pattern = os.path.join(os.path.dirname(template) or ".", f"{parts[0]}.{parts[1]}.editor.*")
    candidates = [p for p in sorted(glob.glob(pattern)) if not p.endswith((".zip", ".pck", ".console.exe"))]
    return candidates[0] if candidates else None


def run(cmd: Sequence[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(cmd), capture_output=True, text=True, timeout=timeout)


def check_version_output(output: str, version: VersionInfo) -> StepResult:
    line = output.strip().splitlines()[-1] if output.strip() else ""
    passed = line.startswith(version.godot_full_config + ".")
    return StepResult("--version", passed, f"'{line}' (expected to start with '{version.godot_full_config}.')")


def check_header_output(output: str, version: VersionInfo) -> StepResult:
    expected = version.header_prefix
    for line in output.splitlines():
        if line.startswith(expected):
            return StepResult("startup header", True, line.strip())
    return StepResult("startup header", False, f"No line starting with '{expected}' in output")


def _boot_template(binary: str, editor: str, project_dir: str, timeout: float) -> subprocess.CompletedProcess[str]:
    with open(os.path.join(project_dir, "pack.gd"), "w", encoding="utf-8") as f:
        f.write(PACK_SCRIPT)
    game_dir = os.path.join(project_dir, "exported")
    os.makedirs(game_dir)
    game = os.path.join(game_dir, "smoke_game" + (".exe" if binary.endswith(".exe") else ""))
    pck = os.path.join(game_dir, "smoke_game.pck")
    pack = run([editor, "--headless", "--path", project_dir, "--script", "res://pack.gd", "--", pck], timeout)
    if pack.returncode != 0 or not os.path.isfile(pck):
        raise RuntimeError(f"packing the smoke project with {editor} failed (exit {pack.returncode})")
    shutil.copyfile(binary, game)
    os.chmod(game, os.stat(game).st_mode | stat.S_IEXEC)
    return run([game, "--headless", "--quit"], timeout)


def smoke_test(
    binary: str, version: VersionInfo, timeout: float, editor_binary: Optional[str] = None
) -> list[StepResult]:
    results: list[StepResult] = []
    if not os.path.isfile(binary):
        return [StepResult("binary", False, f"Binary not found: {binary}")]

    try:
        proc = run([binary, "--version"], timeout)
        if proc.returncode != 0:
            results.append(StepResult("--version", False, f"exit code {proc.returncode}"))
        else:
            results.append(check_version_output(proc.stdout, version))
    except subprocess.TimeoutExpired:
        results.append(StepResult("--version", False, f"timed out after {timeout}s"))

    template = is_template(binary)
    if template:
        editor_binary = editor_binary or find_editor_binary(binary)
        if not editor_binary or not os.path.isfile(editor_binary):
            results.append(
                StepResult("headless boot", False, "export template: an editor binary is needed to pack the project")
            )
            return results

    with tempfile.TemporaryDirectory(prefix="bamboo_smoke_") as project_dir:
        create_smoke_project(project_dir)
        try:
            if template:
                assert editor_binary is not None  # Checked above: templates return early without an editor.
                proc = _boot_template(binary, editor_binary, project_dir, timeout)
            else:
                proc = run([binary, "--headless", "--path", project_dir, "--quit"], timeout)
        except subprocess.TimeoutExpired:
            results.append(StepResult("headless boot", False, f"timed out after {timeout}s"))
            return results
        except RuntimeError as e:
            results.append(StepResult("headless boot", False, str(e)))
            return results
        output = proc.stdout + proc.stderr
        results.append(StepResult("headless boot", proc.returncode == 0, f"exit code {proc.returncode}"))
        results.append(check_header_output(output, version))
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test a Bamboo binary.")
    parser.add_argument("--binary", required=True)
    parser.add_argument("--editor-binary", help="Editor binary used to pack the project when testing a template.")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    version = load_version()
    results = smoke_test(args.binary, version, args.timeout, args.editor_binary)
    passed = all(r.passed for r in results)

    if args.json:
        print(json.dumps({"passed": passed, "steps": [asdict(r) for r in results]}, indent=2))
    else:
        for r in results:
            print(f"[{'PASS' if r.passed else 'FAIL'}] {r.name}: {r.detail}")
        print("Smoke test PASSED." if passed else "Smoke test FAILED.")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
