#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for the Unity asset converters (tools/unity_importer/mat_converter.py, prefab_to_tscn.py).

Run: python3 -m unittest tests/python_build/test_unity_asset_converter.py
Set BAMBOO_BINARY=bin/bamboo.<platform>.editor.<arch> to also load the generated files in the engine.
"""

import math
import os
import re
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMPORTER_DIR = os.path.join(REPO_ROOT, "tools", "unity_importer")
DATA_DIR = os.path.join(REPO_ROOT, "tests", "data")
sys.path.insert(0, IMPORTER_DIR)

import coordinate_conversion as cc  # noqa: E402
import mat_converter  # noqa: E402
import prefab_to_tscn  # noqa: E402
import unity_yaml  # noqa: E402

SAMPLE_MAT = os.path.join(DATA_DIR, "sample_unity_mat.mat")
SAMPLE_PREFAB = os.path.join(DATA_DIR, "unity", "sample_enemy.prefab")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def prop(text, name):
    match = re.search(rf"^{name} = (.+)$", text, re.M)
    return match.group(1) if match else None


def parse_transform(text):
    return [float(v) for v in re.match(r"Transform3D\((.*)\)", text).group(1).split(",")]


def node_block(tscn, name):
    match = re.search(rf'\[node name="{re.escape(name)}"[^\]]*\](?:\n(?!\[).*)*', tscn)
    return match.group(0) if match else None


URP_MAT = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!21 &2100000
Material:
  m_Name: Crate
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs:
    - _BaseMap:
        m_Texture: {fileID: 2800000, guid: aaaa1111, type: 3}
        m_Scale: {x: 1, y: 1}
        m_Offset: {x: 0, y: 0}
    - _EmissionMap:
        m_Texture: {fileID: 2800000, guid: bbbb2222, type: 3}
        m_Scale: {x: 1, y: 1}
        m_Offset: {x: 0, y: 0}
    m_Floats:
    - _Smoothness: 0.35
    - _Metallic: 1
    m_Colors:
    - _BaseColor: {r: 0.123456, g: 1, b: 0, a: 0.5}
    - _EmissionColor: {r: 2, g: 1, b: 0, a: 1}
"""


class TestUnityYaml(unittest.TestCase):
    def test_parse_flow_mapping(self):
        self.assertEqual(unity_yaml.parse_scalar("{x: 1, y: -2.5, z: 0}"), {"x": 1, "y": -2.5, "z": 0})
        self.assertEqual(unity_yaml.parse_scalar("{fileID: 0}"), {"fileID": 0})

    def test_parse_documents(self):
        objects = unity_yaml.parse_documents(read(SAMPLE_PREFAB))
        self.assertEqual(len(objects), 14)
        transform = next(o for o in objects if o.file_id == 201)
        self.assertEqual(transform.type_name, "Transform")
        self.assertEqual(transform.data["m_LocalScale"], {"x": 2, "y": 2, "z": 2})
        self.assertEqual(transform.data["m_Children"], [{"fileID": 301}])
        game_object = next(o for o in objects if o.file_id == 100)
        self.assertEqual(len(game_object.data["m_Component"]), 3)

    def test_guid_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "Assets", "Textures"))
            with open(os.path.join(tmp, "Assets", "Textures", "enemy.png.meta"), "w") as f:
                f.write("fileFormatVersion: 2\nguid: 4a7c9e1b2d3f4a5b6c7d8e9f0a1b2c3d\n")
            index = unity_yaml.build_guid_index(tmp)
            self.assertEqual(index["4a7c9e1b2d3f4a5b6c7d8e9f0a1b2c3d"], "Textures/enemy.png")


