#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for the Unity -> Bamboo mapping spec, coordinate conversion and project survey tool.

Run: python3 -m unittest tests/python_build/test_unity_mapping_spec.py
"""

import json
import math
import os
import random
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPORTER_DIR = os.path.join(REPO_ROOT, "tools", "unity_importer")
SPEC_PATH = os.path.join(IMPORTER_DIR, "schema", "unity_to_bamboo_spec.json")
sys.path.insert(0, IMPORTER_DIR)

import coordinate_conversion as cc  # noqa: E402
import survey_unity_project as survey  # noqa: E402


def load_spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)


def assert_vec_close(test, a, b, places=9):
    for x, y in zip(a, b):
        test.assertAlmostEqual(x, y, places=places)


class TestSpecSchema(unittest.TestCase):
    def setUp(self):
        self.spec = load_spec()

    def test_required_sections(self):
        for key in (
            "node_type_mapping",
            "transform_conversion",
            "lifecycle_methods",
            "component_mapping",
            "type_mapping",
        ):
            self.assertIn(key, self.spec)
            self.assertTrue(self.spec[key], key)

    def test_core_node_mappings(self):
        nodes = self.spec["node_type_mapping"]
        self.assertEqual(nodes["GameObject"]["bamboo"], "Node3D")
        self.assertEqual(nodes["Prefab"]["bamboo"], "PackedScene")
        self.assertEqual(nodes["Prefab Variant"]["bamboo"], "Inherited PackedScene")
        self.assertEqual(nodes["ScriptableObject"]["bamboo"], "Resource")

    def test_lifecycle_methods(self):
        lifecycle = self.spec["lifecycle_methods"]
        expected = {"Start": "_ready", "Update": "_process", "FixedUpdate": "_physics_process"}
        for unity, bamboo in expected.items():
            self.assertEqual(lifecycle[unity]["bamboo"], bamboo)
        self.assertIn("Awake", lifecycle)

    def test_physics_uses_jolt(self):
        self.assertEqual(self.spec["component_mapping"]["Rigidbody"]["physics_engine"], "Jolt")

    def test_type_mapping_completeness(self):
        types = self.spec["type_mapping"]
        for unity_type, bamboo_type in {
            "Vector2": "Vector2",
            "Vector3": "Vector3",
            "Quaternion": "Quaternion",
            "Color": "Color",
            "string": "String",
            "Rect": "Rect2",
            "Bounds": "AABB",
        }.items():
            self.assertEqual(types[unity_type], bamboo_type, unity_type)

    def test_transform_conversion_rules_match_code(self):
        rules = self.spec["transform_conversion"]
        self.assertEqual(rules["method"], "mirror_z")
        self.assertEqual(rules["position"], {"x": "x", "y": "y", "z": "-z"})
        self.assertEqual(rules["rotation_quaternion"], {"x": "-x", "y": "-y", "z": "z", "w": "w"})
        self.assertEqual(rules["scale"], {"x": "x", "y": "y", "z": "z"})


class TestCoordinateConversion(unittest.TestCase):
    def test_basis_vectors(self):
        # Unity +X right, +Y up, +Z forward -> Bamboo +X right, +Y up, -Z forward.
        self.assertEqual(cc.convert_position((1, 0, 0)), (1.0, 0.0, 0.0))
        self.assertEqual(cc.convert_position((0, 1, 0)), (0.0, 1.0, 0.0))
        self.assertEqual(cc.convert_direction((0, 0, 1)), (0.0, 0.0, -1.0))

    def test_sample_position(self):
        self.assertEqual(cc.convert_position((1.5, -2.0, 3.25)), (1.5, -2.0, -3.25))

    def test_scale_unchanged(self):
        self.assertEqual(cc.convert_scale((2, 3, 4)), (2.0, 3.0, 4.0))

    def test_rotation_is_consistent_with_position_conversion(self):
        # Rotating in Unity space then converting must equal converting then rotating in Bamboo space.
        rng = random.Random(1234)
        for _ in range(200):
            axis = [rng.uniform(-1, 1) for _ in range(3)]
            if sum(a * a for a in axis) < 1e-6:
                continue
            q = cc.quat_from_axis_angle(axis, rng.uniform(-math.pi, math.pi))
            v = [rng.uniform(-10, 10) for _ in range(3)]
            unity_result = cc.convert_position(cc.quat_rotate(q, v))
            bamboo_result = cc.quat_rotate(cc.convert_quaternion(q), cc.convert_position(v))
            assert_vec_close(self, unity_result, bamboo_result)

    def test_yaw_90_degrees(self):
        # Unity: +90 deg around +Y turns forward (+Z) to right (+X).
        q = cc.quat_from_axis_angle((0, 1, 0), math.pi / 2)
        assert_vec_close(self, cc.quat_rotate(q, (0, 0, 1)), (1, 0, 0))
        # In Bamboo the converted rotation must turn forward (-Z) to right (+X) as well.
        assert_vec_close(self, cc.quat_rotate(cc.convert_quaternion(q), (0, 0, -1)), (1, 0, 0))

    def test_converted_quaternion_stays_unit(self):
        q = cc.quat_from_axis_angle((1, 2, 3), 0.7)
        q2 = cc.convert_quaternion(q)
        self.assertAlmostEqual(sum(c * c for c in q2), 1.0, places=12)


UNITY_SCENE = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &100
GameObject:
  m_Name: Player
--- !u!4 &101
Transform:
  m_LocalPosition: {x: 0, y: 1, z: 2}
--- !u!54 &102
Rigidbody:
  m_Mass: 1
--- !u!65 &103
BoxCollider:
  m_IsTrigger: 0
--- !u!114 &104
MonoBehaviour:
  m_Script: {fileID: 11500000}
"""

