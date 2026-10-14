#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for misc/scripts/package_templates.py and misc/scripts/smoke_test.py.

Run: python3 -m unittest tests/python_build/test_package_templates.py
"""

import os
import stat
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "misc", "scripts"))

import package_templates as pkg  # noqa: E402
import smoke_test  # noqa: E402
from bamboo_versioning import load_version  # noqa: E402

VERSION_PY = """short_name = "bamboo"
name = "Bamboo Engine"
major = 4
minor = 8
patch = 0
status = "dev"
module_config = ""
bamboo_major = 0
bamboo_minor = 1
bamboo_patch = 0
bamboo_prerelease = "alpha.1"
bamboo_codename = "Sprout"
"""


def quiet(func, *args, **kwargs):
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()) as err:
        result = func(*args, **kwargs)
    return result, err.getvalue()


class VersionFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.version_file = os.path.join(self.root, "version.py")
        with open(self.version_file, "w", encoding="utf-8") as f:
            f.write(VERSION_PY)
        self.version = load_version(self.version_file)
        self.bin_dir = os.path.join(self.root, "bin")
        os.makedirs(self.bin_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def touch(self, name, content=b"binary"):
        path = os.path.join(self.bin_dir, name)
        with open(path, "wb") as f:
            f.write(content)
        return path


class TestVersionInfo(VersionFixture):
    def test_godot_full_config_and_bamboo_string(self):
        self.assertEqual(self.version.godot_full_config, "4.8.dev")
        self.assertEqual(self.version.bamboo_string, "0.1.0-alpha.1")
        self.assertEqual(self.version.header_prefix, "Bamboo Engine v0.1.0-alpha.1 (Godot 4.8.dev.")

    def test_repo_version_file_is_loadable(self):
        version = load_version()
        self.assertEqual(version.major, 4)  # Godot base must stay 4.x for GDExtension compatibility.
        self.assertTrue(version.bamboo_string)


class TestTemplateNames(unittest.TestCase):
    def test_mapping(self):
        cases = {
            "bamboo.windows.template_debug.x86_64.exe": "windows_debug_x86_64.exe",
            "bamboo.windows.template_release.x86_64.llvm.exe": "windows_release_x86_64.exe",
            "bamboo.windows.template_release.arm64.exe": "windows_release_arm64.exe",
            # Console wrappers are copied next to exported games (debug/export_console_wrapper).
            "bamboo.windows.template_debug.x86_64.console.exe": "windows_debug_x86_64_console.exe",
            "bamboo.windows.template_release.x86_64.llvm.console.exe": "windows_release_x86_64_console.exe",
            "bamboo.linuxbsd.template_debug.x86_64": "linux_debug.x86_64",
            "bamboo.linuxbsd.template_release.arm64.llvm": "linux_release.arm64",
            "bamboo_macos.zip": "macos.zip",
        }
        for filename, expected in cases.items():
            self.assertEqual(pkg.template_name_for(filename), expected, filename)

    def test_non_templates_are_ignored(self):
        for filename in [
            "bamboo.macos.editor.arm64",
            "bamboo.windows.editor.x86_64.exe",
            "bamboo.windows.editor.x86_64.console.exe",
            "Bamboo_v0.1.0-alpha.1_templates.tpz",
        ]:
            self.assertIsNone(pkg.template_name_for(filename), filename)


class TestPackaging(VersionFixture):
    def build(self, *extra):
        output = os.path.join(self.root, "out", "templates.tpz")
        code, err = quiet(
            pkg.main, ["--bin-dir", self.bin_dir, "--output", output, "--version-file", self.version_file, *extra]
        )
        return code, err, output

    def test_creates_valid_tpz(self):
        self.touch("bamboo.linuxbsd.template_debug.x86_64")
        self.touch("bamboo.windows.template_release.x86_64.exe")
        self.touch("bamboo_macos.zip")
        code, _, output = self.build()
        self.assertEqual(code, 0)
        self.assertTrue(zipfile.is_zipfile(output))
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            self.assertTrue(all(n.startswith("templates/") for n in names))
            self.assertIn("templates/linux_debug.x86_64", names)
            self.assertIn("templates/windows_release_x86_64.exe", names)
            self.assertIn("templates/macos.zip", names)
            # version.txt must hold the Godot base version: it is validated by the editor installer
            # (at least 3 dot-separated slices) and used as the export_templates/<version>/ folder name.
            version_txt = archive.read("templates/version.txt").decode().strip()
            self.assertEqual(version_txt, self.version.godot_full_config)
            self.assertGreaterEqual(len(version_txt.split(".")), 3)
            self.assertEqual(archive.read("templates/bamboo_version.txt").decode().strip(), "0.1.0-alpha.1")

    def test_missing_templates_warn_but_do_not_crash(self):
        self.touch("bamboo.linuxbsd.template_debug.x86_64")
        code, err, output = self.build()
        self.assertEqual(code, 0)
        self.assertIn("Missing template 'windows_debug_x86_64.exe'", err)
        self.assertTrue(os.path.isfile(output))

    def test_strict_fails_when_templates_missing(self):
        self.touch("bamboo.linuxbsd.template_debug.x86_64")
        code, err, output = self.build("--strict")
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(output))

    def test_no_binaries_is_a_clear_error(self):
        code, err, output = self.build()
        self.assertEqual(code, 1)
        self.assertIn("No export template binaries found", err)
        self.assertFalse(os.path.exists(output))

    def test_dry_run_writes_nothing(self):
        self.touch("bamboo_macos.zip")
        code, _, output = self.build("--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(output))

    def test_explicit_input_and_missing_source(self):
        src = self.touch("custom_linux_binary")
        code, err, output = self.build("--input", f"linux_release.x86_64={src}", "--input", "macos.zip=/nope.zip")
        self.assertEqual(code, 0)
        self.assertIn("source not found: /nope.zip", err)
        with zipfile.ZipFile(output) as archive:
            self.assertIn("templates/linux_release.x86_64", archive.namelist())
            self.assertNotIn("templates/macos.zip", archive.namelist())

    def test_invalid_input_argument(self):
        code, err, _ = self.build("--input", "no-equals-sign")
        self.assertEqual(code, 2)
        self.assertIn("expected TEMPLATE_NAME=PATH", err)


@unittest.skipIf(sys.platform == "win32", "Fake binary is a POSIX shell script")
class TestSmokeTest(VersionFixture):
    def fake_binary(self, header, exit_code=0):
        script = f"""#!/bin/sh
