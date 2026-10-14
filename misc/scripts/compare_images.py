#!/usr/bin/env python3
"""Compare a rendered image against a golden image (visual regression test).

A pixel counts as different when any RGBA channel differs by more than `--channel-tolerance`
(0-255, absorbs tiny driver/rasterizer noise). The test passes when the percentage of different
pixels is <= `--threshold` (fraction, e.g. 0.015 = 1.5%). On failure a `diff.png` is written with
the differing pixels highlighted in red over a dimmed copy of the expected image.

Usage:
    python3 misc/scripts/compare_images.py --expected golden.png --actual output.png
        [--threshold 0.015] [--channel-tolerance 8] [--diff-output diff.png] [--json]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from typing import Optional, Sequence

from PIL import Image, ImageChops

DEFAULT_THRESHOLD = 0.015
DEFAULT_CHANNEL_TOLERANCE = 8


@dataclass
class CompareResult:
    passed: bool
    diff_ratio: float  # Fraction of pixels considered different (0.0 - 1.0).
    mae: float  # Mean absolute error over all RGBA channels (0 - 255).
    rmse: float  # Root mean square error over all RGBA channels (0 - 255).
    size_mismatch: bool
    diff_image: Optional[str] = None

    @property
    def diff_percent(self) -> float:
        return self.diff_ratio * 100.0


def compare(
    expected: Image.Image,
    actual: Image.Image,
    threshold: float = DEFAULT_THRESHOLD,
    channel_tolerance: int = DEFAULT_CHANNEL_TOLERANCE,
    diff_output: Optional[str] = None,
) -> CompareResult:
    expected = expected.convert("RGBA")
    actual = actual.convert("RGBA")
    if expected.size != actual.size:
        return CompareResult(False, 1.0, 255.0, 255.0, True)

    diff = ImageChops.difference(expected, actual)
    pixel_count = expected.size[0] * expected.size[1]

    # Per-pixel maximum channel difference.
    bands = diff.split()
    max_diff = bands[0]
    for band in bands[1:]:
        max_diff = ImageChops.lighter(max_diff, band)
    mask = max_diff.point(lambda v: 255 if v > channel_tolerance else 0)
    different_pixels = mask.histogram()[255]
    diff_ratio = different_pixels / pixel_count

    channel_sum = 0
    channel_sq_sum = 0
    for band in bands:
        for value, count in enumerate(band.histogram()):
            channel_sum += value * count
            channel_sq_sum += value * value * count
    samples = pixel_count * len(bands)
    mae = channel_sum / samples
    rmse = math.sqrt(channel_sq_sum / samples)

    passed = diff_ratio <= threshold
    diff_path = None
    if not passed and diff_output:
        dimmed = Image.blend(expected.convert("RGB"), Image.new("RGB", expected.size, (0, 0, 0)), 0.6)
        red = Image.new("RGB", expected.size, (255, 0, 0))
        highlighted = Image.composite(red, dimmed, mask)
        os.makedirs(os.path.dirname(os.path.abspath(diff_output)), exist_ok=True)
        highlighted.save(diff_output)
        diff_path = diff_output

    return CompareResult(passed, diff_ratio, mae, rmse, False, diff_path)


def compare_files(expected_path: str, actual_path: str, **kwargs) -> CompareResult:
    with Image.open(expected_path) as expected, Image.open(actual_path) as actual:
        return compare(expected, actual, **kwargs)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compare a rendered image against a golden image.")
    parser.add_argument("--expected", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Max fraction of different pixels.")
    parser.add_argument("--channel-tolerance", type=int, default=DEFAULT_CHANNEL_TOLERANCE)
    parser.add_argument("--diff-output", help="Where to write the diff image on failure (default: <actual>_diff.png).")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    for path in (args.expected, args.actual):
        if not os.path.isfile(path):
            print(f"ERROR: Image not found: {path}", file=sys.stderr)
            return 2

    diff_output = args.diff_output or os.path.splitext(args.actual)[0] + "_diff.png"
    result = compare_files(
        args.expected,
        args.actual,
        threshold=args.threshold,
        channel_tolerance=args.channel_tolerance,
        diff_output=diff_output,
    )
    if args.json:
        print(json.dumps(asdict(result) | {"diff_percent": result.diff_percent}, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        detail = "size mismatch" if result.size_mismatch else f"{result.diff_percent:.3f}% pixels differ"
        print(
            f"[{status}] {detail} (threshold {args.threshold * 100:.2f}%), MAE {result.mae:.2f}, RMSE {result.rmse:.2f}"
        )
        if result.diff_image:
            print(f"Diff image: {result.diff_image}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
