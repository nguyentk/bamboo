#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Tests for misc/scripts/release_readiness.py (Go/No-go criteria).

Run: python3 -m unittest tests/python_build/test_release_candidate_readiness.py
The criteria logic is tested on a synthetic repository; the real repository is evaluated for
information only (it is expected to be NO-GO before the GA release).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import release_readiness as rr  # noqa: E402

FULL_EVIDENCE = {key: {"ok": True, "evidence": f"https://example.invalid/{key}"} for key in rr.MANUAL_CRITERIA}


def fake_spctl(ok=True):
    def runner(cmd, capture_output=True, text=True):
        text_out = "accepted\nsource=Notarized Developer ID" if ok else "rejected\nsource=no usable signature"
        return SimpleNamespace(returncode=0 if ok else 3, stdout="", stderr=text_out)

    return runner


class SyntheticRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.write("version.py", 'major = 4\nbamboo_major = 0\nbamboo_minor = 1\nbamboo_patch = 0\nbamboo_prerelease = ""\n')
        self.write("benchmarks/baseline.json", json.dumps({"benchmarks": [{"name": f"b{i}"} for i in range(6)]}))
        for method in ("forward_plus", "mobile", "gl_compatibility"):
            self.write(f"tests/visual/golden/scene_{method}.png", "png")
        self.write("docs/rebase_reports/rebase_rehearsal_w5.md", "report")
        self.write("docs/release_notes/Release_Notes_0.1.0_Sprout.md", "notes")
        self.write("bin/Bamboo_v0.1.0_macOS.dmg", "dmg")
        subprocess.run(["git", "init", "-q", self.root], check=True)
        subprocess.run(["git", "-C", self.root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", self.root, "-c", "user.name=T", "-c", "user.email=t@e", "commit", "-q", "-m", "base"], check=True)
        self.base = subprocess.run(["git", "-C", self.root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, text):
        full = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def evaluate(self, evidence=FULL_EVIDENCE, final=True, notarized=True):
        original = rr.check_patch_tags
        rr.check_patch_tags = lambda root: rr.Criterion("patch_tags", "tags", True, "stubbed")
        try:
            return {c.key: c for c in rr.evaluate(self.root, evidence, final, fake_spctl(notarized))}
        finally:
            rr.check_patch_tags = original


class TestCriteria(SyntheticRepo):
    def test_all_criteria_met_is_go(self):
        criteria = self.evaluate()
        self.assertTrue(all(c.ok for c in criteria.values()), {k: c.detail for k, c in criteria.items() if not c.ok})
        self.assertEqual(len(criteria), 4 + 5 + 2)

    def test_prerelease_version_blocks_final_release(self):
        self.write("version.py", 'major = 4\nbamboo_major = 0\nbamboo_minor = 1\nbamboo_patch = 0\nbamboo_prerelease = "rc.1"\n')
        criteria = self.evaluate()
        self.assertFalse(criteria["stable_version"].ok)
        self.assertEqual(criteria["stable_version"].detail, "0.1.0-rc.1")
        self.assertNotIn("stable_version", self.evaluate(final=False))

    def test_manual_criteria_need_evidence(self):
        evidence = dict(FULL_EVIDENCE, ci_green={"ok": True, "evidence": ""}, zero_p0={"ok": False, "evidence": "2 open"})
        criteria = self.evaluate(evidence=evidence)
        self.assertFalse(criteria["ci_green"].ok)
        self.assertFalse(criteria["zero_p0"].ok)
        self.assertTrue(criteria["dogfood_devices"].ok)

    def test_missing_artifacts(self):
        os.remove(os.path.join(self.root, "docs", "release_notes", "Release_Notes_0.1.0_Sprout.md"))
        shutil.rmtree(os.path.join(self.root, "tests", "visual", "golden"))
        os.remove(os.path.join(self.root, "bin", "Bamboo_v0.1.0_macOS.dmg"))
        criteria = self.evaluate()
        self.assertFalse(criteria["release_notes"].ok)
        self.assertFalse(criteria["golden_images"].ok)
        self.assertFalse(criteria["notarized_dmg"].ok)

    def test_non_notarized_dmg_fails(self):
        self.assertFalse(self.evaluate(notarized=False)["notarized_dmg"].ok)

    def test_small_benchmark_baseline_fails(self):
        self.write("benchmarks/baseline.json", json.dumps({"benchmarks": [{"name": "b1"}]}))
        self.assertFalse(self.evaluate()["benchmark_baseline"].ok)


class TestRealRepository(unittest.TestCase):
    def test_report_runs_on_repository(self):
        with redirect_stdout(StringIO()) as out:
            code = rr.main(["--json"])
        report = json.loads(out.getvalue())
        self.assertEqual(code, 0 if report["go"] else 1)
        keys = {c["key"] for c in report["criteria"]}
        self.assertTrue(set(rr.MANUAL_CRITERIA) <= keys)
        self.assertIn("patch_tags", keys)


if __name__ == "__main__":
    unittest.main()
