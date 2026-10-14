#!/usr/bin/env python3
"""Check that a developer machine is ready to build Bamboo Engine.

Usage:
    python3 misc/scripts/check_dev_env.py [--json] [--min-disk-gb N]

Exit code is 0 when no check failed (warnings are allowed), 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional, Sequence

MIN_PYTHON = (3, 9)
MIN_SCONS = (4, 4)
MIN_APPLE_CLANG = 16
DEFAULT_MIN_DISK_GB = 20
OPTIONAL_PYTHON_PACKAGES = ["pytest", "PIL"]

OK = "ok"
WARN = "warn"
FAIL = "fail"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    hint: str = ""


# A runner takes a command and returns (exit_code, combined_output).
Runner = Callable[[Sequence[str]], tuple[int, str]]
Which = Callable[[str], Optional[str]]


def default_runner(cmd: Sequence[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(list(cmd), capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 127, str(e)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def parse_version(text: str) -> Optional[tuple[int, ...]]:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def check_python(version_info: Sequence[int] = tuple(sys.version_info[:3])) -> CheckResult:
    current = ".".join(str(v) for v in version_info)
    if tuple(version_info[:2]) >= MIN_PYTHON:
        return CheckResult("python", OK, f"Python {current}")
    return CheckResult(
        "python",
        FAIL,
        f"Python {current} is older than {MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
        "Install Python 3.9 or newer from https://www.python.org/downloads/",
    )


def check_scons(runner: Runner, which: Which) -> CheckResult:
    install_hint = "python3 -m pip install --upgrade scons"
    scons_path = which("scons")
    if scons_path:
        code, out = runner([scons_path, "--version"])
    else:
        code, out = runner([sys.executable, "-m", "SCons", "--version"])
        if code == 0:
            return CheckResult(
                "scons",
                WARN,
                "SCons is installed but `scons` is not in PATH",
                "Add the pip scripts directory to PATH (e.g. ~/Library/Python/3.9/bin on macOS)",
            )
        return CheckResult("scons", FAIL, "SCons not found", install_hint)

    version = parse_version(re.sub(r"^.*?SCons: v", "", out, flags=re.S)) if code == 0 else None
    if version is None:
        return CheckResult("scons", FAIL, f"Could not read SCons version from: {out[:120]}", install_hint)
    version_str = ".".join(str(v) for v in version)
    if version[:2] < MIN_SCONS:
        return CheckResult(
            "scons", FAIL, f"SCons {version_str} is older than {MIN_SCONS[0]}.{MIN_SCONS[1]}", install_hint
        )
    return CheckResult("scons", OK, f"SCons {version_str}")


def _check_compiler_macos(runner: Runner, which: Which) -> list[CheckResult]:
    results = []
    code, out = runner(["xcrun", "--sdk", "macosx", "--show-sdk-path"])
    if code != 0:
        if "license" in out.lower():
            results.append(
                CheckResult(
                    "xcode",
                    FAIL,
                    "The Xcode license has not been accepted",
                    "Run once in a terminal: sudo xcodebuild -license accept",
                )
            )
        else:
            results.append(
                CheckResult(
                    "xcode",
                    FAIL,
                    "No macOS SDK found (xcrun failed)",
                    "Install Xcode 16+ and run: sudo xcode-select -s /Applications/Xcode.app/Contents/Developer",
                )
            )
        return results
    results.append(CheckResult("xcode", OK, f"macOS SDK: {out.splitlines()[-1]}"))

    code, out = runner(["xcrun", "clang++", "--version"])
    match = re.search(r"Apple clang version (\d+)", out)
    if code != 0 or not match:
        results.append(CheckResult("compiler", FAIL, "Apple Clang not found via xcrun", "Install Xcode 16 or newer"))
        return results
    major = int(match.group(1))
    if major < MIN_APPLE_CLANG:
        results.append(
            CheckResult(
                "compiler",
                FAIL,
                f"Apple Clang {major} is older than {MIN_APPLE_CLANG} (Xcode 16)",
                "Install Xcode 16 or newer and select it with xcode-select",
            )
        )
    else:
        results.append(CheckResult("compiler", OK, f"Apple Clang {major}"))

    # SCons calls `clang++` from PATH. A non-Apple clang (e.g. llvm-mingw installed for Windows
    # cross-compilation) fails at link time with `___isPlatformVersionAtLeast` undefined.
    path_clang = which("clang++")
    if path_clang:
        code, out = runner([path_clang, "--version"])
        if code == 0 and "Apple clang" not in out:
            results.append(
                CheckResult(
                    "compiler_path",
                    WARN,
                    f"`clang++` in PATH is not Apple Clang ({path_clang})",
                    'Build macOS with Apple Clang first in PATH: PATH="/usr/bin:$PATH" scons platform=macos ...',
                )
            )
        else:
            results.append(CheckResult("compiler_path", OK, f"`clang++` in PATH is Apple Clang ({path_clang})"))
    return results


def check_compiler(system: str, runner: Runner, which: Which) -> list[CheckResult]:
    if system == "Darwin":
        return _check_compiler_macos(runner, which)
    if system == "Windows":
        if which("cl") or which("cl.exe"):
            return [CheckResult("compiler", OK, "MSVC (cl.exe) found")]
        if which("x86_64-w64-mingw32-gcc") or which("x86_64-w64-mingw32-clang"):
            return [CheckResult("compiler", OK, "MinGW-w64 compiler found")]
        return [
            CheckResult(
                "compiler",
                FAIL,
                "No C++ compiler found (cl.exe or MinGW-w64)",
                'Install Visual Studio 2022 with "Desktop development with C++" and run from a Developer Command Prompt',
            )
        ]
    for compiler in ("g++", "clang++"):
        path = which(compiler)
        if path:
            code, out = runner([path, "--version"])
            first_line = out.splitlines()[0] if out else compiler
            return [CheckResult("compiler", OK, first_line)]
    return [
        CheckResult(
            "compiler",
            FAIL,
            "No C++ compiler found (g++ or clang++)",
            "sudo apt install build-essential  (Debian/Ubuntu) or install clang",
        )
    ]


def check_disk(path: str, min_gb: float, disk_usage: Callable[..., Any] = shutil.disk_usage) -> CheckResult:
    free_gb = disk_usage(path).free / (1024**3)
    if free_gb >= min_gb:
        return CheckResult("disk", OK, f"{free_gb:.1f} GB free")
    return CheckResult(
        "disk",
        FAIL,
        f"Only {free_gb:.1f} GB free, at least {min_gb:g} GB required for build artifacts",
        "Free disk space or clean old build objects in bin/obj/",
    )


def check_optional_packages(
    packages: Sequence[str] = OPTIONAL_PYTHON_PACKAGES, find_spec: Optional[Callable[..., Any]] = None
) -> list[CheckResult]:
    if find_spec is None:
        import importlib.util

        find_spec = importlib.util.find_spec
    pip_names = {"PIL": "Pillow"}
    results = []
    for package in packages:
        pip_name = pip_names.get(package, package)
        if find_spec(package) is not None:
            results.append(CheckResult(f"package:{pip_name}", OK, f"{pip_name} installed"))
        else:
            results.append(
                CheckResult(
                    f"package:{pip_name}",
                    WARN,
                    f"{pip_name} not installed (optional)",
                    f"python3 -m pip install {pip_name}",
                )
            )
    return results


def run_checks(
    system: Optional[str] = None,
    runner: Runner = default_runner,
    which: Which = shutil.which,
    repo_path: str = ".",
    min_disk_gb: float = DEFAULT_MIN_DISK_GB,
) -> list[CheckResult]:
    system = system or platform.system()
    results = [check_python(), check_scons(runner, which)]
    results += check_compiler(system, runner, which)
    results.append(check_disk(repo_path, min_disk_gb))
    results += check_optional_packages()
    return results


def exit_code(results: Sequence[CheckResult]) -> int:
    return 1 if any(r.status == FAIL for r in results) else 0


def format_text(results: Sequence[CheckResult], color: bool) -> str:
    colors = {OK: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m"}
    labels = {OK: "OK  ", WARN: "WARN", FAIL: "FAIL"}
    reset = "\033[0m"
    lines = []
    for r in results:
        label = labels[r.status]
        if color:
            label = colors[r.status] + label + reset
        lines.append(f"[{label}] {r.name}: {r.detail}")
        if r.hint and r.status != OK:
            lines.append(f"       -> {r.hint}")
    summary = "Environment is ready to build Bamboo Engine." if exit_code(results) == 0 else "Environment is NOT ready."
    if color:
        summary = (colors[OK] if exit_code(results) == 0 else colors[FAIL]) + summary + reset
    lines.append(summary)
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Bamboo Engine build environment.")
    parser.add_argument("--json", action="store_true", help="Print results as JSON (for CI).")
    parser.add_argument("--min-disk-gb", type=float, default=DEFAULT_MIN_DISK_GB)
    args = parser.parse_args(argv)

    repo_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results = run_checks(repo_path=repo_path, min_disk_gb=args.min_disk_gb)
    code = exit_code(results)
    if args.json:
        print(json.dumps({"ok": code == 0, "checks": [asdict(r) for r in results]}, indent=2))
    else:
        use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
        print(format_text(results, use_color))
    return code


if __name__ == "__main__":
    sys.exit(main())
