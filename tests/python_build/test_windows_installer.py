#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Tests for the Windows installer (misc/dist/windows/bamboo_installer.nsi, misc/scripts/package_windows.sh).

Run: python3 -m unittest tests/python_build/test_windows_installer.py
The NSIS compile test runs when `makensis` is in PATH or MAKENSIS points to it.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NSI = os.path.join(REPO_ROOT, "misc", "dist", "windows", "bamboo_installer.nsi")
SCRIPT = os.path.join(REPO_ROOT, "misc", "scripts", "package_windows.sh")
MAKENSIS = os.environ.get("MAKENSIS") or shutil.which("makensis")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestInstallerScript(unittest.TestCase):
    def setUp(self):
        self.nsi = read(NSI)

    def test_branding_and_attribution(self):
        self.assertIn('!define APP_NAME "Bamboo Engine"', self.nsi)
        self.assertIn('!define APP_EXE "Bamboo.exe"', self.nsi)
        self.assertIn("Bamboo Engine is based on Godot Engine", self.nsi)
        self.assertNotRegex(self.nsi, r'InstallDir\s+"[^"]*Godot')

    def test_per_user_install_without_admin(self):
        self.assertIn("RequestExecutionLevel user", self.nsi)
        self.assertIn("$LOCALAPPDATA", self.nsi)
        self.assertNotIn("HKLM", self.nsi)

    def test_installs_license_and_notices(self):
        for name in ("Bamboo.exe", "Bamboo.console.exe", "LICENSE.txt", "COPYRIGHT.txt"):
            self.assertIn(f'File "${{SOURCE_DIR}}\\{name}"', self.nsi)
            self.assertIn(f'Delete "$INSTDIR\\{name}"', self.nsi)

    def test_uninstaller_registered_and_user_data_kept(self):
        self.assertIn("WriteUninstaller", self.nsi)
        self.assertIn('DeleteRegKey HKCU "${UNINSTALL_KEY}"', self.nsi)
        # Editor settings and projects live in %APPDATA%\\Bamboo and must survive an uninstall.
        self.assertNotIn("$APPDATA", self.nsi)
        self.assertNotRegex(self.nsi, r"RMDir\s+/r")

    def test_requires_64_bit_windows(self):
        self.assertIn("${RunningX64}", self.nsi)

    def test_required_defines_are_passed_by_script(self):
        used = set(re.findall(r"\$\{([A-Z_]+)\}", self.nsi))
        defined = set(re.findall(r"!define\s+([A-Z_]+)", self.nsi)) | {"IfNot", "EndIf", "RunningX64"}
        passed = set(re.findall(r'"-D([A-Z_]+)=', read(SCRIPT)))
        self.assertEqual(used - defined - passed, set())


@unittest.skipUnless(MAKENSIS, "makensis not found (set MAKENSIS)")
class TestInstallerBuild(unittest.TestCase):
    def test_builds_installer_from_staged_binaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "bamboo.windows.editor.x86_64.llvm.exe")
            for path in (exe, exe[: -len(".exe")] + ".console.exe"):
                with open(path, "wb") as f:
                    f.write(b"MZ placeholder")
            out = os.path.join(tmp, "Bamboo_vtest_win64_setup.exe")
            env = dict(os.environ, MAKENSIS=MAKENSIS)
            result = subprocess.run(["sh", SCRIPT, exe, out], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with open(out, "rb") as f:
                data = f.read()
            self.assertEqual(data[:2], b"MZ")
            self.assertIn(b"Nullsoft", data)

    def test_missing_console_wrapper_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = os.path.join(tmp, "bamboo.windows.editor.x86_64.exe")
            with open(exe, "wb") as f:
                f.write(b"MZ")
            result = subprocess.run(["sh", SCRIPT, exe, os.path.join(tmp, "out.exe")], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("console wrapper not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
