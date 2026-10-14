#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for misc/scripts/check_dev_env.py.

Run: python3 -m unittest discover -s tests/python_build -p "test_*.py"
"""

import json
import os
import sys
import unittest
from collections import namedtuple
from contextlib import redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "misc", "scripts"))

import check_dev_env as env  # noqa: E402

DiskUsage = namedtuple("DiskUsage", "total used free")
GB = 1024**3


def make_runner(responses):
    """Runner returning canned (code, output) by the first two command tokens."""

    def runner(cmd):
        key = " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd[:2]))
        return responses.get(key, (127, "command not found"))

    return runner


def make_which(available):
    return lambda name: available.get(name)


APPLE_CLANG = "Apple clang version 21.0.0 (clang-2100.3.34.2)\nTarget: arm64-apple-darwin25.6.0"
SCONS_OUT = "SCons by Steven Knight et al.:\n\tSCons: v4.11.1.b97f32b9, Wed, 26 Aug 2026, by bdbaddog"

HEALTHY_MAC = {
    "scons --version": (0, SCONS_OUT),
    "xcrun --sdk": (0, "/Applications/Xcode.app/.../MacOSX27.0.sdk"),
    "xcrun clang++": (0, APPLE_CLANG),
    "clang++ --version": (0, APPLE_CLANG),
}
HEALTHY_MAC_WHICH = {"scons": "/usr/local/bin/scons", "clang++": "/usr/bin/clang++"}


class TestPythonCheck(unittest.TestCase):
    def test_supported_python(self):
        self.assertEqual(env.check_python((3, 9, 13)).status, env.OK)

    def test_old_python_fails_with_hint(self):
        result = env.check_python((3, 8, 10))
        self.assertEqual(result.status, env.FAIL)
        self.assertIn("python.org", result.hint)


class TestSconsCheck(unittest.TestCase):
    def test_scons_ok(self):
        result = env.check_scons(make_runner(HEALTHY_MAC), make_which(HEALTHY_MAC_WHICH))
        self.assertEqual(result.status, env.OK)
        self.assertIn("4.11.1", result.detail)

    def test_missing_scons_fails_with_install_command(self):
        result = env.check_scons(make_runner({}), make_which({}))
        self.assertEqual(result.status, env.FAIL)
        self.assertIn("pip install --upgrade scons", result.hint)

    def test_scons_not_in_path_warns(self):
        runner = make_runner({os.path.basename(sys.executable) + " -m": (0, SCONS_OUT)})
        result = env.check_scons(runner, make_which({}))
        self.assertEqual(result.status, env.WARN)
        self.assertIn("PATH", result.hint)

    def test_old_scons_fails(self):
        runner = make_runner({"scons --version": (0, "SCons: v4.2.0.abc")})
        result = env.check_scons(runner, make_which({"scons": "/usr/bin/scons"}))
        self.assertEqual(result.status, env.FAIL)


class TestCompilerCheck(unittest.TestCase):
    def test_healthy_macos(self):
        results = env.check_compiler("Darwin", make_runner(HEALTHY_MAC), make_which(HEALTHY_MAC_WHICH))
        self.assertTrue(all(r.status == env.OK for r in results), results)

    def test_xcode_license_not_accepted(self):
        runner = make_runner(
            {"xcrun --sdk": (69, "You have not agreed to the Xcode license agreements. Please run 'sudo xcodebuild -license'")}
        )
        results = env.check_compiler("Darwin", runner, make_which(HEALTHY_MAC_WHICH))
        self.assertEqual(results[0].status, env.FAIL)
        self.assertIn("xcodebuild -license accept", results[0].hint)

    def test_old_apple_clang_fails(self):
        responses = dict(HEALTHY_MAC)
        responses["xcrun clang++"] = (0, "Apple clang version 15.0.0 (clang-1500.3.9.4)")
        results = env.check_compiler("Darwin", make_runner(responses), make_which(HEALTHY_MAC_WHICH))
        compiler = next(r for r in results if r.name == "compiler")
        self.assertEqual(compiler.status, env.FAIL)
        self.assertIn("Xcode 16", compiler.hint)

    def test_non_apple_clang_in_path_warns(self):
        responses = dict(HEALTHY_MAC)
        responses["clang++ --version"] = (0, "clang version 23.1.3 (https://github.com/llvm/llvm-project.git)")
        which = make_which({"scons": "/usr/local/bin/scons", "clang++": "/usr/local/bin/clang++"})
        results = env.check_compiler("Darwin", make_runner(responses), which)
        path_check = next(r for r in results if r.name == "compiler_path")
        self.assertEqual(path_check.status, env.WARN)
        self.assertIn('PATH="/usr/bin:$PATH"', path_check.hint)

    def test_linux_without_compiler_fails(self):
        results = env.check_compiler("Linux", make_runner({}), make_which({}))
        self.assertEqual(results[0].status, env.FAIL)
        self.assertIn("build-essential", results[0].hint)

    def test_linux_with_gcc(self):
        runner = make_runner({"g++ --version": (0, "g++ (Ubuntu 13.2.0) 13.2.0")})
        results = env.check_compiler("Linux", runner, make_which({"g++": "/usr/bin/g++"}))
        self.assertEqual(results[0].status, env.OK)

    def test_windows_without_compiler_fails(self):
        results = env.check_compiler("Windows", make_runner({}), make_which({}))
        self.assertEqual(results[0].status, env.FAIL)
        self.assertIn("Visual Studio 2022", results[0].hint)

    def test_windows_with_msvc(self):
        results = env.check_compiler("Windows", make_runner({}), make_which({"cl.exe": "C:/VS/cl.exe"}))
        self.assertEqual(results[0].status, env.OK)


class TestDiskCheck(unittest.TestCase):
    def test_enough_space(self):
        result = env.check_disk(".", 20, disk_usage=lambda p: DiskUsage(500 * GB, 400 * GB, 100 * GB))
        self.assertEqual(result.status, env.OK)

    def test_not_enough_space(self):
        result = env.check_disk(".", 20, disk_usage=lambda p: DiskUsage(500 * GB, 495 * GB, 5 * GB))
        self.assertEqual(result.status, env.FAIL)
        self.assertIn("20", result.detail)


class TestOptionalPackages(unittest.TestCase):
    def test_missing_optional_package_only_warns(self):
        results = env.check_optional_packages(["pytest", "PIL"], find_spec=lambda name: None)
        self.assertTrue(all(r.status == env.WARN for r in results))
        self.assertIn("pip install Pillow", results[1].hint)


class TestExitCodeAndOutput(unittest.TestCase):
    def test_exit_code(self):
        ok = env.CheckResult("a", env.OK, "")
        warn = env.CheckResult("b", env.WARN, "")
        fail = env.CheckResult("c", env.FAIL, "")
        self.assertEqual(env.exit_code([ok, warn]), 0)
        self.assertEqual(env.exit_code([ok, fail]), 1)

    def test_healthy_environment_exits_zero(self):
        results = env.run_checks(
            system="Darwin", runner=make_runner(HEALTHY_MAC), which=make_which(HEALTHY_MAC_WHICH), min_disk_gb=0
        )
        self.assertEqual(env.exit_code(results), 0)

    def test_text_output_contains_hint_for_failures(self):
        text = env.format_text([env.CheckResult("scons", env.FAIL, "SCons not found", "pip install scons")], False)
        self.assertIn("[FAIL] scons", text)
        self.assertIn("-> pip install scons", text)
        self.assertIn("NOT ready", text)

    def test_json_flag(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            code = env.main(["--json", "--min-disk-gb", "0"])
        data = json.loads(buffer.getvalue())
        self.assertIn("checks", data)
        self.assertEqual(data["ok"], code == 0)
        self.assertTrue(all({"name", "status", "detail", "hint"} <= set(c) for c in data["checks"]))


if __name__ == "__main__":
    unittest.main()
