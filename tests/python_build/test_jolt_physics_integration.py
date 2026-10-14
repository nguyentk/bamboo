#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""End-to-end checks of the 3D physics engine selection (Jolt Physics default).

Run: BAMBOO_BINARY=bin/bamboo.macos.editor.arm64 python3 -m unittest tests/python_build/test_jolt_physics_integration.py
Skipped when BAMBOO_BINARY is not set.
"""

import os
import re
import subprocess
import tempfile
import unittest

BINARY = os.environ.get("BAMBOO_BINARY")

FALL_SCRIPT = """extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var body := RigidBody3D.new()
	var shape := CollisionShape3D.new()
	shape.shape = BoxShape3D.new()
	body.add_child(shape)
	body.position = Vector3(0, 10, 0)
	root.add_child(body)
	for i in 60:
		await physics_frame
	print("ENGINE=", ProjectSettings.get_setting("physics/3d/physics_engine"))
	print("FALL_Y=", body.position.y)
	quit(0)
"""


def write_project(directory, physics_engine=None):
    lines = ["config_version=5", "", "[application]", "", 'config/name="JoltCheck"', ""]
    if physics_engine is not None:
        lines += ["[physics]", "", f'3d/physics_engine="{physics_engine}"', ""]
    with open(os.path.join(directory, "project.godot"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    with open(os.path.join(directory, "fall.gd"), "w", encoding="utf-8") as f:
        f.write(FALL_SCRIPT)


def run_fall(directory):
    proc = subprocess.run(
        [BINARY, "--headless", "--path", directory, "-s", "res://fall.gd"], capture_output=True, text=True, timeout=120
    )
    return proc.returncode, proc.stdout + proc.stderr


@unittest.skipUnless(BINARY, "Set BAMBOO_BINARY to run engine integration tests")
class TestJoltIntegration(unittest.TestCase):
    def test_rigid_body_falls_with_jolt(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(tmp, "Jolt Physics")
            code, output = run_fall(tmp)
            self.assertEqual(code, 0, output)
            self.assertIn("ENGINE=Jolt Physics", output)
            fall_y = float(re.search(r"FALL_Y=([-\d.e]+)", output).group(1))
            # One second of free fall at 9.8 m/s^2 drops the body by ~4.9 m.
            self.assertLess(fall_y, 10.0 - 4.0)
            self.assertNotIn("not available in this build", output)

    def test_unknown_engine_falls_back_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(tmp, "NotAPhysicsEngine")
            code, output = run_fall(tmp)
            self.assertEqual(code, 0, output)
            self.assertIn('3D physics engine "NotAPhysicsEngine"', output)
            self.assertIn("not available in this build", output)
            fall_y = float(re.search(r"FALL_Y=([-\d.e]+)", output).group(1))
            self.assertLess(fall_y, 10.0 - 4.0)  # The fallback engine still simulates.

    def test_default_setting_does_not_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(tmp)  # Old project without an explicit engine ("DEFAULT").
            code, output = run_fall(tmp)
            self.assertEqual(code, 0, output)
            self.assertIn("ENGINE=DEFAULT", output)
            self.assertNotIn("not available in this build", output)

    @unittest.skipUnless(os.environ.get("BAMBOO_GUI_TESTS"), "Opens an editor window; set BAMBOO_GUI_TESTS=1")
    def test_new_empty_project_gets_jolt(self):
        # `touch project.godot` workflow: the editor fills in EditorNode::get_initial_settings().
        # Upstream only does this when the editor is not headless (editor_node.cpp, `!cmdline_mode`).
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "project.godot"), "w").close()
            proc = subprocess.run(
                [BINARY, "--editor", "--path", tmp, "--quit-after", "60"], capture_output=True, text=True, timeout=300
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            with open(os.path.join(tmp, "project.godot"), encoding="utf-8") as f:
                self.assertIn('3d/physics_engine="Jolt Physics"', f.read())


if __name__ == "__main__":
    unittest.main()
