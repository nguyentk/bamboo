#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Tests for misc/scripts/package_release.py and checks of a real release directory.

Run: python3 -m unittest tests/python_build/test_release_artifacts.py
Set BAMBOO_RELEASE_DIR=bin/release/<version> to verify real artifacts (presence, size, checksums).
"""

import os
import sys
import tarfile
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import package_release as pr  # noqa: E402

# Expected size range (MB) of each artifact type.
SIZE_RANGES_MB = {".dmg": (50, 150), ".zip": (50, 400), ".tar.xz": (20, 200), ".tpz": (20, 2000)}


def size_range(name):
    for suffix, bounds in SIZE_RANGES_MB.items():
        if name.endswith(suffix):
            return bounds
    return None


class TestPackaging(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(self.bin)
        self.out = os.path.join(self.tmp.name, "release")

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, name, content=b"data"):
        with open(os.path.join(self.bin, name), "wb") as f:
            f.write(content)

    def test_collects_every_platform_and_checksums(self):
        self.make("Bamboo_v0.1.0_macOS.dmg", b"dmg")
        self.make("bamboo.windows.editor.x86_64.exe", b"exe")
        self.make("bamboo.windows.editor.x86_64.console.exe", b"console")
        self.make("bamboo.windows.editor.dev.x86_64.exe", b"dev build must be skipped")
        self.make("bamboo.linuxbsd.editor.x86_64", b"elf")
        self.make("Bamboo_v0.1.0_templates.tpz", b"tpz")
        produced, missing = pr.collect(self.bin, self.out, "0.1.0")
        self.assertEqual(missing, [])
        self.assertEqual(sorted(produced), sorted(pr.artifact_names("0.1.0").values()))

        with zipfile.ZipFile(os.path.join(self.out, "Bamboo_v0.1.0_win64.zip")) as archive:
            self.assertEqual(
                sorted(archive.namelist()),
                ["bamboo.windows.editor.x86_64.console.exe", "bamboo.windows.editor.x86_64.exe"],
            )
        with tarfile.open(os.path.join(self.out, "Bamboo_v0.1.0_linux.x86_64.tar.xz")) as archive:
            self.assertEqual(archive.getnames(), ["bamboo.linuxbsd.editor.x86_64"])

        sums = pr.read_checksums(os.path.join(self.out, "SHA256SUMS.txt"))
        self.assertEqual(set(sums), set(produced))
        for name, digest in sums.items():
            self.assertEqual(digest, pr.sha256_file(os.path.join(self.out, name)))

    def test_windows_installer_is_optional_and_checksummed(self):
        self.make("Bamboo_v0.1.0_templates.tpz", b"tpz")
        self.make("Bamboo_v0.1.0_win64_setup.exe", b"setup")
        produced, missing = pr.collect(self.bin, self.out, "0.1.0")
        self.assertIn("Bamboo_v0.1.0_win64_setup.exe", produced)
        self.assertEqual(len(missing), 3)
        sums = pr.read_checksums(os.path.join(self.out, "SHA256SUMS.txt"))
        self.assertIn("Bamboo_v0.1.0_win64_setup.exe", sums)

    def test_missing_platforms_are_reported(self):
        self.make("Bamboo_v0.1.0_templates.tpz", b"tpz")
        produced, missing = pr.collect(self.bin, self.out, "0.1.0")
        self.assertEqual(produced, ["Bamboo_v0.1.0_export_templates.tpz"])
        self.assertEqual(len(missing), 3)

    def test_checksum_mismatch_is_detected(self):
        self.make("Bamboo_v0.1.0_templates.tpz", b"tpz")
        pr.collect(self.bin, self.out, "0.1.0")
        with open(os.path.join(self.out, "Bamboo_v0.1.0_export_templates.tpz"), "ab") as f:
            f.write(b"tampered")
        sums = pr.read_checksums(os.path.join(self.out, "SHA256SUMS.txt"))
        self.assertNotEqual(
            sums["Bamboo_v0.1.0_export_templates.tpz"],
            pr.sha256_file(os.path.join(self.out, "Bamboo_v0.1.0_export_templates.tpz")),
        )

    def test_cli_without_artifacts_fails(self):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(pr.main(["--bin-dir", self.bin, "--output-dir", self.out]), 1)


@unittest.skipUnless(os.environ.get("BAMBOO_RELEASE_DIR"), "Set BAMBOO_RELEASE_DIR to check real release artifacts")
class TestRealRelease(unittest.TestCase):
    def setUp(self):
        self.dir = os.environ["BAMBOO_RELEASE_DIR"]
        self.sums = pr.read_checksums(os.path.join(self.dir, "SHA256SUMS.txt"))

    def test_checksums_match(self):
        self.assertTrue(self.sums)
        for name, digest in self.sums.items():
            self.assertEqual(digest, pr.sha256_file(os.path.join(self.dir, name)), name)

    def test_sizes_in_expected_range(self):
        for name in self.sums:
            bounds = size_range(name)
            if bounds:
                size_mb = os.path.getsize(os.path.join(self.dir, name)) / (1024 * 1024)
                self.assertTrue(bounds[0] <= size_mb <= bounds[1], f"{name}: {size_mb:.1f} MB not in {bounds}")


if __name__ == "__main__":
    unittest.main()
