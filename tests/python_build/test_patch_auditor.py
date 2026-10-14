#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for misc/scripts/audit_bamboo_patches.py, using a throw-away Git repository.

Run: python3 -m unittest tests/python_build/test_patch_auditor.py
"""

import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "misc", "scripts"))

import audit_bamboo_patches as audit  # noqa: E402

UPSTREAM_CPP = "\n".join(["#include <cstdio>", "", "int main() {", "\treturn 0;", "}", ""] + [f"// line {i}" for i in range(40)]) + "\n"


def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)


class AuditRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test")
        self.write("core/main.cpp", UPSTREAM_CPP)
        self.write("thirdparty/lib/lib.c", "int lib(void) { return 1; }\n")
        self.write("docs/readme.md", "docs\n")
        self.write("SConstruct", "env = None\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "upstream")
        self.base = subprocess.run(
            ["git", "-C", self.repo, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, text):
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def run_audit(self, **kwargs):
        return audit.audit(self.repo, self.base, **kwargs)

    def untagged_paths(self, **kwargs):
        return [h.path for r in self.run_audit(**kwargs) for h in r.untagged]


class TestDetection(AuditRepo):
    def test_tagged_change_passes(self):
        self.write("core/main.cpp", UPSTREAM_CPP.replace("\treturn 0;", "\t// BAMBOO: Return a Bamboo exit code.\n\treturn 1;"))
        reports = self.run_audit()
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].untagged, [])

    def test_untagged_change_is_reported(self):
        self.write("core/main.cpp", UPSTREAM_CPP.replace("\treturn 0;", "\treturn 2;"))
        self.assertEqual(self.untagged_paths(), ["core/main.cpp"])

    def test_marker_within_window_covers_hunk(self):
        # A function-level marker a few lines above the change counts.
        self.write("core/main.cpp", UPSTREAM_CPP.replace("int main() {", "// BAMBOO: Patched main.\nint main() {").replace("\treturn 0;", "\treturn 3;"))
        self.assertEqual(self.untagged_paths(), [])

    def test_marker_outside_window_does_not_cover_hunk(self):
        text = UPSTREAM_CPP.replace("#include <cstdio>", "// BAMBOO: Far away marker.\n#include <cstdio>")
        text = text.replace("// line 39", "// line 39 changed")
        self.write("core/main.cpp", text)
        self.assertIn("core/main.cpp", self.untagged_paths(window=5))

    def test_python_marker(self):
        self.write("SConstruct", "# BAMBOO: Bamboo build setting.\nenv = 'bamboo'\n")
        self.assertEqual(self.untagged_paths(), [])

    def test_removed_lines_without_marker_are_reported(self):
        self.write("core/main.cpp", UPSTREAM_CPP.replace("#include <cstdio>\n", ""))
        self.assertEqual(self.untagged_paths(), ["core/main.cpp"])

    def test_thirdparty_and_docs_are_ignored(self):
        self.write("thirdparty/lib/lib.c", "int lib(void) { return 2; }\n")
        self.write("docs/readme.md", "changed docs\n")
        self.assertEqual(self.run_audit(), [])

    def test_new_files(self):
        self.write("core/bamboo_new.cpp", "// BAMBOO: New Bamboo file.\nint bamboo() { return 0; }\n")
        self.write("core/untagged_new.cpp", "int x() { return 0; }\n")
        reports = {r.path: r for r in self.run_audit()}
        self.assertTrue(reports["core/bamboo_new.cpp"].new_file)
        self.assertEqual(reports["core/bamboo_new.cpp"].untagged, [])
        self.assertEqual(len(reports["core/untagged_new.cpp"].untagged), 1)

    def test_committed_only_ignores_working_tree(self):
        self.write("core/main.cpp", UPSTREAM_CPP.replace("\treturn 0;", "\treturn 2;"))
        self.assertEqual(self.untagged_paths(committed_only=True), [])
        git(self.repo, "commit", "-q", "-am", "untagged change")
        self.assertEqual(self.untagged_paths(committed_only=True), ["core/main.cpp"])


class TestScopeAndCli(AuditRepo):
    def test_in_scope(self):
        self.assertTrue(audit.in_scope("core/object/object.cpp"))
        self.assertTrue(audit.in_scope("platform/macos/SCsub"))
        self.assertTrue(audit.in_scope("SConstruct"))
        self.assertFalse(audit.in_scope("thirdparty/zlib/zlib.c"))
        self.assertFalse(audit.in_scope("core/version_generated.gen.h"))
        self.assertFalse(audit.in_scope("docs/Guides.md"))
        self.assertFalse(audit.in_scope("modules/noise/doc_classes/FastNoiseLite.xml"))

    def test_exit_codes_and_report(self):
        self.write("core/main.cpp", UPSTREAM_CPP.replace("\treturn 0;", "\treturn 2;"))
        output = os.path.join(self.repo, "report", "audit.md")
        with redirect_stdout(StringIO()):
            code = audit.main(["--repo", self.repo, "--base", self.base, "--output", output])
        self.assertEqual(code, 1)
        with open(output, encoding="utf-8") as f:
            report = f.read()
        self.assertIn("## Untagged patches", report)
        self.assertIn("`core/main.cpp:4`", report)
        with redirect_stdout(StringIO()):
            self.assertEqual(audit.main(["--repo", self.repo, "--base", self.base, "--no-fail"]), 0)

    def test_clean_tree_exits_zero(self):
        with redirect_stdout(StringIO()) as out:
            code = audit.main(["--repo", self.repo, "--base", self.base])
        self.assertEqual(code, 0)
        self.assertIn("All patches are tagged.", out.getvalue())


if __name__ == "__main__":
    unittest.main()
