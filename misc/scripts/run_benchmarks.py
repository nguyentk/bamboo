#!/usr/bin/env python3
"""Run the Bamboo benchmark suite (`benchmarks/`) and detect performance regressions.

The engine runs `benchmarks/` headless; the GDScript runner writes a JSON report. The report is
validated, optionally merged over several runs (median per metric) and compared with
`benchmarks/baseline.json`: a metric that gets worse by more than its tolerance (DEFAULT_TOLERANCES, or `--tolerance` for all
metrics) is a regression and the script exits with code 1.

Usage:
    python3 misc/scripts/run_benchmarks.py --binary bin/bamboo.macos.editor.arm64
        [--output-json bin/benchmark.json] [--runs 3] [--tolerance 0.10] [--update-baseline]
        [--compare-only results.json]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bamboo_versioning import REPO_ROOT  # noqa: E402

BENCHMARK_DIR = os.path.join(REPO_ROOT, "benchmarks")
BASELINE_PATH = os.path.join(BENCHMARK_DIR, "baseline.json")

REQUIRED_SCENARIOS = [
    "bench_2d_sprites",
    "bench_3d_draw_calls",
    "bench_physics_3d_stack",
    "bench_gdscript_cpu",
    "bench_startup_time",
    "bench_memory_footprint",
]
REQUIRED_FIELDS = ["fps_avg", "frame_time_ms", "physics_time_ms", "memory_bytes"]

# Metric -> True when higher is better.
TRACKED_METRICS: Dict[str, bool] = {
    "fps_avg": True,
    "frame_time_ms": False,
    "frame_time_p95_ms": False,
    "physics_time_ms": False,
    "memory_bytes": False,
    "startup_ms": False,
}
# Ignore relative changes on values this small (pure timer noise), per metric unit.
NOISE_FLOOR = {"frame_time_ms": 0.05, "frame_time_p95_ms": 0.05, "physics_time_ms": 0.05, "startup_ms": 5.0}

# Default allowed degradation per metric. Wall-clock metrics measured on the same binary vary by
# ~6% between runs on a developer machine (more for multi-threaded physics), so a flat 5% would
# report false regressions. Memory is near-deterministic and keeps a tight threshold.
DEFAULT_TOLERANCES = {
    "fps_avg": 0.10,
    "frame_time_ms": 0.10,
    "frame_time_p95_ms": 0.20,
    "physics_time_ms": 0.25,
    "memory_bytes": 0.02,
    "startup_ms": 0.15,
}


def validate_report(report: dict) -> List[str]:
    """Return a list of schema errors (empty when the report is valid)."""
    errors = []
    benchmarks = report.get("benchmarks")
    if not isinstance(benchmarks, list):
        return ["missing 'benchmarks' list"]
    by_name = {b.get("name"): b for b in benchmarks if isinstance(b, dict)}
    for name in REQUIRED_SCENARIOS:
        if name not in by_name:
            errors.append(f"missing scenario '{name}'")
            continue
        for field in REQUIRED_FIELDS:
            value = by_name[name].get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{name}.{field} is not a number")
            elif value < 0:
                errors.append(f"{name}.{field} is negative")
            elif field in ("fps_avg", "frame_time_ms", "memory_bytes") and value == 0:
                errors.append(f"{name}.{field} must be positive")
    return errors


def relative_change(baseline: float, current: float, higher_is_better: bool) -> float:
    """Signed relative change where a positive value means *worse* performance."""
    if baseline == 0:
        return 0.0
    change = (current - baseline) / baseline
    return -change if higher_is_better else change


def find_regressions(
    baseline: dict, current: dict, tolerance: Optional[float] = None
) -> List[Tuple[str, str, float, float, float]]:
    """Return (scenario, metric, baseline, current, worse_ratio) for every regression.

    `tolerance` overrides the per-metric DEFAULT_TOLERANCES when given.
    """
    base_by_name = {b["name"]: b for b in baseline.get("benchmarks", [])}
    regressions = []
    for bench in current.get("benchmarks", []):
        base = base_by_name.get(bench.get("name"))
        if not base:
            continue
        for metric, higher_is_better in TRACKED_METRICS.items():
            if metric not in base or metric not in bench:
                continue
            b, c = float(base[metric]), float(bench[metric])
            if abs(c - b) <= NOISE_FLOOR.get(metric, 0.0):
                continue
            worse = relative_change(b, c, higher_is_better)
            allowed = tolerance if tolerance is not None else DEFAULT_TOLERANCES.get(metric, 0.05)
            if worse > allowed:
                regressions.append((bench["name"], metric, b, c, worse))
    return regressions


def median_report(reports: Sequence[dict]) -> dict:
    """Merge several runs: numeric fields become the median across runs."""
    merged = json.loads(json.dumps(reports[0]))
    for index, bench in enumerate(merged["benchmarks"]):
        for key, value in bench.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values = [r["benchmarks"][index][key] for r in reports]
                bench[key] = statistics.median(values)
    merged["runs"] = len(reports)
    return merged


def run_once(binary: str, timeout: float) -> dict:
    with tempfile.TemporaryDirectory(prefix="bamboo_bench_") as tmp:
        output = os.path.join(tmp, "results.json")
        cmd = [binary, "--headless", "--path", BENCHMARK_DIR, "--", f"--output={output}"]
        start = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        wall_ms = (time.perf_counter() - start) * 1000.0
        if proc.returncode != 0 or not os.path.isfile(output):
            tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-15:])
            raise RuntimeError(f"Benchmark run failed (exit {proc.returncode}):\n{tail}")
        with open(output, encoding="utf-8") as f:
            report = json.load(f)
    report["process_wall_ms"] = wall_ms
    return report


def format_markdown(report: dict) -> str:
    lines = [
        f"Bamboo {report.get('bamboo_version')} (Godot {report.get('godot_version')}), "
        f"renderer {report.get('renderer')}, headless={report.get('headless')}, {report.get('os')}, {report.get('cpu')}",
        "",
        "| Scenario | FPS avg | Frame ms | Frame p95 ms | Physics ms | Memory MB |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for b in report.get("benchmarks", []):
        lines.append(
            f"| {b['name']} | {b.get('fps_avg', 0):.1f} | {b.get('frame_time_ms', 0):.3f} | "
            f"{b.get('frame_time_p95_ms', 0):.3f} | {b.get('physics_time_ms', 0):.3f} | {b.get('memory_bytes', 0) / 1048576:.1f} |"
        )
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Bamboo benchmark suite.")
    parser.add_argument("--binary", help="Bamboo binary (editor or template_debug).")
    parser.add_argument("--compare-only", help="Skip running; validate/compare an existing results JSON.")
    parser.add_argument("--output-json", help="Where to save the merged results.")
    parser.add_argument("--baseline", default=BASELINE_PATH)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument(
        "--tolerance", type=float, default=None, help="Override all per-metric tolerances (e.g. 0.05 = 5%%)."
    )
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args(argv)

    if args.compare_only:
        with open(args.compare_only, encoding="utf-8") as f:
            report = json.load(f)
    elif args.binary:
        try:
            report = median_report([run_once(args.binary, args.timeout) for _ in range(max(1, args.runs))])
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
    else:
        parser.error("--binary or --compare-only is required")

    errors = validate_report(report)
    if errors:
        print("ERROR: Invalid benchmark report:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 2

    print(format_markdown(report))
    if args.output_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.output_json)), exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if args.update_baseline:
        with open(args.baseline, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Baseline updated: {args.baseline}")
        return 0

    if not os.path.isfile(args.baseline):
        print(f"No baseline at {args.baseline}; run with --update-baseline to create one.")
        return 0
    with open(args.baseline, encoding="utf-8") as f:
        baseline = json.load(f)
    regressions = find_regressions(baseline, report, args.tolerance)
    for name, metric, b, c, worse in regressions:
        print(f"REGRESSION {name}.{metric}: {b:.3f} -> {c:.3f} ({worse * 100:.1f}% worse)")
    if regressions:
        return 1
    limit = f"{args.tolerance * 100:.0f}%" if args.tolerance is not None else "per-metric tolerances"
    print(f"No regression beyond {limit} against the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
