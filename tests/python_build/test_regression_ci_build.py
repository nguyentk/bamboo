#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Regression tests for CI-only build failures (tests/regression/README.md).

BAMBOO-REG-3: the Android Gradle build parsed every line of version.py as `key = value` and crashed on the
              comment / blank lines of the Bamboo version block.
BAMBOO-REG-4: SCU builds only compile the test folders listed in scu_builders.py, while force_link.gen.h
              references every test file, so a new test folder broke the link of `scu_build=yes` builds.

Run: python3 -m unittest tests/python_build/test_regression_ci_build.py
"""

import ast
import glob
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def gradle_version_name(version_py: str, required: list[str]) -> str:
    """Python port of generateGodotLibraryVersion() in platform/android/java/app/config.gradle."""
    required = list(required)
    values = {}
    for line in version_py.splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().replace('"', "")
        if key in required:
            if value:
                values[key] = value
            required.remove(key)
    return ".".join(values.values()) if not required else "custom_build"


class TestAndroidVersionParsing(unittest.TestCase):
    def setUp(self):
        with open(
            os.path.join(REPO_ROOT, "platform", "android", "java", "app", "config.gradle"), encoding="utf-8"
        ) as f:
            self.gradle = f.read()

    def test_gradle_skips_comments_and_blank_lines(self):
        self.assertIn('line.trim().startsWith("#")', self.gradle)
        self.assertIn("line.trim().isEmpty()", self.gradle)
        self.assertIn('!line.contains("=")', self.gradle)

    def test_version_py_has_lines_the_old_parser_could_not_handle(self):
        # Keeps the regression meaningful: the Bamboo block has comments and blank lines.
        with open(os.path.join(REPO_ROOT, "version.py"), encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertTrue(any("=" not in line for line in lines))

    def test_android_library_version_is_the_godot_base_version(self):
        with open(os.path.join(REPO_ROOT, "version.py"), encoding="utf-8") as f:
            name = gradle_version_name(f.read(), ["major", "minor", "patch", "status", "module_config"])
        self.assertEqual(name, "4.8.0.dev")


class TestScuTestFolders(unittest.TestCase):
    def test_every_test_folder_with_sources_is_in_the_scu_list(self):
        with open(os.path.join(REPO_ROOT, "scu_builders.py"), encoding="utf-8") as f:
            source = f.read()
        match = re.search(r'process_folder\(\s*\[\s*"tests",(.*?)\]', source, re.S)
        self.assertIsNotNone(match)
        listed = set(ast.literal_eval("[" + match.group(1) + "]"))
        tests_dir = os.path.join(REPO_ROOT, "tests")
        folders = {
            "/" + os.path.relpath(os.path.dirname(path), tests_dir).replace(os.sep, "/")
            for path in glob.glob(os.path.join(tests_dir, "*", "**", "*.cpp"), recursive=True)
        }
        self.assertEqual(sorted(folders - listed), [], "add these folders to the tests SCU list in scu_builders.py")


if __name__ == "__main__":
    unittest.main()
