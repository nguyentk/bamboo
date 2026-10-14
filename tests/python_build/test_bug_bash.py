#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Tests for the automated bug bash triage (misc/scripts/run_bug_bash.py).

Run: python3 -m unittest tests/python_build/test_bug_bash.py
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import run_bug_bash as bb  # noqa: E402


def result(code=0, output="", timed_out=False):
    return bb.RunResult(code, output, timed_out, 1.0)


class TestClassification(unittest.TestCase):
    def classify(self, res):
        return bb.classify_run("area", "check", res, "ok", {})

    def test_clean_run_passes(self):
        self.assertEqual(self.classify(result(0, "Bamboo Engine v0.1.0\n")).status, "pass")

    def test_crash_signal_and_hang_are_p0(self):
        self.assertEqual(self.classify(result(-11)).status, "P0")
        self.assertEqual(self.classify(result(None, timed_out=True)).status, "P0")
        self.assertEqual(self.classify(result(1, "Program crashed with signal 11")).status, "P0")

    def test_non_zero_exit_and_script_errors_are_p1(self):
        self.assertEqual(self.classify(result(1)).status, "P1")
        self.assertEqual(self.classify(result(0, "SCRIPT ERROR: Parse Error: x\n")).status, "P1")

    def test_engine_error_messages_are_p3(self):
        finding = self.classify(result(0, "ERROR: Something odd happened.\n"))
        self.assertEqual(finding.status, "P3")
        self.assertEqual(finding.details["errors"], ["Something odd happened."])

    def test_benign_errors_are_ignored(self):
        self.assertEqual(self.classify(result(0, "ERROR: Connection to remote host failed!\n")).status, "pass")

    def test_bugbash_lines_are_parsed(self):
        out = 'noise\nBUGBASH {"area": "physics", "check": "x", "passed": true, "details": {"a": 1}}\nmore\n'
        self.assertEqual(bb.bugbash_entries(out), [{"area": "physics", "check": "x", "passed": True, "details": {"a": 1}}])


class TestRenderingRules(unittest.TestCase):
    def probe(self, **details):
        line = "BUGBASH " + bb.json.dumps({"area": "rendering", "check": "render_probe", "passed": True, "details": details})
        original = bb.run
        bb.run = lambda cmd, timeout, cwd=bb.REPO_ROOT: result(0, line + "\n")
        try:
            return bb.area_rendering("bamboo", True)[0]
        finally:
            bb.run = original

    def test_vsync_ignored_is_p3(self):
        finding = self.probe(worst_warmup_ms=20, steady_fps=120.0, vsync_mode=1, refresh_hz=60.0)
        self.assertEqual(finding.status, "P3")
        self.assertIn("VSync", finding.summary)

    def test_vsync_disabled_high_fps_passes(self):
        self.assertEqual(self.probe(worst_warmup_ms=20, steady_fps=400.0, vsync_mode=0, refresh_hz=60.0).status, "pass")

    def test_startup_stutter_is_p3(self):
        finding = self.probe(worst_warmup_ms=1287.0, steady_fps=60.0, vsync_mode=1, refresh_hz=60.0)
        self.assertEqual(finding.status, "P3")
        self.assertIn("stutter", finding.summary)


class TestReport(unittest.TestCase):
    def test_report_counts_and_orders_by_severity(self):
        findings = [
            bb.Finding("editor", "a", "pass", "ok"),
            bb.Finding("rendering", "b", "P3", "stutter"),
            bb.Finding("export", "c", "blocked", "no templates"),
            bb.Finding("game", "d", "P1", "script error"),
        ]
        counts = bb.triage_counts(findings)
        self.assertEqual(counts, {"P0": 0, "P1": 1, "P2": 0, "P3": 1, "blocked": 1, "pass": 1})
        report = bb.render_report(findings, "0.1.0-beta.1", os.path.join(REPO_ROOT, "bin", "x"), "test")
        self.assertIn("| 0 | 1 | 0 | 1 | 1 | 1 |", report)
        issues = report.split("## Phát hiện")[1].split("## Tất cả")[0]
        self.assertLess(issues.index("`d`"), issues.index("`b`"))
        self.assertLess(issues.index("`b`"), issues.index("`c`"))
        self.assertNotIn("`a`", issues)

    def test_templates_dir_uses_bamboo_data_folder(self):
        path = bb._templates_dir("4.8.dev")
        self.assertIn("Bamboo".lower(), path.lower())
        self.assertTrue(path.endswith(os.path.join("export_templates", "4.8.dev")))


if __name__ == "__main__":
    unittest.main()
