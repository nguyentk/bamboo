#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for misc/scripts/run_benchmarks.py.

Run: python3 -m unittest tests/python_build/test_benchmark_runner.py
Set BAMBOO_BINARY=bin/bamboo.<platform>.editor.<arch> to also run the suite end-to-end.
"""

import copy
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import run_benchmarks as rb  # noqa: E402


def make_report(fps=100.0, frame=10.0, physics=2.0, memory=100_000_000, startup=300.0):
    benchmarks = []
    for name in rb.REQUIRED_SCENARIOS:
        bench = {
            "name": name,
            "fps_avg": fps,
            "frame_time_ms": frame,
            "frame_time_p95_ms": frame * 1.2,
            "physics_time_ms": physics,
            "memory_bytes": memory,
        }
        if name == "bench_startup_time":
            bench["startup_ms"] = startup
        benchmarks.append(bench)
    return {"bamboo_version": "0.1.0-alpha.1", "benchmarks": benchmarks}


class TestSchema(unittest.TestCase):
    def test_valid_report(self):
        self.assertEqual(rb.validate_report(make_report()), [])

    def test_all_required_scenarios(self):
        self.assertEqual(len(rb.REQUIRED_SCENARIOS), 6)
        report = make_report()
        report["benchmarks"] = report["benchmarks"][:-1]
        errors = rb.validate_report(report)
        self.assertTrue(any("bench_memory_footprint" in e for e in errors))

    def test_numeric_and_positive_fields(self):
        report = make_report()
        report["benchmarks"][0]["fps_avg"] = "fast"
        report["benchmarks"][1]["frame_time_ms"] = -1.0
        report["benchmarks"][2]["memory_bytes"] = 0
        errors = rb.validate_report(report)
        self.assertIn("bench_2d_sprites.fps_avg is not a number", errors)
        self.assertIn("bench_3d_draw_calls.frame_time_ms is negative", errors)
        self.assertIn("bench_physics_3d_stack.memory_bytes must be positive", errors)

    def test_missing_benchmarks_list(self):
        self.assertEqual(rb.validate_report({}), ["missing 'benchmarks' list"])

    def test_committed_baseline_is_valid(self):
        with open(rb.BASELINE_PATH, encoding="utf-8") as f:
            self.assertEqual(rb.validate_report(json.load(f)), [])


class TestRegressionDetection(unittest.TestCase):
    def test_relative_change(self):
        # Lower is better: 10 -> 11 ms is 10% worse.
        self.assertAlmostEqual(rb.relative_change(10.0, 11.0, higher_is_better=False), 0.10)
        # Higher is better: 100 -> 90 FPS is 10% worse; 100 -> 110 is 10% better.
        self.assertAlmostEqual(rb.relative_change(100.0, 90.0, higher_is_better=True), 0.10)
        self.assertAlmostEqual(rb.relative_change(100.0, 110.0, higher_is_better=True), -0.10)
        self.assertEqual(rb.relative_change(0.0, 5.0, higher_is_better=False), 0.0)

    def test_no_regression_on_identical_reports(self):
        self.assertEqual(rb.find_regressions(make_report(), make_report(), 0.05), [])

    def test_regression_beyond_tolerance(self):
        current = make_report(frame=10.6)  # 6% slower
        names = {(r[0], r[1]) for r in rb.find_regressions(make_report(), current, 0.05)}
        self.assertIn(("bench_2d_sprites", "frame_time_ms"), names)

    def test_change_within_tolerance(self):
        self.assertEqual(rb.find_regressions(make_report(), make_report(frame=10.4), 0.05), [])

    def test_improvement_is_not_a_regression(self):
        self.assertEqual(rb.find_regressions(make_report(), make_report(fps=150.0, frame=5.0), 0.05), [])

    def test_fps_drop_detected(self):
        regressions = rb.find_regressions(make_report(fps=100.0), make_report(fps=80.0), 0.05)
        fps = [r for r in regressions if r[1] == "fps_avg"]
        self.assertEqual(len(fps), 6)
        self.assertAlmostEqual(fps[0][4], 0.20)

    def test_noise_floor_ignores_tiny_absolute_changes(self):
        # 0.01 ms -> 0.02 ms is +100% but far below the timer noise floor.
        self.assertEqual(rb.find_regressions(make_report(frame=0.01), make_report(frame=0.02), 0.05), [])

    def test_default_per_metric_tolerances(self):
        # 8% slower frames are within the default 10% frame-time tolerance...
        self.assertEqual(rb.find_regressions(make_report(), make_report(frame=10.8, fps=93.0)), [])
        # ...but 3% more memory exceeds the 2% memory tolerance.
        regressions = rb.find_regressions(make_report(), make_report(memory=103_000_000))
        self.assertTrue(regressions)
        self.assertTrue(all(r[1] == "memory_bytes" for r in regressions))

    def test_startup_regression(self):
        regressions = rb.find_regressions(make_report(startup=300.0), make_report(startup=400.0))
        self.assertEqual([(r[0], r[1]) for r in regressions], [("bench_startup_time", "startup_ms")])


class TestMergeAndCli(unittest.TestCase):
    def test_median_report(self):
        reports = [make_report(fps=f) for f in (90.0, 110.0, 100.0)]
        merged = rb.median_report(reports)
        self.assertEqual(merged["runs"], 3)
        self.assertEqual(merged["benchmarks"][0]["fps_avg"], 100.0)
        self.assertEqual(merged["benchmarks"][0]["name"], "bench_2d_sprites")

    def run_cli(self, *args):
        with redirect_stdout(StringIO()) as out, redirect_stderr(StringIO()) as err:
            code = rb.main(list(args))
        return code, out.getvalue() + err.getvalue()

    def test_cli_compare_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline = os.path.join(tmp, "baseline.json")
            current = os.path.join(tmp, "current.json")
            with open(baseline, "w") as f:
                json.dump(make_report(), f)
            with open(current, "w") as f:
                json.dump(make_report(frame=13.0, fps=70.0), f)
            code, out = self.run_cli("--compare-only", current, "--baseline", baseline)
            self.assertEqual(code, 1)
            self.assertIn("REGRESSION", out)

            with open(current, "w") as f:
                json.dump(make_report(), f)
            code, out = self.run_cli("--compare-only", current, "--baseline", baseline)
            self.assertEqual(code, 0)

    def test_cli_rejects_invalid_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = os.path.join(tmp, "current.json")
            bad = copy.deepcopy(make_report())
            bad["benchmarks"].pop()
            with open(current, "w") as f:
                json.dump(bad, f)
            code, out = self.run_cli("--compare-only", current, "--baseline", os.path.join(tmp, "none.json"))
            self.assertEqual(code, 2)
            self.assertIn("Invalid benchmark report", out)


@unittest.skipUnless(os.environ.get("BAMBOO_BINARY"), "Set BAMBOO_BINARY to run the suite end-to-end")
class TestEndToEnd(unittest.TestCase):
    def test_suite_runs_headless_and_produces_valid_json(self):
        report = rb.run_once(os.environ["BAMBOO_BINARY"], timeout=600)
        self.assertEqual(rb.validate_report(report), [])
        self.assertTrue(report["headless"])


if __name__ == "__main__":
    unittest.main()