class TestMaterialConverter(unittest.TestCase):
    def test_glossiness_to_roughness(self):
        text, _ = mat_converter.convert_material(read(SAMPLE_MAT))
        self.assertTrue(text.startswith('[gd_resource type="StandardMaterial3D" format=3]'))
        # _Glossiness 0.8 -> roughness 0.2 (tolerance 0.001).
        self.assertAlmostEqual(float(prop(text, "roughness")), 0.2, delta=0.001)
        self.assertEqual(prop(text, "metallic"), "0.25")

    def test_color_rounding(self):
        text, _ = mat_converter.convert_material(read(SAMPLE_MAT))
        self.assertEqual(prop(text, "albedo_color"), "Color(0.8, 0.3137, 0.2, 1)")
        components = re.match(r"Color\((.*)\)", prop(text, "albedo_color")).group(1).split(", ")
        for component in components:
            value = float(component)
            self.assertTrue(0.0 <= value <= 1.0)
            self.assertLessEqual(len(component.split(".")[-1]) if "." in component else 0, 4)

    def test_textures_resolved_with_guid_index(self):
        index = {"4a7c9e1b2d3f4a5b6c7d8e9f0a1b2c3d": "Textures/enemy.png", "6b1d0f3c2a8e4b7f9c0d1e2f3a4b5c6d": "Textures/enemy_n.png"}
        text, warnings = mat_converter.convert_material(read(SAMPLE_MAT), index)
        self.assertEqual(warnings, [])
        self.assertIn('path="res://assets/Textures/enemy.png" id="1_albedo"', text)
        self.assertIn('path="res://assets/Textures/enemy_n.png" id="2_normal"', text)
        self.assertEqual(prop(text, "albedo_texture"), 'ExtResource("1_albedo")')
        self.assertEqual(prop(text, "normal_enabled"), "true")
        self.assertEqual(prop(text, "uv1_scale"), "Vector3(2, 2, 1)")
        self.assertEqual(prop(text, "uv1_offset"), "Vector3(0.5, 0, 0)")

    def test_unresolved_texture_warns(self):
        _, warnings = mat_converter.convert_material(read(SAMPLE_MAT))
        self.assertEqual(len(warnings), 2)
        self.assertIn("_MainTex", warnings[0])

    def test_urp_lit_properties(self):
        text, _ = mat_converter.convert_material(URP_MAT, {"aaaa1111": "crate.png", "bbbb2222": "crate_e.png"})
        self.assertAlmostEqual(float(prop(text, "roughness")), 0.65, delta=0.001)
        self.assertEqual(prop(text, "metallic"), "1")
        self.assertEqual(prop(text, "albedo_color"), "Color(0.1235, 1, 0, 0.5)")
        self.assertEqual(prop(text, "transparency"), "1")
        self.assertEqual(prop(text, "emission_enabled"), "true")
        self.assertIn("emission_texture = ExtResource(", text)

    def test_missing_material_raises(self):
        with self.assertRaises(ValueError):
            mat_converter.convert_material("%YAML 1.1\n--- !u!1 &1\nGameObject:\n  m_Name: X\n")


