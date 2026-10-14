#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for the Bamboo build profiles (profiles/) and misc/scripts/measure_binary_sizes.py.

Run: python3 -m unittest tests/python_build/test_build_profiles.py
"""

import json
import os
import re
import runpy
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROFILES_DIR = os.path.join(REPO_ROOT, "profiles")
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import measure_binary_sizes as mbs  # noqa: E402

PROFILES = ["bamboo_2d", "bamboo_mobile", "bamboo_pc"]
# Options renamed or removed in Godot 4 / Bamboo; profiles must not use them.
DEPRECATED_OPTIONS = {"tools", "bits", "float", "use_lto", "debug_release", "release_debug", "module_mono_enabled_glue"}


def scons_option_names():
    """Option names declared in SConstruct and the platform detect scripts, plus module toggles."""
    names = set()
    sources = [os.path.join(REPO_ROOT, "SConstruct")]
    platform_dir = os.path.join(REPO_ROOT, "platform")
    sources += [os.path.join(platform_dir, p, "detect.py") for p in os.listdir(platform_dir)]
    for path in sources:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                names |= set(re.findall(r'(?:Variable|opts\.Add)\(\s*\(?\[?"([a-z0-9_]+)"', f.read()))
    modules_dir = os.path.join(REPO_ROOT, "modules")
    for module in os.listdir(modules_dir):
        if os.path.isfile(os.path.join(modules_dir, module, "config.py")):
            names.add(f"module_{module}_enabled")
    return names


def load_profile(name):
    return {k: v for k, v in runpy.run_path(os.path.join(PROFILES_DIR, f"{name}.py")).items() if not k.startswith("__")}


class TestProfiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.known_options = scons_option_names()

    def test_all_profiles_exist_and_parse(self):
        for name in PROFILES:
            with self.subTest(name=name):
                self.assertIsInstance(load_profile(name), dict)

    def test_options_are_known_and_not_deprecated(self):
        for name in PROFILES:
            for option in load_profile(name):
                with self.subTest(profile=name, option=option):
                    self.assertNotIn(option, DEPRECATED_OPTIONS)
                    self.assertIn(option, self.known_options)

    def test_boolean_values_are_valid(self):
        for name in PROFILES:
            for option, value in load_profile(name).items():
                if option.startswith(("disable_", "module_")):
                    with self.subTest(profile=name, option=option):
                        self.assertIn(value, ("yes", "no"))

    def test_2d_profile_disables_3d(self):
        profile = load_profile("bamboo_2d")
        self.assertEqual(profile["disable_3d"], "yes")
        self.assertEqual(profile["disable_physics_3d"], "yes")
        self.assertEqual(profile["module_jolt_physics_enabled"], "no")
        # Size optimization is what brings the 2D template past the 25% reduction target.
        self.assertIn(profile["optimize"], ("size", "size_extra"))
        # Complex text shaping and deprecated APIs stay available (they are not dropped for size).
        self.assertNotIn("module_text_server_adv_enabled", profile)
        self.assertNotIn("deprecated", profile)

    def test_mobile_profile_optimizes_for_size(self):
        profile = load_profile("bamboo_mobile")
        self.assertIn(profile["optimize"], ("size", "size_extra"))
        self.assertEqual(profile["module_openxr_enabled"], "no")

    def test_profiles_use_distinct_suffixes(self):
        suffixes = [load_profile(name)["extra_suffix"] for name in PROFILES]
        self.assertEqual(len(set(suffixes)), len(PROFILES))

    def test_gdbuild_files(self):
        for name in PROFILES:
            with self.subTest(name=name):
                with open(os.path.join(PROFILES_DIR, f"{name}.gdbuild"), encoding="utf-8") as f:
                    data = json.load(f)
                self.assertEqual(data["type"], "build_profile")
                self.assertIsInstance(data["disabled_classes"], list)
                for option in data["disabled_build_options"]:
                    self.assertIn(option, self.known_options)
        with open(os.path.join(PROFILES_DIR, "bamboo_2d.gdbuild"), encoding="utf-8") as f:
            self.assertIs(json.load(f)["disabled_build_options"]["disable_3d"], True)


class TestMeasureBinarySizes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, name, size):
        with open(os.path.join(self.bin, name), "wb") as f:
            f.write(os.urandom(size // 2) + b"\0" * (size - size // 2))

    def test_name_parsing(self):
        cases = {
            "bamboo.macos.template_release.arm64": ("", "arm64"),
            "bamboo.macos.template_release.arm64.2d": ("2d", "arm64"),
            "bamboo.windows.template_release.x86_64.llvm.mobile.exe": ("mobile", "x86_64"),
            "bamboo.linuxbsd.editor.dev.x86_64": ("", "x86_64"),
        }
        for name, (suffix, arch) in cases.items():
            match = mbs.BINARY_RE.match(name)
            self.assertIsNotNone(match, name)
            self.assertEqual(match.group("suffix") or "", suffix)
            self.assertEqual(match.group("arch"), arch)
        self.assertIsNone(mbs.BINARY_RE.match("bamboo_macos.zip"))

    def test_reduction_against_reference(self):
        self.make("bamboo.macos.template_release.arm64", 4000)
        self.make("bamboo.macos.template_release.arm64.2d", 3000)
        binaries = mbs.find_binaries(self.bin)
        table = mbs.build_table(binaries)
        self.assertIn("| `bamboo.macos.template_release.arm64` | default |", table)
        self.assertRegex(table, r"`bamboo\.macos\.template_release\.arm64\.2d` \| 2d \|.*\| -25\.0% \|")
        self.assertTrue(all(b.zip_size > 0 and b.gzip_size > 0 for b in binaries))

    def test_pc_profile_is_reference_when_plain_build_missing(self):
        self.make("bamboo.macos.template_release.arm64.pc", 1000)
        self.make("bamboo.macos.template_release.arm64.mobile", 800)
        table = mbs.build_table(mbs.find_binaries(self.bin, compress=False))
        self.assertIn("| pc | 0.0 | 0.0 | 0.0 | reference |", table)
        self.assertIn("-20.0%", table)

    def test_reduction_formula(self):
        self.assertAlmostEqual(mbs.reduction(200, 150), 25.0)
        self.assertEqual(mbs.reduction(0, 10), 0.0)

    def test_errors_when_not_built(self):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()) as err:
            self.assertEqual(mbs.main(["--bin-dir", self.bin]), 1)
            self.assertIn("No Bamboo binaries found", err.getvalue())
            self.assertEqual(mbs.main(["--bin-dir", os.path.join(self.bin, "missing")]), 2)

    def test_writes_report(self):
        self.make("bamboo.macos.template_release.arm64", 2000)
        output = os.path.join(self.bin, "reports", "sizes.md")
        with redirect_stdout(StringIO()):
            self.assertEqual(mbs.main(["--bin-dir", self.bin, "--output", output]), 0)
        with open(output, encoding="utf-8") as f:
            self.assertIn("| Binary | Profile |", f.read())


if __name__ == "__main__":
    unittest.main()