UNITY_PREFAB = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &200
GameObject:
  m_Name: Enemy
--- !u!4 &201
Transform:
  m_LocalPosition: {x: 0, y: 0, z: 0}
--- !u!136 &202
CapsuleCollider:
  m_Height: 2
"""

UNITY_PREFAB_VARIANT = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1001 &300
PrefabInstance:
  m_SourcePrefab: {fileID: 100100000, guid: abc, type: 3}
"""

PLAYER_CS = """using UnityEngine;
using UnityEngine.Events;
public class Player : MonoBehaviour {
    public UnityEvent onDeath;
    void Update() { float h = Input.GetAxis("Horizontal"); }
}
"""

CONFIG_CS = """using UnityEngine;
public class GameConfig : ScriptableObject { public int lives = 3; }
"""

MANIFEST = '{"dependencies": {"com.unity.render-pipelines.universal": "17.0.3", "com.unity.textmeshpro": "3.0.6"}}'


class TestSurveyTool(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        files = {
            "Assets/Scenes/Main.unity": UNITY_SCENE,
            "Assets/Prefabs/Enemy.prefab": UNITY_PREFAB,
            "Assets/Prefabs/EnemyBoss.prefab": UNITY_PREFAB_VARIANT,
            "Assets/Scripts/Player.cs": PLAYER_CS,
            "Assets/Scripts/GameConfig.cs": CONFIG_CS,
            "Assets/Models/enemy.fbx": "binary",
            "Assets/Textures/enemy.png": "binary",
            "Assets/Textures/enemy.png.meta": "guid: abc",
            "Packages/manifest.json": MANIFEST,
        }
        for rel, content in files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        self.report = survey.survey(root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_counts(self):
        self.assertEqual(self.report["scenes"], 1)
        self.assertEqual(self.report["prefabs"], 2)
        self.assertEqual(self.report["prefab_variants"], 1)
        self.assertEqual(self.report["scripts"], 2)
        self.assertEqual(self.report["assets"]["models"], 1)
        self.assertEqual(self.report["assets"]["textures"], 1)  # .meta files are ignored

    def test_components_and_categories(self):
        physics = self.report["components_by_category"]["physics"]
        self.assertEqual(physics, {"BoxCollider": 1, "CapsuleCollider": 1, "Rigidbody": 1})
        self.assertEqual(self.report["components"]["MonoBehaviour"], 1)

    def test_script_features(self):
        features = self.report["script_features"]
        self.assertEqual(features["MonoBehaviour"], 1)
        self.assertEqual(features["ScriptableObject"], 1)
        self.assertEqual(features["UnityEvent"], 1)
        self.assertEqual(features["Legacy Input (Input.Get*)"], 1)

    def test_render_pipeline_and_packages(self):
        self.assertEqual(self.report["render_pipeline"], "URP")
        self.assertIn("com.unity.textmeshpro", self.report["packages"])

    def test_every_component_has_a_mapping_or_is_structural(self):
        spec = load_spec()
        mapped = set(spec["component_mapping"]) | set(spec["node_type_mapping"])
        mapped |= {key.split(":")[0] for key in spec["component_mapping"]}
        mapped |= {part for key in spec["component_mapping"] for part in key.split("+")}
        structural = {"GameObject", "Transform", "MonoBehaviour", "PrefabInstance", "CanvasRenderer"}
        for component in self.report["components"]:
            self.assertTrue(component in mapped or component in structural, component)

    def test_missing_assets_folder(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(FileNotFoundError):
                survey.survey(empty)


if __name__ == "__main__":
    unittest.main()
