#!/usr/bin/env python3
# BAMBOO: Automated bug bash runner (sprint 0.1.0-beta.1, ALL).
"""Run the automated part of the Bamboo bug bash and triage the findings P0-P3.

Areas (see .prompts/0.1.0-beta.1/PROMPT_ALL_BUG_BASH_AND_TRIAGE.md):
    editor     open every Bamboo project + a new empty project in the editor, check the version header
    export     export the dogfood game with every preset (templates must be installed)
    rendering  each test scene x Forward+/Mobile/Compatibility, windowed: errors, startup stutter, FPS
    physics    tests/bug_bash/scripts/physics_stress.gd (1000 Jolt bodies, raycast, CCD, signals)
    game       dogfood autopilot: windowed FPS run + headless soak (memory leak check)

Severity rules (applied automatically, review before filing issues):
    P0  crash / hang / engine abort
    P1  a functional check fails, a script error or an export failure with templates present
    P2  performance below target (FPS < 60, physics p95 >= 16.6 ms, memory growth)
    P3  warnings, startup shader stutter > 500 ms, VSync enabled but FPS above the display refresh rate
    blocked  the check cannot run on this machine (missing templates / SDK)

Usage:
    python3 misc/scripts/run_bug_bash.py --binary bin/bamboo.macos.editor.arm64 \
        [--areas editor,export,rendering,physics,game] [--soak-seconds 900] [--no-window] \
        [--output-json bug_bash.json] [--report docs/reports/bug_bash_<version>.md]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Sequence

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bamboo_versioning import load_version  # noqa: E402

AREAS = ["editor", "export", "rendering", "physics", "game"]
PROJECTS = ["game_dogfood", "benchmarks", "tests/visual", "tests/bug_bash"]
RENDERERS = ["forward_plus", "mobile", "gl_compatibility"]
RENDER_SCENES = [
    ("tests/visual", "res://scenes/test_pbr_materials.tscn"),
    ("tests/visual", "res://scenes/test_shadow_mapping.tscn"),
    ("tests/visual", "res://scenes/test_alpha_blending.tscn"),
    ("tests/visual", "res://scenes/test_canvas_item_2d.tscn"),
    ("game_dogfood", "res://scenes/main_level.tscn"),
]
EXPORT_PRESETS = ["macOS", "Windows Desktop", "Linux", "Android"]
STUTTER_MS = 500.0
VSYNC_TOLERANCE = 1.1  # FPS may exceed the refresh rate by 10% (timer jitter) before VSync is considered ignored.
TARGET_FPS = 60.0

# Engine messages that are expected in these runs and are not product defects.
BENIGN_ERRORS = [
    re.compile(r"Connection to remote host failed"),  # no debugger / LSP listening
]

_BUGBASH_RE = re.compile(r"^BUGBASH (\{.*\})\s*$", re.M)
_ERROR_RE = re.compile(r"^(?:SCRIPT )?ERROR: (.*)$", re.M)


@dataclass
class Finding:
    area: str
    check: str
    status: str  # pass | P0 | P1 | P2 | P3 | blocked
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    returncode: Optional[int]
    output: str
    timed_out: bool
    seconds: float


def run(cmd: Sequence[str], timeout: float, cwd: str = REPO_ROOT) -> RunResult:
    start = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, errors="replace")
        return RunResult(proc.returncode, proc.stdout + proc.stderr, False, time.time() - start)
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"") + (exc.stderr or b"")
        text = out.decode(errors="replace") if isinstance(out, bytes) else out
        return RunResult(None, text, True, time.time() - start)


def engine_errors(output: str) -> list[str]:
    errors = []
    for message in _ERROR_RE.findall(output):
        if not any(p.search(message) for p in BENIGN_ERRORS):
            errors.append(message.strip())
    return errors


def bugbash_entries(output: str) -> list[dict[str, Any]]:
    return [json.loads(m) for m in _BUGBASH_RE.findall(output)]


def crashed(result: RunResult) -> bool:
    # Negative return codes are signals (SIGSEGV, SIGABRT...) on POSIX.
    return (
        result.timed_out
        or (result.returncode is not None and result.returncode < 0)
        or "CrashHandlerException" in result.output
        or "Program crashed with signal" in result.output
    )


def classify_run(area: str, check: str, result: RunResult, ok_summary: str, details: dict[str, Any]) -> Finding:
    errors = engine_errors(result.output)
    details = dict(details, seconds=round(result.seconds, 1))
    if errors:
        details["errors"] = errors[:10]
    if crashed(result):
        reason = "timeout/hang" if result.timed_out else f"crash (exit {result.returncode})"
        return Finding(area, check, "P0", reason, details)
    if result.returncode != 0:
        return Finding(area, check, "P1", f"exit code {result.returncode}", details)
    if any("SCRIPT ERROR" in line or "Parse Error" in line for line in errors):
        return Finding(area, check, "P1", "script error", details)
    if errors:
        return Finding(area, check, "P3", f"{len(errors)} engine error message(s)", details)
    return Finding(area, check, "pass", ok_summary, details)


# --- Areas -------------------------------------------------------------------------------------


def area_editor(binary: str, expected_version: str) -> list[Finding]:
    findings = []
    result = run([binary, "--headless", "--quit"], 120)
    header = next((line for line in result.output.splitlines() if line.startswith("Bamboo Engine v")), "")
    ok = f"v{expected_version} " in header
    findings.append(
        Finding(
            "editor",
            "version_header",
            "pass" if ok else "P1",
            header or "no startup header",
            {"expected": expected_version},
        )
    )

    for project in PROJECTS:
        result = run([binary, "--headless", "--editor", "--path", project, "--quit"], 300)
        findings.append(classify_run("editor", f"open_project:{project}", result, "opens without errors", {}))

    with tempfile.TemporaryDirectory(prefix="bamboo_bugbash_new_") as tmp:
        with open(os.path.join(tmp, "project.godot"), "w", encoding="utf-8") as f:
            f.write('config_version=5\n\n[application]\n\nconfig/name="Bug Bash New Project"\n')
        result = run([binary, "--headless", "--editor", "--path", tmp, "--quit"], 300)
        finding = classify_run("editor", "open_new_empty_project", result, "new project opens", {})
        if finding.status == "pass" and not os.path.isdir(os.path.join(tmp, ".godot")):
            finding = Finding("editor", "open_new_empty_project", "P1", ".godot folder not created", finding.details)
        findings.append(finding)
    return findings


def _templates_dir(godot_full_config: str) -> str:
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/Bamboo")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("APPDATA", ""), "Bamboo")
    else:
        base = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "bamboo")
    return os.path.join(base, "export_templates", godot_full_config)


def area_export(binary: str, godot_full_config: str) -> list[Finding]:
    findings = []
    templates = _templates_dir(godot_full_config)
    required = {
        "macOS": ["macos.zip"],
        "Windows Desktop": ["windows_release_x86_64.exe"],
        "Linux": ["linux_release.x86_64"],
        "Android": ["android_release.apk", "android_source.zip"],
    }
    run([binary, "--headless", "--path", "game_dogfood", "--import"], 300)
    with tempfile.TemporaryDirectory(prefix="bamboo_bugbash_export_") as out_dir:
        for preset in EXPORT_PRESETS:
            missing = [t for t in required[preset] if not os.path.isfile(os.path.join(templates, t))]
            if missing:
                findings.append(
                    Finding(
                        "export",
                        f"export:{preset}",
                        "blocked",
                        f"templates not installed: {', '.join(missing)}",
                        {"templates_dir": templates},
                    )
                )
                continue
            ext = {"macOS": ".zip", "Windows Desktop": ".exe", "Linux": ".x86_64", "Android": ".apk"}[preset]
            target = os.path.join(out_dir, "dogfood" + ext)
            result = run([binary, "--headless", "--path", "game_dogfood", "--export-release", preset, target], 600)
            finding = classify_run("export", f"export:{preset}", result, "exported", {})
            if finding.status == "pass" and not os.path.isfile(target):
                finding = Finding(
                    "export", f"export:{preset}", "P1", "export reported success but produced no file", finding.details
                )
            elif finding.status == "pass":
                finding.details["size_mib"] = round(os.path.getsize(target) / 1048576, 1)
            findings.append(finding)
    return findings


def area_rendering(binary: str, window: bool) -> list[Finding]:
    if not window:
        return [Finding("rendering", "renderer_matrix", "blocked", "needs a window/GPU (--no-window given)")]
    probe = os.path.join(REPO_ROOT, "tests", "bug_bash", "scripts", "render_probe.gd")
    findings = []
    for project, scene in RENDER_SCENES:
        for method in RENDERERS:
            check = f"{os.path.basename(scene)}:{method}"
            cmd = [
                binary,
                "--path",
                project,
                "--rendering-method",
                method,
                "--resolution",
                "1280x720",
                "-s",
                probe,
                "--",
                f"--scene={scene}",
            ]
            result = run(cmd, 180)
            entries = bugbash_entries(result.output)
            details = entries[0]["details"] if entries else {}
            finding = classify_run("rendering", check, result, "renders", details)
            if finding.status == "pass" and details:
                refresh = float(details.get("refresh_hz") or 0)
                vsync_on = details.get("vsync_mode", 0) != 0
                if details.get("worst_warmup_ms", 0) > STUTTER_MS:
                    finding.status = "P3"
                    finding.summary = f"startup stutter {details['worst_warmup_ms']:.0f} ms (shader compilation)"
                elif vsync_on and refresh > 0 and details.get("steady_fps", 0) > refresh * VSYNC_TOLERANCE:
                    finding.status = "P3"
                    finding.summary = f"VSync on but {details['steady_fps']} FPS on a {refresh:g} Hz display"
                else:
                    finding.summary = (
                        f"{details.get('steady_fps')} FPS, warm-up worst {details.get('worst_warmup_ms')} ms"
                    )
            findings.append(finding)
    return findings


def area_physics(binary: str) -> list[Finding]:
    run([binary, "--headless", "--path", "tests/bug_bash", "--import"], 300)
    result = run([binary, "--headless", "--path", "tests/bug_bash", "-s", "res://scripts/physics_stress.gd"], 600)
    entries = bugbash_entries(result.output)
    if crashed(result) or not entries:
        return [classify_run("physics", "physics_stress", result, "ran", {})]
    findings = []
    for entry in entries:
        status = "pass" if entry["passed"] else ("P2" if entry["check"] == "stack_physics_time" else "P1")
        findings.append(
            Finding("physics", entry["check"], status, "ok" if entry["passed"] else "check failed", entry["details"])
        )
    return findings


def area_game(binary: str, window: bool, soak_seconds: float) -> list[Finding]:
    findings = []
    run([binary, "--headless", "--path", "game_dogfood", "--import"], 300)
    runs: list[tuple[str, list[str], float]] = [("dogfood_fps_windowed", [], 60.0)] if window else []
    runs.append(("dogfood_soak_headless", ["--headless"], soak_seconds))
    for check, extra, seconds in runs:
        cmd = [
            binary,
            *extra,
            "--path",
            "game_dogfood",
            "-s",
            "res://tests/soak_test.gd",
            "--",
            f"--seconds={seconds:g}",
        ]
        result = run(cmd, seconds + 300)
        entries = bugbash_entries(result.output)
        details = entries[0]["details"] if entries else {}
        finding = classify_run("game", check, result, "ok", details)
        if entries and not entries[0]["passed"] and finding.status in ("pass", "P3"):
            finding.status = "P1" if details.get("player_min_y", 0) <= -10 else "P2"
            finding.summary = (
                "player left the level"
                if finding.status == "P1"
                else f"memory growth {details.get('static_mib_per_min')} MiB/min"
            )
        elif finding.status == "pass" and not extra:
            fps = float(details.get("fps_median", 0))
            finding.summary = f"median {fps:.0f} FPS, min {details.get('fps_min')} FPS"
            if fps < TARGET_FPS:
                finding.status, finding.summary = "P2", f"median {fps:.0f} FPS < {TARGET_FPS:.0f}"
        elif finding.status == "pass":
            finding.summary = f"{details.get('seconds')} s, memory {details.get('static_mib_per_min')} MiB/min, {details.get('coins_collected')} coins"
        findings.append(finding)
    return findings


# --- Report ------------------------------------------------------------------------------------

SEVERITY_ORDER = ["P0", "P1", "P2", "P3", "blocked", "pass"]


def triage_counts(findings: Sequence[Finding]) -> dict[str, int]:
    return {s: sum(1 for f in findings if f.status == s) for s in SEVERITY_ORDER}


def render_report(findings: Sequence[Finding], version: str, binary: str, environment: str) -> str:
    counts = triage_counts(findings)
    lines = [
        f"# Bug bash tự động — Bamboo {version}",
        "",
        f"> Sinh bởi `misc/scripts/run_bug_bash.py` · binary `{os.path.relpath(binary, REPO_ROOT)}` · {environment}.",
        "> Mức độ gán tự động theo quy tắc trong script; TL rà lại trước khi tạo issue.",
        "",
        "## Tổng hợp",
        "",
        "| P0 | P1 | P2 | P3 | Blocked | Pass |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        "| " + " | ".join(str(counts[s]) for s in SEVERITY_ORDER) + " |",
        "",
        "## Phát hiện (không tính pass)",
        "",
        "| Mức | Khu vực | Kiểm tra | Mô tả |",
        "| :--- | :--- | :--- | :--- |",
    ]
    issues = sorted((f for f in findings if f.status != "pass"), key=lambda f: SEVERITY_ORDER.index(f.status))
    for f in issues:
        lines.append(f"| {f.status} | {f.area} | `{f.check}` | {f.summary} |")
    if not issues:
        lines.append("| — | — | — | Không có |")
    lines += ["", "## Tất cả kiểm tra", "", "| Khu vực | Kiểm tra | Kết quả | Mô tả |", "| :--- | :--- | :--- | :--- |"]
    for f in findings:
        lines.append(f"| {f.area} | `{f.check}` | {f.status} | {f.summary} |")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the automated Bamboo bug bash.")
    parser.add_argument("--binary", required=True, help="Bamboo editor binary.")
    parser.add_argument("--areas", default=",".join(AREAS))
    parser.add_argument("--soak-seconds", type=float, default=900.0)
    parser.add_argument("--no-window", action="store_true", help="Skip checks that open a window.")
    parser.add_argument("--output-json")
    parser.add_argument("--merge-json", help="Previous --output-json: keep its findings for the areas not run now.")
    parser.add_argument("--report", help="Write the Markdown triage report here.")
    args = parser.parse_args(argv)

    binary = os.path.abspath(args.binary)
    version = load_version()
    areas = [a for a in args.areas.split(",") if a]
    window = not args.no_window
    findings: list[Finding] = []
    for area in areas:
        print(f"== {area}", flush=True)
        if area == "editor":
            new = area_editor(binary, version.bamboo_string)
        elif area == "export":
            new = area_export(binary, version.godot_full_config)
        elif area == "rendering":
            new = area_rendering(binary, window)
        elif area == "physics":
            new = area_physics(binary)
        elif area == "game":
            new = area_game(binary, window, args.soak_seconds)
        else:
            parser.error(f"unknown area '{area}'")
        for f in new:
            print(f"  [{f.status}] {f.check}: {f.summary}", flush=True)
        findings += new

    if args.merge_json:
        with open(args.merge_json, encoding="utf-8") as fh:
            previous = [Finding(**x) for x in json.load(fh)["findings"]]
        findings = [f for f in previous if f.area not in areas] + findings
        findings.sort(key=lambda f: AREAS.index(f.area) if f.area in AREAS else len(AREAS))

    counts = triage_counts(findings)
    print("Triage: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as fh:
            json.dump(
                {"bamboo_version": version.bamboo_string, "findings": [asdict(x) for x in findings]}, fh, indent=2
            )
    if args.report:
        env = f"{sys.platform}, {os.uname().machine}" if hasattr(os, "uname") else sys.platform
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(render_report(findings, version.bamboo_string, binary, env))
    return 1 if counts["P0"] or counts["P1"] else 0


if __name__ == "__main__":
    sys.exit(main())
