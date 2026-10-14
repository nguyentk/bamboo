#!/usr/bin/env python3
"""Inventory a Unity project before porting it to Bamboo Engine.

Scans the `Assets/` folder (text-serialized Unity YAML is required: Project Settings > Editor >
Asset Serialization = Force Text) and reports scenes, prefabs, scripts, components, physics,
rendering, UI and input usage.

Usage:
    python3 tools/unity_importer/survey_unity_project.py /path/to/UnityProject [--json] [--output report.json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import Dict, Optional, Sequence

# Unity built-in class IDs (YAML header `--- !u!<class_id> &<file_id>`).
# Reference: https://docs.unity3d.com/Manual/ClassIDReference.html
UNITY_CLASS_IDS: Dict[int, str] = {
    1: "GameObject",
    4: "Transform",
    20: "Camera",
    23: "MeshRenderer",
    33: "MeshFilter",
    50: "Rigidbody2D",
    54: "Rigidbody",
    58: "CircleCollider2D",
    60: "PolygonCollider2D",
    61: "BoxCollider2D",
    64: "MeshCollider",
    65: "BoxCollider",
    81: "AudioListener",
    82: "AudioSource",
    95: "Animator",
    108: "Light",
    111: "Animation",
    114: "MonoBehaviour",
    135: "SphereCollider",
    136: "CapsuleCollider",
    137: "SkinnedMeshRenderer",
    143: "CharacterController",
    195: "NavMeshAgent",
    198: "ParticleSystem",
    212: "SpriteRenderer",
    215: "ReflectionProbe",
    218: "Terrain",
    222: "CanvasRenderer",
    223: "Canvas",
    224: "RectTransform",
    1001: "PrefabInstance",
}

CATEGORIES = {
    "physics": {
        "Rigidbody",
        "Rigidbody2D",
        "CharacterController",
        "BoxCollider",
        "SphereCollider",
        "CapsuleCollider",
        "MeshCollider",
        "BoxCollider2D",
        "CircleCollider2D",
        "PolygonCollider2D",
    },
    "rendering": {"MeshRenderer", "MeshFilter", "SkinnedMeshRenderer", "SpriteRenderer", "Light", "Camera", "ReflectionProbe", "Terrain"},
    "animation": {"Animator", "Animation"},
    "audio": {"AudioSource", "AudioListener"},
    "vfx": {"ParticleSystem"},
    "ui": {"Canvas", "CanvasRenderer", "RectTransform"},
    "navigation": {"NavMeshAgent"},
}

MODEL_EXTENSIONS = {".fbx", ".obj", ".blend", ".gltf", ".glb", ".dae", ".3ds", ".max", ".ma", ".mb"}
TEXTURE_EXTENSIONS = {".png", ".tga", ".jpg", ".jpeg", ".psd", ".tif", ".tiff", ".exr", ".hdr", ".bmp", ".gif"}
AUDIO_EXTENSIONS = {".wav", ".ogg", ".mp3", ".aif", ".aiff", ".flac"}

_HEADER_RE = re.compile(r"^--- !u!(\d+) &", re.M)

SCRIPT_PATTERNS = {
    "MonoBehaviour": re.compile(r":\s*MonoBehaviour\b"),
    "ScriptableObject": re.compile(r":\s*ScriptableObject\b"),
    "UnityEvent": re.compile(r"\bUnityEvent\b"),
    "C# event/Action": re.compile(r"\b(event\s+\w|Action<|Action\b|Func<)"),
    "Coroutine": re.compile(r"\bIEnumerator\b|\bStartCoroutine\b"),
    "Legacy Input (Input.Get*)": re.compile(r"\bInput\.Get(Axis|Button|Key|Mouse)"),
    "New Input System": re.compile(r"\bUnityEngine\.InputSystem\b|\bInputAction\b"),
    "TextMeshPro": re.compile(r"\bTMPro\b|\bTextMeshPro"),
    "Addressables": re.compile(r"\bAddressables\b"),
    "DOTween": re.compile(r"\bDOTween\b|\.DO[A-Z]\w*\("),
    "async/await": re.compile(r"\basync\s+\w|\bawait\b"),
}


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def is_prefab_variant(text: str) -> bool:
    """Heuristic: a variant has a PrefabInstance (1001) but no own root GameObject definition."""
    class_ids = {int(c) for c in _HEADER_RE.findall(text)}
    return 1001 in class_ids and "m_SourcePrefab" in text and 1 not in class_ids


def survey(project_path: str) -> dict:
    assets = os.path.join(project_path, "Assets")
    if not os.path.isdir(assets):
        raise FileNotFoundError(f"No Assets/ folder found in {project_path}")

    files = Counter()
    components = Counter()
    script_features = Counter()
    binary_yaml = []
    prefabs = variants = 0

    for root, dirs, names in os.walk(assets):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in names:
            ext = os.path.splitext(name)[1].lower()
            path = os.path.join(root, name)
            if ext == ".meta":
                continue
            if ext in (".unity", ".prefab", ".asset", ".mat", ".controller", ".anim", ".physicmaterial"):
                files[ext] += 1
                text = _read_text(path)
                if not text.startswith("%YAML"):
                    binary_yaml.append(os.path.relpath(path, project_path))
                    continue
                if ext in (".unity", ".prefab"):
                    for class_id in _HEADER_RE.findall(text):
                        components[UNITY_CLASS_IDS.get(int(class_id), f"class_{class_id}")] += 1
                if ext == ".prefab":
                    prefabs += 1
                    if is_prefab_variant(text):
                        variants += 1
            elif ext == ".cs":
                files[".cs"] += 1
                text = _read_text(path)
                for feature, pattern in SCRIPT_PATTERNS.items():
                    if pattern.search(text):
                        script_features[feature] += 1
            elif ext in MODEL_EXTENSIONS:
                files["models"] += 1
            elif ext in TEXTURE_EXTENSIONS:
                files["textures"] += 1
            elif ext in AUDIO_EXTENSIONS:
                files["audio"] += 1
            elif ext in (".shader", ".shadergraph", ".hlsl", ".cginc", ".compute"):
                files["shaders"] += 1
            elif ext == ".vfx":
                files["vfx_graph"] += 1
            elif ext == ".inputactions":
                files["input_actions"] += 1
            elif ext in (".uxml", ".uss"):
                files["ui_toolkit"] += 1

    by_category = {
        category: {name: components[name] for name in sorted(names) if components[name]}
        for category, names in CATEGORIES.items()
    }

    packages = {}
    manifest = os.path.join(project_path, "Packages", "manifest.json")
    if os.path.isfile(manifest):
        try:
            packages = json.loads(_read_text(manifest)).get("dependencies", {})
        except json.JSONDecodeError:
            packages = {}

    render_pipeline = "Built-in"
    if any("render-pipelines.universal" in p for p in packages):
        render_pipeline = "URP"
    elif any("render-pipelines.high-definition" in p for p in packages):
        render_pipeline = "HDRP"

    return {
        "project": os.path.abspath(project_path),
        "scenes": files[".unity"],
        "prefabs": prefabs,
        "prefab_variants": variants,
        "scripts": files[".cs"],
        "script_features": dict(sorted(script_features.items())),
        "components": dict(sorted(components.items())),
        "components_by_category": by_category,
        "assets": {
            "models": files["models"],
            "textures": files["textures"],
            "audio": files["audio"],
            "materials": files[".mat"],
            "shaders": files["shaders"],
            "vfx_graph": files["vfx_graph"],
            "animator_controllers": files[".controller"],
            "animation_clips": files[".anim"],
            "physic_materials": files[".physicmaterial"],
            "scriptable_object_assets": files[".asset"],
            "input_actions": files["input_actions"],
            "ui_toolkit": files["ui_toolkit"],
        },
        "render_pipeline": render_pipeline,
        "packages": packages,
        "binary_serialized_files": binary_yaml,
    }


def format_report(report: dict) -> str:
    lines = [
        f"Unity project: {report['project']}",
        f"Render pipeline: {report['render_pipeline']}",
        f"Scenes: {report['scenes']}  Prefabs: {report['prefabs']} (variants: {report['prefab_variants']})  Scripts: {report['scripts']}",
        "Assets: " + ", ".join(f"{k}={v}" for k, v in report["assets"].items() if v),
        "Script features: " + (", ".join(f"{k}={v}" for k, v in report["script_features"].items()) or "-"),
    ]
    for category, counts in report["components_by_category"].items():
        if counts:
            lines.append(f"{category}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    if report["binary_serialized_files"]:
        lines.append(
            f"WARNING: {len(report['binary_serialized_files'])} binary-serialized assets; "
            "set Asset Serialization to 'Force Text' and re-run."
        )
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory a Unity project before porting to Bamboo.")
    parser.add_argument("project")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", help="Write the JSON report to this file.")
    args = parser.parse_args(argv)
    try:
        report = survey(args.project)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
