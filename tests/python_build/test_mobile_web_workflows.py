#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Static checks of the Bamboo CI workflows (desktop, mobile and web).

Run: python3 -m unittest tests/python_build/test_mobile_web_workflows.py
Uses PyYAML for a full syntax check when it is installed; the other checks need no dependency.
"""

import os
import re
import shutil
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(REPO_ROOT, ".github", "workflows")
BUILD_ACTION = os.path.join(REPO_ROOT, ".github", "actions", "godot-build", "action.yml")

PLATFORM_WORKFLOWS = ["android", "ios", "web", "linux", "macos", "windows"]

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - depends on the environment
    yaml = None


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def workflow(name):
    return read(os.path.join(WORKFLOWS, f"{name}_builds.yml"))


def scons_flags(text):
    match = re.search(r"^  SCONS_FLAGS: >-\n((?:    .*\n)+)", text, re.M)
    return match.group(1).split() if match else []


class TestWorkflowSyntax(unittest.TestCase):
    def test_no_tabs_and_consistent_indentation(self):
        for name in PLATFORM_WORKFLOWS:
            text = workflow(name)
            self.assertNotIn("\t", text, f"{name}: tab character in YAML")
            for number, line in enumerate(text.splitlines(), 1):
                indent = len(line) - len(line.lstrip(" "))
                if line.strip() and not line.lstrip().startswith("#"):
                    self.assertEqual(indent % 2, 0, f"{name}_builds.yml:{number}: odd indentation")

    @unittest.skipIf(yaml is None, "PyYAML not installed")
    def test_yaml_parses(self):
        for name in PLATFORM_WORKFLOWS:
            data = yaml.safe_load(workflow(name))
            self.assertIn("jobs", data, name)

    @unittest.skipIf(yaml is not None or shutil.which("ruby") is None, "PyYAML present or Ruby unavailable")
    def test_yaml_parses_with_ruby(self):
        # Fallback full YAML parse when PyYAML is not installed (Ruby ships with macOS).
        for name in PLATFORM_WORKFLOWS:
            path = os.path.join(WORKFLOWS, f"{name}_builds.yml")
            proc = subprocess.run(
                ["ruby", "-ryaml", "-e", 'abort("no jobs") unless YAML.load_file(ARGV[0]).key?("jobs")', path],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"{name}: {proc.stderr}")


class TestBambooBuildFlags(unittest.TestCase):
    def test_build_name_is_bamboo(self):
        # BUILD_NAME is an environment variable read by methods.get_version_info(), not an SCons option.
        action = read(BUILD_ACTION)
        self.assertIn('export BUILD_NAME="bamboo"', action)
        self.assertNotIn('BUILD_NAME="official"', action)

    def test_update_check_disabled_everywhere(self):
        for name in PLATFORM_WORKFLOWS:
            self.assertIn("engine_update_check=no", scons_flags(workflow(name)), name)

    def test_every_workflow_uses_the_shared_build_action(self):
        for name in PLATFORM_WORKFLOWS:
            self.assertIn("uses: ./.github/actions/godot-build", workflow(name), name)

    def test_build_caches(self):
        for name in PLATFORM_WORKFLOWS:
            text = workflow(name)
            self.assertIn("./.github/actions/godot-cache-restore", text, name)
            self.assertIn("./.github/actions/godot-cache-save", text, name)


class TestMobileAndWeb(unittest.TestCase):
    def test_android_architectures(self):
        text = workflow("android")
        archs = set(re.findall(r"scons-flags: arch=(\w+)", text)) | set(re.findall(r"^\s+arch=(\w+)$", text, re.M))
        self.assertTrue({"arm64", "arm32", "x86_64"} <= archs, archs)

    def test_android_java_17(self):
        self.assertRegex(workflow("android"), r"java-version: 17")

    def test_ios_device_and_simulator(self):
        text = workflow("ios")
        self.assertIn("platform: ios", text)
        self.assertIn("simulator=yes arch=arm64", text)

    def test_web_threads_variants(self):
        text = workflow("web")
        self.assertIn("scons-flags: threads=yes", text)
        self.assertIn("scons-flags: threads=no", text)

    def test_emscripten_toolchain_is_cached(self):
        text = workflow("web")
        self.assertIn("emscripten-core/setup-emsdk", text)
        self.assertIn("actions-cache-folder:", text)
        self.assertNotIn("no-cache: true", text)


class TestDesktopSmokeTest(unittest.TestCase):
    def test_smoke_test_runs_for_editor_builds(self):
        for name in ["linux", "macos", "windows"]:
            text = workflow(name)
            self.assertIn("python misc/scripts/smoke_test.py --binary", text, name)
            self.assertRegex(text, r"- name: Bamboo smoke test\n(?:\s+#.*\n)*\s+if: matrix.target == 'editor'", name)


if __name__ == "__main__":
    unittest.main()