if [ "$1" = "--version" ]; then
  echo "4.8.dev.bamboo.abcdef123"
  exit 0
fi
echo "{header}"
exit {exit_code}
"""
        path = self.touch("fake_bamboo", script.encode())
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        return path

    def test_passes_with_bamboo_header(self):
        binary = self.fake_binary("Bamboo Engine v0.1.0-alpha.1 (Godot 4.8.dev.bamboo.abcdef123) - https://example")
        results = smoke_test.smoke_test(binary, self.version, timeout=30)
        self.assertTrue(all(r.passed for r in results), results)

    def test_fails_with_godot_header(self):
        binary = self.fake_binary("Godot Engine v4.8.dev.custom_build - https://godotengine.org")
        results = smoke_test.smoke_test(binary, self.version, timeout=30)
        header = next(r for r in results if r.name == "startup header")
        self.assertFalse(header.passed)

    def test_fails_on_non_zero_exit(self):
        binary = self.fake_binary("Bamboo Engine v0.1.0-alpha.1 (Godot 4.8.dev.bamboo)", exit_code=1)
        results = smoke_test.smoke_test(binary, self.version, timeout=30)
        boot = next(r for r in results if r.name == "headless boot")
        self.assertFalse(boot.passed)

    def test_missing_binary(self):
        results = smoke_test.smoke_test(os.path.join(self.root, "missing"), self.version, timeout=30)
        self.assertFalse(results[0].passed)


if __name__ == "__main__":
    unittest.main()