class TestPrefabConverter(unittest.TestCase):
    def setUp(self):
        self.tscn = prefab_to_tscn.convert_prefab(read(SAMPLE_PREFAB))

    def test_position_is_converted_to_right_handed(self):
        # Unity Vector3(1, 2, 3) -> Bamboo Vector3(1, 2, -3).
        values = parse_transform(prop(node_block(self.tscn, "Enemy"), "transform"))
        self.assertEqual(values[9:], [1.0, 2.0, -3.0])

    def test_rotation_and_scale(self):
        values = parse_transform(prop(node_block(self.tscn, "Body"), "transform"))
        basis = [values[0:3], values[3:6], values[6:9]]
        # Unity: +90 deg around Y (forward +Z -> right +X), scale 2.
        # Bamboo basis must map local forward (-Z) to +X, scaled by 2.
        local_forward = (0.0, 0.0, -1.0)
        mapped = [sum(basis[i][j] * local_forward[j] for j in range(3)) for i in range(3)]
        for got, expected in zip(mapped, (2.0, 0.0, 0.0)):
            self.assertAlmostEqual(got, expected, places=4)

    def test_matrix_matches_quaternion_rotation(self):
        q = cc.quat_from_axis_angle((0.3, 1.0, -0.4), 1.1)
        basis = prefab_to_tscn.quat_to_basis(q)
        v = (0.7, -1.2, 2.5)
        by_matrix = [sum(basis[i][j] * v[j] for j in range(3)) for i in range(3)]
        for a, b in zip(by_matrix, cc.quat_rotate(q, v)):
            self.assertAlmostEqual(a, b, places=9)

    def test_hierarchy_parents(self):
        self.assertIn('[node name="Enemy" type="RigidBody3D"]', self.tscn)
        self.assertIn('[node name="Body" type="MeshInstance3D" parent="."]', self.tscn)
        self.assertIn('[node name="Weapon" type="MeshInstance3D" parent="Body"]', self.tscn)
        self.assertIn('[node name="Eye Light" type="OmniLight3D" parent="."]', self.tscn)

    def test_collider_and_inactive_object(self):
        self.assertIn('[sub_resource type="BoxShape3D" id="Shape_1"]\nsize = Vector3(1, 2, 1)', self.tscn)
        shape = node_block(self.tscn, "CollisionShape3D")
        self.assertIn('parent="."', shape)
        self.assertEqual(parse_transform(prop(shape, "transform"))[9:], [0.0, 1.0, -0.5])
        self.assertEqual(prop(node_block(self.tscn, "Eye Light"), "visible"), "false")
        self.assertEqual(prop(node_block(self.tscn, "Body"), "metadata/unity_mesh_guid"), '"9f8e7d6c5b4a39281706f5e4d3c2b1a0"')

    def test_three_level_nesting_paths(self):
        nested = prefab_to_tscn.convert_prefab(
            read(SAMPLE_PREFAB).replace("m_Children: []\n  m_Father: {fileID: 201}", "m_Children:\n  - {fileID: 401}\n  m_Father: {fileID: 201}")
            .replace("  - {fileID: 201}\n  - {fileID: 401}\n  m_Father: {fileID: 0}", "  - {fileID: 201}\n  m_Father: {fileID: 0}")
            .replace("m_Father: {fileID: 101}\n--- !u!108", "m_Father: {fileID: 301}\n--- !u!108")
        )
        self.assertIn('[node name="Eye Light" type="OmniLight3D" parent="Body/Weapon"]', nested)

    def test_duplicate_sibling_names_are_made_unique(self):
        text = read(SAMPLE_PREFAB).replace("m_Name: Eye Light", "m_Name: Body")
        tscn = prefab_to_tscn.convert_prefab(text)
        self.assertIn('[node name="Body2" type="OmniLight3D" parent="."]', tscn)

    def test_variant_without_root_raises(self):
        variant = "%YAML 1.1\n--- !u!1001 &1\nPrefabInstance:\n  m_SourcePrefab: {fileID: 100100000, guid: abc, type: 3}\n"
        with self.assertRaises(ValueError):
            prefab_to_tscn.convert_prefab(variant)


VALIDATE_SCRIPT = """extends SceneTree

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var scene: PackedScene = load(args[0])
	var material: StandardMaterial3D = load(args[1])
	if scene == null or material == null:
		quit(1)
		return
	var root := scene.instantiate()
	print("ROOT=", root.name, ":", root.get_class(), " CHILDREN=", root.get_child_count(),
		" WEAPON=", root.get_node("Body/Weapon").get_class(), " ROUGHNESS=", snappedf(material.roughness, 0.001))
	root.free()
	quit(0)
"""


@unittest.skipUnless(os.environ.get("BAMBOO_BINARY"), "Set BAMBOO_BINARY to load converted assets in the engine")
class TestLoadInEngine(unittest.TestCase):
    def test_generated_files_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "project.godot"), "w") as f:
                f.write('config_version=5\n\n[application]\n\nconfig/name="ConverterCheck"\n')
            with open(os.path.join(tmp, "validate.gd"), "w") as f:
                f.write(VALIDATE_SCRIPT)
            with open(os.path.join(tmp, "enemy.tscn"), "w") as f:
                f.write(prefab_to_tscn.convert_prefab(read(SAMPLE_PREFAB)))
            with open(os.path.join(tmp, "material.tres"), "w") as f:
                f.write(mat_converter.convert_material(read(SAMPLE_MAT).replace("fileID: 2800000", "fileID: 0"))[0])
            proc = subprocess.run(
                [os.environ["BAMBOO_BINARY"], "--headless", "--path", tmp, "--script", "res://validate.gd", "--",
                 "res://enemy.tscn", "res://material.tres"],
                capture_output=True, text=True, timeout=120,
            )
            output = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, output)
            self.assertIn("ROOT=Enemy:RigidBody3D CHILDREN=3 WEAPON=MeshInstance3D ROUGHNESS=0.2", output)
            self.assertNotIn("ERROR", output)


if __name__ == "__main__":
    unittest.main()
