#!/usr/bin/env python3
"""Convert Unity materials (`.mat`, Standard or URP/Lit) to Bamboo `StandardMaterial3D` (`.tres`).

Property mapping (URP name first, then Built-in Standard name):
    _BaseColor / _Color             -> albedo_color
    _BaseMap / _MainTex             -> albedo_texture (+ uv1_scale / uv1_offset)
    _Metallic                       -> metallic
    _Smoothness / _Glossiness       -> roughness = 1 - smoothness
    _BumpMap                        -> normal_texture (Unity and Bamboo both use OpenGL-style +Y normal maps)
    _OcclusionMap                   -> ao_texture
    _EmissionColor / _EmissionMap   -> emission

Usage:
    python3 tools/unity_importer/mat_converter.py --input Enemy.mat --output enemy.tres
        [--unity-project /path/to/UnityProject] [--res-prefix res://assets]
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unity_yaml  # noqa: E402

MATERIAL_CLASS_ID = 21


def fmt(value: float) -> str:
    """Format a float like Bamboo's text resources (no trailing zeros, max 4 decimals)."""
    value = round(float(value), 4)
    if value == int(value):
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _props(entries: Optional[list[Any]]) -> dict[str, Any]:
    """Flatten Unity's `- _Name: value` lists into a dict."""
    result = {}
    for entry in entries or []:
        if isinstance(entry, dict):
            result.update(entry)
    return result


def _first(props: dict[str, Any], *names):
    for name in names:
        if name in props and props[name] is not None:
            return props[name]
    return None


def _texture_guid(tex_env) -> Optional[str]:
    if not isinstance(tex_env, dict):
        return None
    texture = tex_env.get("m_Texture")
    if isinstance(texture, dict) and texture.get("fileID", 0) != 0 and texture.get("guid"):
        return str(texture["guid"])
    return None


def convert_material(
    unity_text: str, guid_index: Optional[dict[str, str]] = None, res_prefix: str = "res://assets"
) -> tuple[str, list[str]]:
    """Return (tres_text, warnings)."""
    warnings: list[str] = []
    material = next((o for o in unity_yaml.parse_documents(unity_text) if o.class_id == MATERIAL_CLASS_ID), None)
    if material is None:
        raise ValueError("No Material object found in the .mat file")

    saved = material.data.get("m_SavedProperties") or {}
    tex_envs = _props(saved.get("m_TexEnvs"))
    floats = _props(saved.get("m_Floats"))
    colors = _props(saved.get("m_Colors"))

    properties: list[str] = []
    ext_resources: list[str] = []

    def texture_resource(prop: str, label: str) -> Optional[str]:
        tex_env = tex_envs.get(prop)
        guid = _texture_guid(tex_env)
        if not guid:
            return None
        path = (guid_index or {}).get(guid)
        if path is None:
            warnings.append(f"{prop}: texture GUID {guid} not found (pass --unity-project to resolve it)")
            res_path = f"{res_prefix}/unresolved/{guid}.png"
        else:
            res_path = f"{res_prefix}/{path}"
        res_id = f"{len(ext_resources) + 1}_{label}"
        ext_resources.append(f'[ext_resource type="Texture2D" path="{res_path}" id="{res_id}"]')
        return f'ExtResource("{res_id}")'

    color = _first(colors, "_BaseColor", "_Color")
    if isinstance(color, dict):
        r, g, b, a = (color.get(c, 1.0) for c in ("r", "g", "b", "a"))
        properties.append(f"albedo_color = Color({fmt(r)}, {fmt(g)}, {fmt(b)}, {fmt(a)})")
        if float(a) < 1.0:
            properties.append("transparency = 1")

    albedo_prop = "_BaseMap" if _texture_guid(tex_envs.get("_BaseMap")) else "_MainTex"
    albedo = texture_resource(albedo_prop, "albedo")
    if albedo:
        properties.append(f"albedo_texture = {albedo}")
        tex_env = tex_envs.get(albedo_prop) or {}
        scale, offset = tex_env.get("m_Scale") or {}, tex_env.get("m_Offset") or {}
        if scale and (scale.get("x", 1) != 1 or scale.get("y", 1) != 1):
            properties.append(f"uv1_scale = Vector3({fmt(scale.get('x', 1))}, {fmt(scale.get('y', 1))}, 1)")
        if offset and (offset.get("x", 0) != 0 or offset.get("y", 0) != 0):
            properties.append(f"uv1_offset = Vector3({fmt(offset.get('x', 0))}, {fmt(offset.get('y', 0))}, 0)")

    metallic = _first(floats, "_Metallic")
    properties.append(f"metallic = {fmt(metallic if metallic is not None else 0.0)}")
    smoothness = _first(floats, "_Smoothness", "_Glossiness")
    roughness = 1.0 - float(smoothness) if smoothness is not None else 1.0
    properties.append(f"roughness = {fmt(min(max(roughness, 0.0), 1.0))}")

    normal = texture_resource("_BumpMap", "normal")
    if normal:
        properties += ["normal_enabled = true", f"normal_texture = {normal}"]
        bump_scale = _first(floats, "_BumpScale")
        if bump_scale is not None and float(bump_scale) != 1.0:
            properties.append(f"normal_scale = {fmt(bump_scale)}")

    occlusion = texture_resource("_OcclusionMap", "ao")
    if occlusion:
        properties += ["ao_enabled = true", f"ao_texture = {occlusion}"]

    emission_color = _first(colors, "_EmissionColor")
    emission_map = texture_resource("_EmissionMap", "emission")
    if isinstance(emission_color, dict) and any(float(emission_color.get(c, 0)) > 0 for c in "rgb"):
        r, g, b = (emission_color.get(c, 0.0) for c in "rgb")
        properties += ["emission_enabled = true", f"emission = Color({fmt(r)}, {fmt(g)}, {fmt(b)}, 1)"]
        if emission_map:
            properties.append(f"emission_texture = {emission_map}")

    name = material.data.get("m_Name") or "Material"
    lines = ['[gd_resource type="StandardMaterial3D" format=3]', ""]
    if ext_resources:
        lines += ext_resources + [""]
    lines += ["[resource]", f'resource_name = "{name}"'] + properties
    return "\n".join(lines) + "\n", warnings


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a Unity .mat to a Bamboo StandardMaterial3D .tres.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--unity-project", help="Unity project root, used to resolve texture GUIDs via .meta files.")
    parser.add_argument("--res-prefix", default="res://assets")
    args = parser.parse_args(argv)

    guid_index = unity_yaml.build_guid_index(args.unity_project) if args.unity_project else None
    with open(args.input, "r", encoding="utf-8") as f:
        try:
            text, warnings = convert_material(f.read(), guid_index, args.res_prefix)
        except ValueError as e:
            print(f"ERROR: {args.input}: {e}", file=sys.stderr)
            return 1
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
