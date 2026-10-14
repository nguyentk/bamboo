#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for misc/scripts/check_release_branch.py (feature freeze).

Run: python3 -m unittest tests/python_build/test_release_freeze.py
"""

import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import check_release_branch as crb  # noqa: E402

VERSION_TEMPLATE = """major = 4
minor = 8
patch = 0
bamboo_major = 0
bamboo_minor = 1
bamboo_patch = 0
bamboo_prerelease = "{prerelease}"
bamboo_codename = "Sprout"
"""


def version(prerelease="beta.1", minor=1, major=4):
    return {
        "major": major,
        "bamboo_major": 0,
        "bamboo_minor": minor,
        "bamboo_patch": 0,
        "bamboo_prerelease": prerelease,
    }


class TestRules(unittest.TestCase):
    def test_branch_names(self):
        self.assertEqual(crb.check_branch_name("release/0.1"), ((0, 1), []))
        self.assertEqual(crb.check_branch_name("release/1.12")[0], (1, 12))
        for bad in ("bamboo/main", "release/0.1.0", "release-0.1", "releases/0.1"):
            line, errors = crb.check_branch_name(bad)
            self.assertIsNone(line, bad)
            self.assertTrue(errors)

    def test_prerelease_states(self):
        for ok in ("beta.1", "beta.12", "rc.1", ""):
            self.assertEqual(crb.check_version(version(ok), (0, 1)), [], ok)
        for bad in ("alpha.1", "dev", "beta", "rc1", "beta.1.2"):
            self.assertTrue(crb.check_version(version(bad), (0, 1)), bad)

    def test_version_must_match_branch(self):
        errors = crb.check_version(version("beta.1", minor=2), (0, 1))
        self.assertTrue(any("release/0.1" in e for e in errors))

    def test_godot_base_must_not_change(self):
        self.assertTrue(crb.check_version(version("beta.1", major=0), (0, 1)))

    def test_feature_commits(self):
        subjects = [
            "fix: crash when importing a model",
            "feat: add terrain node",
            "feat(render): new upscaler",
            "feature: something",
            "[Bamboo Feature] Timeline",
            "[Bamboo Fix] Correct the About dialog",
        ]
        self.assertEqual(
            crb.find_feature_commits(subjects),
            ["feat: add terrain node", "feat(render): new upscaler", "feature: something", "[Bamboo Feature] Timeline"],
        )

    def test_repository_version_is_valid_for_its_state(self):
        # The development branch can be alpha/beta/rc/final; this only validates the format and the
        # Godot base version. On a release branch, run check_release_branch.py in CI.
        data = runpy.run_path(os.path.join(REPO_ROOT, "version.py"))
        self.assertEqual(data["major"], 4)
        self.assertRegex(data["bamboo_prerelease"], r"^((alpha|beta|rc)\.\d+)?$")


class TestOnGitRepository(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        self.git("init", "-q")
        # `git init -b` needs Git 2.28+; symbolic-ref works with older versions.
        self.git("symbolic-ref", "HEAD", "refs/heads/bamboo/main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.write_version("alpha.3")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "feat: work before the freeze")
        self.git("checkout", "-q", "-b", "release/0.1")
        self.write_version("beta.1")
        self.git("commit", "-q", "-am", "[Bamboo Release] Bump version to 0.1.0-beta.1")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", self.repo, *args], check=True, capture_output=True)

    def write_version(self, prerelease):
        with open(os.path.join(self.repo, "version.py"), "w") as f:
            f.write(VERSION_TEMPLATE.format(prerelease=prerelease))

    def run_check(self, *extra):
        with redirect_stdout(StringIO()) as out:
            code = crb.main(["--repo", self.repo, *extra])
        return code, out.getvalue()

    def test_valid_release_branch(self):
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn("Bamboo 0.1.0-beta.1", output)

    def test_feature_commit_after_freeze_fails(self):
        with open(os.path.join(self.repo, "new.txt"), "w") as f:
            f.write("x")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "feat: sneak a feature in")
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("feature commit on a frozen branch", output)

    def test_alpha_on_release_branch_fails(self):
        self.write_version("alpha.4")
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("alpha.4", output)

    def test_wrong_branch_name_fails(self):
        self.git("checkout", "-q", "bamboo/main")
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("release/<major>.<minor>", output)


if __name__ == "__main__":
    unittest.main()
