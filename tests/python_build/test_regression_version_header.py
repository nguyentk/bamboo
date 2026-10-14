#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""[Regression] BAMBOO-REG-1: the generated version header must only contain valid preprocessor lines.

A `# BAMBOO:` comment inserted into the `version_info_builder` template once produced
`# BAMBOO: ...` in core/version_generated.gen.h ("invalid preprocessing directive").

Run: python3 -m unittest tests/python_build/test_regression_version_header.py
"""

import os
import re
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

import methods  # noqa: E402
from core import core_builders  # noqa: E402

VALID_LINE = re.compile(r"^(#(define|pragma|include|ifndef|ifdef|endif|if|else|elif)\b.*|//.*|/\*.*|\s*\*.*|)$")


class _Target:
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path


class _Source:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data


class TestRegressionVersionHeader(unittest.TestCase):
    def generate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "version_generated.gen.h")
            core_builders.version_info_builder(
                [_Target(path)], [_Source(methods.get_version_info("", silent=True))], None
            )
            with open(path, encoding="utf-8") as f:
                return f.read()

    def test_only_valid_preprocessor_lines(self):
        for number, line in enumerate(self.generate().splitlines(), 1):
            self.assertRegex(line, VALID_LINE, f"line {number} is not valid in a C header: {line!r}")

    def test_bamboo_macros_are_generated(self):
        header = self.generate()
        for macro in ("MAJOR", "MINOR", "PATCH", "PRERELEASE", "CODENAME", "STRING"):
            self.assertIn(f"#define BAMBOO_VERSION_{macro} ", header)


if __name__ == "__main__":
    unittest.main()
