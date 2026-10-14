#!/usr/bin/env python3
"""Render the golden-image test scenes with each renderer and compare them with the golden images.

Each scene in `tests/visual/scenes/` is rendered with Movie Maker mode (`--write-movie`) at a fixed
frame rate; the frame `--frame` (default 10, after shader compilation) is kept as
`tests/visual/output/<scene>_<method>.png` and compared with `tests/visual/golden/<scene>_<method>.png`.

A GPU (or a software rasterizer such as llvmpipe/lavapipe on Linux) is required: `--headless`
uses a dummy renderer and cannot capture images.

Usage:
    python3 misc/scripts/capture_golden_images.py --binary bin/bamboo.macos.editor.arm64
        [--methods forward_plus,mobile,gl_compatibility] [--scenes test_pbr_materials,...]
        [--update-golden] [--threshold 0.015] [--golden-dir tests/visual/golden/linux]

Golden images depend on the GPU driver: `tests/visual/golden/` holds the macOS (Metal) baseline and
`tests/visual/golden/linux/` the Linux llvmpipe/lavapipe baseline used by the nightly CI job.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compare_images  # noqa: E402
from bamboo_versioning import REPO_ROOT  # noqa: E402

VISUAL_DIR = os.path.join(REPO_ROOT, "tests", "visual")
METHODS = ["forward_plus", "mobile", "gl_compatibility"]
# 2D canvas rendering is compared between Forward+ and Compatibility only.
SCENE_METHODS = {"test_canvas_item_2d": ["forward_plus", "gl_compatibility"]}


def list_scenes() -> list[str]:
    return sorted(
        os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(VISUAL_DIR, "scenes", "*.tscn"))
    )


def frame_path(movie_base: str, frame: int) -> str:
    # MovieWriterPNGWAV writes `<base><frame padded to 8 digits>.png`.
    return f"{movie_base}{frame:08d}.png"


def render(binary: str, scene: str, method: str, frame: int, output: str, timeout: float) -> Optional[str]:
    with tempfile.TemporaryDirectory(prefix="bamboo_golden_") as tmp:
        movie_base = os.path.join(tmp, "frame")
        cmd = [
            binary,
            "--path",
            VISUAL_DIR,
            "--rendering-method",
            method,
            "--write-movie",
            movie_base + ".png",
            "--fixed-fps",
            "10",
            "--quit-after",
            str(frame + 1),
            "--resolution",
            "320x240",
            "--disable-vsync",
            f"res://scenes/{scene}.tscn",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return f"timed out after {timeout}s"
        produced = frame_path(movie_base, frame)
        if not os.path.isfile(produced):
            frames = sorted(glob.glob(movie_base + "*.png"))
            if not frames:
                tail = (proc.stdout + proc.stderr).strip().splitlines()[-5:]
                return f"no frame written (exit {proc.returncode}): " + " | ".join(tail)
            produced = frames[-1]
        os.makedirs(os.path.dirname(output), exist_ok=True)
        shutil.copyfile(produced, output)
    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Capture and compare Bamboo golden images.")
    parser.add_argument("--binary", required=True)
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--scenes", default="", help="Comma-separated scene names (default: all).")
    parser.add_argument("--frame", type=int, default=10)
    parser.add_argument("--threshold", type=float, default=compare_images.DEFAULT_THRESHOLD)
    parser.add_argument("--channel-tolerance", type=int, default=compare_images.DEFAULT_CHANNEL_TOLERANCE)
    parser.add_argument("--update-golden", action="store_true", help="Overwrite golden images with the new renders.")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--golden-dir", default=os.path.join(VISUAL_DIR, "golden"), help="Golden images folder.")
    parser.add_argument("--output-dir", default=os.path.join(VISUAL_DIR, "output"), help="Rendered images folder.")
    args = parser.parse_args(argv)

    methods = [m for m in args.methods.split(",") if m]
    scenes = [s for s in args.scenes.split(",") if s] or list_scenes()
    output_dir = os.path.abspath(args.output_dir)
    golden_dir = os.path.abspath(args.golden_dir)

    failures = 0
    for scene in scenes:
        for method in methods:
            if method not in SCENE_METHODS.get(scene, METHODS):
                continue
            name = f"{scene}_{method}"
            actual = os.path.join(output_dir, name + ".png")
            golden = os.path.join(golden_dir, name + ".png")
            error = render(args.binary, scene, method, args.frame, actual, args.timeout)
            if error:
                print(f"[FAIL] {name}: render error: {error}")
                failures += 1
                continue
            if args.update_golden:
                os.makedirs(golden_dir, exist_ok=True)
                shutil.copyfile(actual, golden)
                print(f"[GOLD] {name}: golden image updated")
                continue
            if not os.path.isfile(golden):
                print(f"[FAIL] {name}: missing golden image {golden} (run with --update-golden)")
                failures += 1
                continue
            result = compare_images.compare_files(
                golden,
                actual,
                threshold=args.threshold,
                channel_tolerance=args.channel_tolerance,
                diff_output=os.path.join(output_dir, name + "_diff.png"),
            )
            status = "PASS" if result.passed else "FAIL"
            print(f"[{status}] {name}: {result.diff_percent:.3f}% pixels differ (MAE {result.mae:.2f})")
            failures += 0 if result.passed else 1

    print("Golden-image tests PASSED." if failures == 0 else f"Golden-image tests FAILED ({failures}).")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
