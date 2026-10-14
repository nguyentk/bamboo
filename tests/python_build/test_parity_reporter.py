#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for misc/scripts/compare_unity_bamboo_metrics.py.

Run: python3 -m unittest tests/python_build/test_parity_reporter.py
"""

import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import compare_unity_bamboo_metrics as cmp  # noqa: E402

UNITY_SAMPLE = os.path.join(REPO_ROOT, "tests", "data", "unity_benchmark_sample.json")
BAMBOO_SAMPLE = os.path.join(REPO_ROOT, "tests", "data", "bamboo_benchmark_sample.json")


def quiet(func, *args):
    with redirect_stdout(StringIO()) as out, redirect_stderr(StringIO()) as err:
        code = func(*args)
    return code, out.getvalue(), err.getvalue()


class TestParsing(unittest.TestCase):
    def test_load_samples(self):
        self.assertEqual(cmp.load_metrics(UNITY_SAMPLE, "unity")["engine"], "unity")
        self.assertEqual(cmp.load_metrics(BAMBOO_SAMPLE, "bamboo")["metrics"]["fps_avg"], 60.0)

    def test_wrong_engine_and_missing_metric(self):
        errors = cmp.validate({"engine": "bamboo", "metrics": {"fps_avg": 60}}, "unity")
        self.assertIn("engine must be 'unity'", errors)
        self.assertIn("metrics.draw_calls must be a number", errors)
        self.assertIn(
            "metrics.fps_avg must not be negative",
            cmp.validate({"engine": "unity", "metrics": {**{k: 1 for k in cmp.METRICS}, "fps_avg": -1}}, "unity"),
        )


class TestFormulas(unittest.TestCase):
    def test_percent_change_matches_spec(self):
        # perf_gain = (bamboo_fps - unity_fps) / unity_fps * 100
        self.assertAlmostEqual(cmp.percent_change(50.0, 60.0), 20.0)
        # size_reduction = (unity_size - bamboo_size) / unity_size * 100
        self.assertAlmostEqual(cmp.improvement(100.0, 60.0, higher_is_better=False), 40.0)
        self.assertEqual(cmp.percent_change(0.0, 10.0), 0.0)

    def test_improvement_sign(self):
        self.assertAlmostEqual(cmp.improvement(40.0, 38.0, higher_is_better=True), -5.0)
        self.assertAlmostEqual(cmp.improvement(500.0, 400.0, higher_is_better=False), 20.0)

    def test_verdicts(self):
        rows = {
            r["metric"]: r
            for r in cmp.compare(cmp.load_metrics(UNITY_SAMPLE, "unity"), cmp.load_metrics(BAMBOO_SAMPLE, "bamboo"))
        }
        self.assertEqual(rows["fps_avg"]["verdict"], "Bamboo better")
        self.assertEqual(rows["fps_1pct_low"]["verdict"], "Unity better")
        self.assertEqual(rows["cold_startup_ms"]["verdict"], "Parity")
        self.assertAlmostEqual(rows["install_size_mb"]["improvement"], 40.0)


class TestReport(unittest.TestCase):
    def test_markdown_table(self):
        unity, bamboo = cmp.load_metrics(UNITY_SAMPLE, "unity"), cmp.load_metrics(BAMBOO_SAMPLE, "bamboo")
        report = cmp.format_report(unity, bamboo, cmp.compare(unity, bamboo))
        self.assertIn("| Metric | Unity | Bamboo | Bamboo vs Unity | Verdict |", report)
        self.assertIn("| FPS average | 50.0 FPS | 60.0 FPS | +20.0% | Bamboo better |", report)
        self.assertIn("| Install size | 100 MB | 60.0 MB | +40.0% | Bamboo better |", report)
        self.assertIn("SAMPLE DATA", report)
        self.assertEqual(
            len([row for row in report.splitlines() if row.startswith("| ") and "---" not in row]), 1 + len(cmp.METRICS)
        )

    def test_refuses_to_publish_sample_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "report.md")
            code, _, err = quiet(cmp.main, ["--unity", UNITY_SAMPLE, "--bamboo", BAMBOO_SAMPLE, "--output", output])
            self.assertEqual(code, 2)
            self.assertIn("sample data", err)
            self.assertFalse(os.path.exists(output))
            code, _, _ = quiet(
                cmp.main, ["--unity", UNITY_SAMPLE, "--bamboo", BAMBOO_SAMPLE, "--output", output, "--allow-sample"]
            )
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(output))

    def test_real_data_is_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {}
            for engine, source in (("unity", UNITY_SAMPLE), ("bamboo", BAMBOO_SAMPLE)):
                with open(source) as f:
                    data = json.load(f)
                data["sample"] = False
                paths[engine] = os.path.join(tmp, f"{engine}.json")
                with open(paths[engine], "w") as f:
                    json.dump(data, f)
            output = os.path.join(tmp, "report.md")
            code, _, _ = quiet(cmp.main, ["--unity", paths["unity"], "--bamboo", paths["bamboo"], "--output", output])
            self.assertEqual(code, 0)
            with open(output) as f:
                self.assertNotIn("SAMPLE DATA", f.read())

    def test_invalid_input(self):
        code, _, err = quiet(cmp.main, ["--unity", BAMBOO_SAMPLE, "--bamboo", BAMBOO_SAMPLE])
        self.assertEqual(code, 2)
        self.assertIn("engine must be 'unity'", err)


if __name__ == "__main__":
    unittest.main()
