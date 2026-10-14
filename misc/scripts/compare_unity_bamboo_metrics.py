#!/usr/bin/env python3
"""Compare performance metrics of a Unity build and its Bamboo port and write a Markdown report.

Input JSON (one file per engine):
    {
      "engine": "unity" | "bamboo",
      "engine_version": "6000.0.x" | "0.1.0-beta.1",
      "device": "Snapdragon 778G / Android 14",
      "scene": "main_level",
      "frames": 1000,
      "sample": false,                      # true for synthetic data (never for published reports)
      "metrics": {
        "fps_avg": 60.0, "fps_1pct_low": 48.0, "draw_calls": 120,
        "ram_mb": 410.0, "install_size_mb": 85.0, "cold_startup_ms": 2300.0
      }
    }

Usage:
    python3 misc/scripts/compare_unity_bamboo_metrics.py --unity unity.json --bamboo bamboo.json
        [--output docs/reports/unity_vs_bamboo_parity_report.md] [--allow-sample]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Optional, Sequence

# metric -> (label, unit, higher_is_better)
METRICS: dict[str, tuple[str, str, bool]] = {
    "fps_avg": ("FPS average", "FPS", True),
    "fps_1pct_low": ("FPS 1% low", "FPS", True),
    "draw_calls": ("Draw calls / frame", "", False),
    "ram_mb": ("RAM usage", "MB", False),
    "install_size_mb": ("Install size", "MB", False),
    "cold_startup_ms": ("Cold startup", "ms", False),
}


def load_metrics(path: str, expected_engine: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    errors = validate(data, expected_engine)
    if errors:
        raise ValueError(f"{path}: " + "; ".join(errors))
    return data


def validate(data: dict[str, Any], expected_engine: str) -> list[str]:
    errors = []
    if data.get("engine") != expected_engine:
        errors.append(f"engine must be '{expected_engine}'")
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return errors + ["missing 'metrics' object"]
    for key in METRICS:
        value = metrics.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"metrics.{key} must be a number")
        elif value < 0:
            errors.append(f"metrics.{key} must not be negative")
    return errors


def percent_change(unity: float, bamboo: float) -> float:
    """Raw relative difference of Bamboo vs Unity, e.g. FPS gain = (bamboo - unity) / unity * 100."""
    if unity == 0:
        return 0.0
    return (bamboo - unity) / unity * 100.0


def improvement(unity: float, bamboo: float, higher_is_better: bool) -> float:
    """Signed improvement of Bamboo over Unity in percent (positive = Bamboo is better)."""
    change = percent_change(unity, bamboo)
    return change if higher_is_better else -change


def compare(unity: dict[str, Any], bamboo: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, (label, unit, higher_is_better) in METRICS.items():
        u, b = float(unity["metrics"][key]), float(bamboo["metrics"][key])
        gain = improvement(u, b, higher_is_better)
        verdict = "Bamboo better" if gain > 0.5 else ("Unity better" if gain < -0.5 else "Parity")
        rows.append({
            "metric": key,
            "label": label,
            "unit": unit,
            "unity": u,
            "bamboo": b,
            "improvement": gain,
            "verdict": verdict,
        })
    return rows


def fmt_value(value: float, unit: str) -> str:
    text = f"{value:,.0f}" if value >= 100 else f"{value:,.1f}"
    return f"{text} {unit}".strip()


def format_report(unity: dict[str, Any], bamboo: dict[str, Any], rows: Sequence[dict[str, Any]]) -> str:
    sample = unity.get("sample") or bamboo.get("sample")
    lines = ["# Unity vs Bamboo — parity benchmark", ""]
    if sample:
        lines += ["> **SAMPLE DATA** — synthetic numbers used to test the tooling; not a measurement.", ""]
    lines += [
        f"- Unity: {unity.get('engine_version', '?')} · Bamboo: {bamboo.get('engine_version', '?')}",
        f"- Device: {bamboo.get('device') or unity.get('device', '?')} · Scene: {bamboo.get('scene', '?')} · "
        f"Frames: {bamboo.get('frames', '?')}",
        "",
        "| Metric | Unity | Bamboo | Bamboo vs Unity | Verdict |",
        "| :--- | ---: | ---: | ---: | :--- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['label']} | {fmt_value(r['unity'], r['unit'])} | {fmt_value(r['bamboo'], r['unit'])} | "
            f"{r['improvement']:+.1f}% | {r['verdict']} |"
        )
    lines += ["", "Positive percentages mean Bamboo is better (higher FPS, lower draw calls/RAM/size/startup)."]
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compare Unity and Bamboo benchmark metrics.")
    parser.add_argument("--unity", required=True)
    parser.add_argument("--bamboo", required=True)
    parser.add_argument("--output")
    parser.add_argument("--allow-sample", action="store_true", help="Allow synthetic sample data in the output.")
    args = parser.parse_args(argv)

    try:
        unity = load_metrics(args.unity, "unity")
        bamboo = load_metrics(args.bamboo, "bamboo")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if (unity.get("sample") or bamboo.get("sample")) and args.output and not args.allow_sample:
        print("ERROR: input is sample data; refusing to write a report without --allow-sample.", file=sys.stderr)
        return 2

    report = format_report(unity, bamboo, compare(unity, bamboo))
    print(report)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
