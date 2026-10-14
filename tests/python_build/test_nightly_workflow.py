#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Checks of the nightly benchmark + golden-image workflow and its per-runner baselines.

Run: python3 -m unittest tests/python_build/test_nightly_workflow.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NIGHTLY = os.path.join(REPO_ROOT, ".github", "workflows", "bamboo_nightly.yml")
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import capture_golden_images as cgi  # noqa: E402


def load_workflow():
    """Parse the workflow with PyYAML, or with Ruby (ships with macOS) as a fallback."""
    try:
        import yaml  # type: ignore

        with open(NIGHTLY, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        if shutil.which("ruby") is None:
            raise unittest.SkipTest("Neither PyYAML nor Ruby is available")
        out = subprocess.run(
            ["ruby", "-ryaml", "-rjson", "-e", "puts JSON.generate(YAML.load_file(ARGV[0]))", NIGHTLY],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return json.loads(out)


class TestNightlyWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_workflow()
        with open(NIGHTLY, encoding="utf-8") as f:
            cls.text = f.read()

    def test_triggers(self):
        # Ruby/PyYAML parse the `on` key as boolean true.
        triggers = self.data.get("on") or self.data.get(True) or self.data.get("true")
        self.assertIn("schedule", triggers)
        self.assertIn("workflow_dispatch", triggers)

    def test_linux_and_macos_runners(self):
        runners = {m["runner-id"]: m for m in self.data["jobs"]["nightly"]["strategy"]["matrix"]["include"]}
        self.assertEqual(set(runners), {"linux", "macos"})
        self.assertIn("xvfb-run", runners["linux"]["gpu-wrapper"])
        self.assertIn("vulkan=no", runners["macos"]["scons-flags"])

    def test_runs_benchmarks_and_golden_images_with_per_runner_baselines(self):
        self.assertIn("misc/scripts/run_benchmarks.py", self.text)
        self.assertIn("misc/scripts/capture_golden_images.py", self.text)
        self.assertIn("benchmarks/baselines/${{ matrix.runner-id }}.json", self.text)
        self.assertIn("tests/visual/golden/${{ matrix.runner-id }}", self.text)

    def test_bamboo_build_flags(self):
        self.assertIn("engine_update_check=no", self.text)
        self.assertIn("uses: ./.github/actions/godot-build", self.text)

    def test_results_uploaded_even_on_failure(self):
        steps = self.data["jobs"]["nightly"]["steps"]
        upload = [s for s in steps if s.get("uses") == "./.github/actions/upload-artifact"]
        self.assertEqual(len(upload), 1)
        self.assertEqual(upload[0]["if"], "always()")


class TestGoldenDirOption(unittest.TestCase):
    def test_missing_golden_in_custom_dir_fails_and_update_writes_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = os.path.join(tmp, "render.png")
            from PIL import Image

            Image.new("RGB", (4, 4), (10, 20, 30)).save(fake)

            def fake_render(binary, scene, method, frame, output, timeout):
                os.makedirs(os.path.dirname(output), exist_ok=True)
                shutil.copyfile(fake, output)
                return None

            original = cgi.render
            cgi.render = fake_render
            try:
                golden = os.path.join(tmp, "golden", "linux")
                output = os.path.join(tmp, "out")
                args = [
                    "--binary",
                    "x",
                    "--scenes",
                    "test_pbr_materials",
                    "--methods",
                    "forward_plus",
                    "--golden-dir",
                    golden,
                    "--output-dir",
                    output,
                ]
                self.assertEqual(cgi.main(args), 1)
                self.assertEqual(cgi.main(args + ["--update-golden"]), 0)
                self.assertTrue(os.path.isfile(os.path.join(golden, "test_pbr_materials_forward_plus.png")))
                self.assertEqual(cgi.main(args), 0)
            finally:
                cgi.render = original


if __name__ == "__main__":
    unittest.main()
