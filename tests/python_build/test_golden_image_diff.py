#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Unit tests for misc/scripts/compare_images.py (golden-image comparison).

Run: python3 -m unittest tests/python_build/test_golden_image_diff.py
"""

import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "misc", "scripts"))

import compare_images as ci  # noqa: E402


def solid(color, size=(64, 64)):
    return Image.new("RGBA", size, color)


class TestCompareImages(unittest.TestCase):
    def test_identical_images_pass_with_zero_error(self):
        result = ci.compare(solid((120, 60, 30, 255)), solid((120, 60, 30, 255)))
        self.assertTrue(result.passed)
        self.assertEqual(result.diff_percent, 0.0)
        self.assertEqual(result.mae, 0.0)

    def test_black_vs_white_fails_with_full_difference(self):
        result = ci.compare(solid((0, 0, 0, 255)), solid((255, 255, 255, 255)))
        self.assertFalse(result.passed)
        self.assertEqual(result.diff_percent, 100.0)

    def test_few_pixels_below_threshold_pass(self):
        expected = solid((0, 0, 0, 255), (100, 100))
        actual = expected.copy()
        for x in range(10):  # 10 / 10000 = 0.1% < 1.5%
            actual.putpixel((x, 0), (255, 255, 255, 255))
        result = ci.compare(expected, actual, threshold=0.015)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.diff_percent, 0.1)

    def test_many_pixels_above_threshold_fail(self):
        expected = solid((0, 0, 0, 255), (100, 100))
        actual = expected.copy()
        for x in range(100):
            for y in range(2):  # 200 / 10000 = 2% > 1.5%
                actual.putpixel((x, y), (255, 255, 255, 255))
        self.assertFalse(ci.compare(expected, actual, threshold=0.015).passed)

    def test_channel_tolerance_absorbs_small_noise(self):
        result = ci.compare(solid((100, 100, 100, 255)), solid((104, 97, 100, 255)), channel_tolerance=8)
        self.assertTrue(result.passed)
        self.assertEqual(result.diff_percent, 0.0)
        self.assertGreater(result.mae, 0.0)

    def test_size_mismatch_fails(self):
        result = ci.compare(solid((0, 0, 0, 255), (64, 64)), solid((0, 0, 0, 255), (32, 32)))
        self.assertFalse(result.passed)
        self.assertTrue(result.size_mismatch)

    def test_diff_image_written_on_failure_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = os.path.join(tmp, "diff.png")
            ci.compare(solid((0, 0, 0, 255)), solid((0, 0, 0, 255)), diff_output=diff_path)
            self.assertFalse(os.path.exists(diff_path))

            expected = solid((0, 0, 0, 255), (10, 10))
            actual = expected.copy()
            for x in range(10):
                actual.putpixel((x, 5), (255, 255, 255, 255))
            result = ci.compare(expected, actual, threshold=0.0, diff_output=diff_path)
            self.assertEqual(result.diff_image, diff_path)
            with Image.open(diff_path) as diff:
                self.assertEqual(diff.getpixel((3, 5)), (255, 0, 0))  # Differing pixel is red.
                self.assertNotEqual(diff.getpixel((3, 0)), (255, 0, 0))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, "a.png")
            b = os.path.join(tmp, "b.png")
            solid((0, 0, 0, 255)).save(a)
            solid((255, 255, 255, 255)).save(b)
            with redirect_stdout(StringIO()):
                self.assertEqual(ci.main(["--expected", a, "--actual", a]), 0)
                self.assertEqual(ci.main(["--expected", a, "--actual", b]), 1)
            self.assertTrue(os.path.exists(os.path.join(tmp, "b_diff.png")))


if __name__ == "__main__":
    unittest.main()
