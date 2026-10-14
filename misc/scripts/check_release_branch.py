#!/usr/bin/env python3
"""Check that a Bamboo release branch respects the feature-freeze policy.

Checks (see docs/policies/release_freeze_policy.md):
  1. The branch is named `release/<major>.<minor>`.
  2. `version.py` matches the branch: bamboo_major.bamboo_minor == <major>.<minor>, and
     `bamboo_prerelease` is `beta.N`, `rc.N` or "" (final). `alpha.N` is not allowed after the freeze.
  3. No feature commit landed on the branch after it was cut from `--base` (subjects starting with
     `feat:`, `feature:` or `[Bamboo Feature]`); only fixes are allowed.

Usage:
    python3 misc/scripts/check_release_branch.py [--branch release/0.1] [--base bamboo/main] [--repo .]
"""

from __future__ import annotations

import argparse
import os
import re
import runpy
import subprocess
import sys
from typing import Any, Optional, Sequence

BRANCH_RE = re.compile(r"^release/(\d+)\.(\d+)$")
PRERELEASE_RE = re.compile(r"^(?:(beta|rc)\.(\d+))?$")
FEATURE_COMMIT_RE = re.compile(r"^(feat(\(.+\))?!?:|feature:|\[Bamboo Feature\])", re.IGNORECASE)


def check_branch_name(branch: str) -> tuple[Optional[tuple[int, int]], list[str]]:
    match = BRANCH_RE.match(branch)
    if not match:
        return None, [f"branch '{branch}' does not follow the 'release/<major>.<minor>' convention"]
    return (int(match.group(1)), int(match.group(2))), []


def check_version(version: dict[str, Any], line: Optional[tuple[int, int]]) -> list[str]:
    errors = []
    prerelease = str(version.get("bamboo_prerelease", ""))
    if not PRERELEASE_RE.match(prerelease):
        errors.append(
            f"bamboo_prerelease '{prerelease}' is not allowed after the feature freeze (use beta.N, rc.N or '')"
        )
    if line is not None:
        current = (int(version.get("bamboo_major", -1)), int(version.get("bamboo_minor", -1)))
        if current != line:
            errors.append(f"version.py is {current[0]}.{current[1]} but the branch is release/{line[0]}.{line[1]}")
    # The Godot base version must stay untouched (GDExtension compatibility).
    if int(version.get("major", 0)) != 4:
        errors.append("version.py `major` must stay at the Godot base version (4)")
    return errors


def find_feature_commits(subjects: Sequence[str]) -> list[str]:
    return [s for s in subjects if FEATURE_COMMIT_RE.match(s.strip())]


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def commit_subjects(repo: str, base: str, branch: str) -> list[str]:
    try:
        merge_base = git(repo, "merge-base", base, branch).strip()
    except subprocess.CalledProcessError:
        return []
    return [line for line in git(repo, "log", "--format=%s", f"{merge_base}..{branch}").splitlines() if line]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Bamboo release branch against the feature-freeze policy.")
    parser.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    parser.add_argument("--branch", help="Branch to check (default: current branch).")
    parser.add_argument("--base", default="bamboo/main", help="Development branch the release was cut from.")
    parser.add_argument("--version-file", help="Default: <repo>/version.py")
    args = parser.parse_args(argv)

    branch = args.branch or git(args.repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    version = runpy.run_path(args.version_file or os.path.join(args.repo, "version.py"))

    line, errors = check_branch_name(branch)
    errors += check_version(version, line)
    features = find_feature_commits(commit_subjects(args.repo, args.base, branch)) if line else []
    errors += [f"feature commit on a frozen branch: '{s}'" for s in features]

    prerelease = version.get("bamboo_prerelease", "")
    label = f"{version.get('bamboo_major')}.{version.get('bamboo_minor')}.{version.get('bamboo_patch')}"
    print(f"Branch: {branch} · Bamboo {label}{'-' + prerelease if prerelease else ''}")
    for error in errors:
        print(f"ERROR: {error}")
    print("Release branch check PASSED." if not errors else "Release branch check FAILED.")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
