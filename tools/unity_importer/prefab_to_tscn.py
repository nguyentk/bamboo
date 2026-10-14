#!/usr/bin/env python3
"""Convert a Unity prefab (`.prefab`, text YAML) to a Bamboo scene (`.tscn`).

- Rebuilds the GameObject / Transform hierarchy (`m_Father`, `m_Children`).
- Converts transforms from Unity (left-handed) to Bamboo (right-handed) with a Z flip, see
  `coordinate_conversion.py`.
- Chooses the node type from the components (see `schema/unity_to_bamboo_spec.json`) and adds
  `CollisionShape3D` children for Box/Sphere/Capsule colliders.
- Mesh references cannot be resolved from the prefab alone; the Unity mesh GUID is kept as node
  metadata (`unity_mesh_guid`) for the model import step.

Usage:
    python3 tools/unity_importer/prefab_to_tscn.py --input Enemy.prefab --output enemy.tscn
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import coordinate_conversion as cc  # noqa: E402
import unity_yaml  # noqa: E402
from mat_converter import fmt  # noqa: E402

CLASS_GAMEOBJECT = 1
CLASS_TRANSFORM = 4
CLASS_CAMERA = 20
CLASS_MESH_RENDERER = 23
CLASS_MESH_FILTER = 33
CLASS_RIGIDBODY = 54
CLASS_BOX_COLLIDER = 65
CLASS_LIGHT = 108
CLASS_SPHERE_COLLIDER = 135
CLASS_CAPSULE_COLLIDER = 136
CLASS_SKINNED_MESH_RENDERER = 137
CLASS_CHARACTER_CONTROLLER = 143
CLASS_AUDIO_SOURCE = 82
COLLIDERS = {CLASS_BOX_COLLIDER, CLASS_SPHERE_COLLIDER, CLASS_CAPSULE_COLLIDER}
# Unity Light.m_Type: 0 = Spot, 1 = Directional, 2 = Point.
LIGHT_TYPES = {0: "SpotLight3D", 1: "DirectionalLight3D", 2: "OmniLight3D"}


def quat_to_basis(q: Sequence[float]) -> List[List[float]]:
    """Rotation matrix (rows) from a unit quaternion (x, y, z, w)."""
    x, y, z, w = q
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


def transform3d(position: Sequence[float], rotation: Sequence[float], scale: Sequence[float]) -> str:
    """Bamboo `Transform3D(...)` text (basis rows, then origin) from Unity local TRS values."""
    pos = cc.convert_position(position)
    rot = cc.convert_quaternion(rotation)
    scl = cc.convert_scale(scale)
    basis = quat_to_basis(rot)
    values = [basis[i][j] * scl[j] for i in range(3) for j in range(3)] + list(pos)
    return "Transform3D(" + ", ".join(fmt(v) for v in values) + ")"


def _vec(data, keys="xyz", default=0.0) -> Tuple[float, ...]:
    data = data or {}
    return tuple(float(data.get(k, default)) for k in keys)


def _file_id(ref) -> int:
    return int(ref.get("fileID", 0)) if isinstance(ref, dict) else 0


class PrefabConverter:
    def __init__(self, objects: List[unity_yaml.UnityObject]):
        self.by_id: Dict[int, unity_yaml.UnityObject] = {o.file_id: o for o in objects}
        self.sub_resources: List[str] = []
        self.nodes: List[str] = []

    def components_of(self, game_object: unity_yaml.UnityObject) -> List[unity_yaml.UnityObject]:
        result = []
        for entry in game_object.data.get("m_Component") or []:
            component = self.by_id.get(_file_id((entry or {}).get("component")))
            if component:
                result.append(component)
        return result

    def node_type(self, components: List[unity_yaml.UnityObject]) -> str:
        ids = {c.class_id for c in components}
        if CLASS_RIGIDBODY in ids:
            rigidbody = next(c for c in components if c.class_id == CLASS_RIGIDBODY)
            return "AnimatableBody3D" if int(rigidbody.data.get("m_IsKinematic", 0)) else "RigidBody3D"
        if CLASS_CHARACTER_CONTROLLER in ids:
            return "CharacterBody3D"
        if ids & COLLIDERS:
            colliders = [c for c in components if c.class_id in COLLIDERS]
            if all(int(c.data.get("m_IsTrigger", 0)) for c in colliders):
                return "Area3D"
            if not ids & {CLASS_MESH_RENDERER, CLASS_SKINNED_MESH_RENDERER}:
                return "StaticBody3D"
        if CLASS_MESH_RENDERER in ids or CLASS_SKINNED_MESH_RENDERER in ids:
            return "MeshInstance3D"
        if CLASS_CAMERA in ids:
            return "Camera3D"
        if CLASS_LIGHT in ids:
            light = next(c for c in components if c.class_id == CLASS_LIGHT)
            return LIGHT_TYPES.get(int(light.data.get("m_Type", 2)), "OmniLight3D")
        if CLASS_AUDIO_SOURCE in ids:
            return "AudioStreamPlayer3D"
        return "Node3D"

    def add_shape(self, collider: unity_yaml.UnityObject) -> Optional[Tuple[str, str]]:
        """Create the shape sub-resource; return (sub_resource_id, local Transform3D)."""
        res_id = f"Shape_{len(self.sub_resources) + 1}"
        center = _vec(collider.data.get("m_Center"))
        rotation = (0.0, 0.0, 0.0, 1.0)
        if collider.class_id == CLASS_BOX_COLLIDER:
            size = _vec(collider.data.get("m_Size"), default=1.0)
            body = f"size = Vector3({fmt(size[0])}, {fmt(size[1])}, {fmt(size[2])})"
            shape = "BoxShape3D"
        elif collider.class_id == CLASS_SPHERE_COLLIDER:
            body = f"radius = {fmt(collider.data.get('m_Radius', 0.5))}"
            shape = "SphereShape3D"
        elif collider.class_id == CLASS_CAPSULE_COLLIDER:
            body = f"radius = {fmt(collider.data.get('m_Radius', 0.5))}\nheight = {fmt(collider.data.get('m_Height', 2))}"
            shape = "CapsuleShape3D"
            # Unity m_Direction: 0 = X, 1 = Y (Bamboo capsules are Y-aligned), 2 = Z.
            direction = int(collider.data.get("m_Direction", 1))
            s = 0.7071067811865476
            rotation = {0: (0.0, 0.0, s, s), 2: (s, 0.0, 0.0, s)}.get(direction, rotation)
        else:
            return None
        self.sub_resources.append(f'[sub_resource type="{shape}" id="{res_id}"]\n{body}')
        return res_id, transform3d(center, rotation, (1.0, 1.0, 1.0))

    def emit(self, transform: unity_yaml.UnityObject, parent_path: Optional[str], used_names: Dict[str, int]) -> None:
        game_object = self.by_id.get(_file_id(transform.data.get("m_GameObject")))
        if game_object is None:
            return
        components = self.components_of(game_object)
        base_name = str(game_object.data.get("m_Name") or "Node").replace("/", "_").replace(".", "_")
        name = base_name
        if parent_path is not None:
            count = used_names.get(base_name, 0)
            used_names[base_name] = count + 1
            if count:
                name = f"{base_name}{count + 1}"

        node_type = self.node_type(components)
        header = f'[node name="{name}" type="{node_type}"'
        if parent_path is not None:
            header += f' parent="{parent_path}"'
        lines = [header + "]"]

        transform_text = transform3d(
            _vec(transform.data.get("m_LocalPosition")),
            _vec(transform.data.get("m_LocalRotation"), "xyzw"),
            _vec(transform.data.get("m_LocalScale"), default=1.0),
        )
        if transform_text != "Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)":
            lines.append(f"transform = {transform_text}")
        if not int(game_object.data.get("m_IsActive", 1)):
            lines.append("visible = false")
        mesh_filter = next((c for c in components if c.class_id == CLASS_MESH_FILTER), None)
        if mesh_filter:
            mesh = mesh_filter.data.get("m_Mesh") or {}
            if mesh.get("guid"):
                lines.append(f'metadata/unity_mesh_guid = "{mesh["guid"]}"')
            if mesh.get("fileID"):
                lines.append(f'metadata/unity_mesh_file_id = {mesh["fileID"]}')
        self.nodes.append("\n".join(lines))

        my_path = "." if parent_path is None else (name if parent_path == "." else f"{parent_path}/{name}")
        child_names: Dict[str, int] = {}
        for index, collider in enumerate(c for c in components if c.class_id in COLLIDERS):
            shape = self.add_shape(collider)
            if shape:
                res_id, shape_transform = shape
                shape_lines = [f'[node name="CollisionShape3D{index + 1 if index else ""}" type="CollisionShape3D" parent="{my_path}"]']
                if shape_transform != "Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)":
                    shape_lines.append(f"transform = {shape_transform}")
                shape_lines.append(f'shape = SubResource("{res_id}")')
                self.nodes.append("\n".join(shape_lines))
        for child_ref in transform.data.get("m_Children") or []:
            child = self.by_id.get(_file_id(child_ref))
            if child is not None:
                self.emit(child, my_path, child_names)

    def convert(self) -> str:
        transforms = [o for o in self.by_id.values() if o.class_id == CLASS_TRANSFORM]
        roots = [t for t in transforms if _file_id(t.data.get("m_Father")) == 0]
        if not roots:
            raise ValueError("No root Transform found (prefab variants must be converted from their base prefab)")
        self.emit(roots[0], None, {})
        parts = ["[gd_scene format=3]", ""]
        for sub_resource in self.sub_resources:
            parts += [sub_resource, ""]
        for node in self.nodes:
            parts += [node, ""]
        return "\n".join(parts).rstrip("\n") + "\n"


def convert_prefab(unity_text: str) -> str:
    return PrefabConverter(unity_yaml.parse_documents(unity_text)).convert()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a Unity .prefab to a Bamboo .tscn scene.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as f:
        try:
            text = convert_prefab(f.read())
        except ValueError as e:
            print(f"ERROR: {args.input}: {e}", file=sys.stderr)
            return 1
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
