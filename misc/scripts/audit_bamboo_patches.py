#!/usr/bin/env python3
"""Audit Bamboo patches to the Godot source tree.

Every change Bamboo makes to upstream Godot code must be marked with a `BAMBOO:` comment
(`// BAMBOO: <reason>` in C/C++, `# BAMBOO: <reason>` in Python/SCons) so that upstream rebases
stay manageable. This script diffs the tree against the upstream base and reports every changed
hunk without a nearby `BAMBOO:` marker.

A hunk counts as tagged when a `BAMBOO:` marker is in its added lines or within `--window` lines
before or after it in the new file (one marker can document a whole function). A new file
counts as tagged when it contains a marker anywhere.

Usage:
    python3 misc/scripts/audit_bamboo_patches.py [--base REF] [--committed-only]
        [--output docs/rebase_reports/patch_audit.md] [--window 15] [--no-fail]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional, Sequence

# Upstream Godot commit Bamboo was forked from (used when `upstream/master` is not fetched).
FORK_BASE = "c24bf5d933"

# Upstream directories/files whose changes must be tagged.
SCOPE_DIRS = ("core/", "servers/", "scene/", "editor/", "main/", "platform/", "drivers/", "modules/", "tests/")
SCOPE_ROOT_FILES = ("SConstruct", "methods.py", "platform_methods.py", "version.py", "scu_builders.py")
CODE_EXTENSIONS = (".cpp", ".h", ".hpp", ".c", ".cc", ".mm", ".m", ".inc", ".glsl", ".py")
EXCLUDED_PARTS = ("thirdparty/", ".gen.", "/doc_classes/", "editor/translations/", "tests/data/")

MARKER = re.compile(r"(//|#|/\*|\*)\s*BAMBOO:")
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class Hunk:
    path: str
    new_start: int
    new_count: int
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    tagged: bool = False


@dataclass
class FileReport:
    path: str
    new_file: bool
    hunks: list[Hunk] = field(default_factory=list)

    @property
    def untagged(self) -> list[Hunk]:
        return [h for h in self.hunks if not h.tagged]


def in_scope(path: str) -> bool:
    if any(part in path for part in EXCLUDED_PARTS):
        return False
    name = os.path.basename(path)
    if path in SCOPE_ROOT_FILES:
        return True
    if not path.startswith(SCOPE_DIRS):
        return False
    return name == "SCsub" or name.endswith(CODE_EXTENSIONS)


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def resolve_base(repo: str, base: Optional[str]) -> str:
    if base:
        return base
    try:
        return git(repo, "merge-base", "HEAD", "upstream/master").strip()
    except subprocess.CalledProcessError:
        return FORK_BASE


def parse_diff(diff_text: str) -> dict[str, list[Hunk]]:
    hunks: dict[str, list[Hunk]] = {}
    path = None
    current: Optional[Hunk] = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            current = None
            continue
        if line.startswith("--- ") or line.startswith("diff --git"):
            continue
        match = HUNK_HEADER.match(line)
        if match and path:
            current = Hunk(path, int(match.group(3)), int(match.group(4) or 1))
            hunks.setdefault(path, []).append(current)
            continue
        if current is None:
            continue
        if line.startswith("+"):
            current.added.append(line[1:])
        elif line.startswith("-"):
            current.removed.append(line[1:])
    return hunks


def read_lines(repo: str, path: str) -> list[str]:
    try:
        with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def is_tagged(hunk: Hunk, file_lines: list[str], window: int) -> bool:
    if any(MARKER.search(line) for line in hunk.added):
        return True
    start = max(0, hunk.new_start - 1 - window)
    end = min(len(file_lines), hunk.new_start - 1 + max(hunk.new_count, 1) + window)
    return any(MARKER.search(line) for line in file_lines[start:end])


def audit(repo: str, base: str, committed_only: bool = False, window: int = 15) -> list[FileReport]:
    target = [f"{base}..HEAD"] if committed_only else [base]
    diff = git(repo, "diff", "-U0", "--no-color", "--no-renames", *target, "--")
    added_files = set(git(repo, "diff", "--name-only", "--diff-filter=A", "--no-renames", *target, "--").split())
    if not committed_only:
        added_files |= set(git(repo, "ls-files", "--others", "--exclude-standard").split())

    reports: dict[str, FileReport] = {}
    for path, hunks in parse_diff(diff).items():
        if not in_scope(path) or path in added_files:
            continue
        lines = read_lines(repo, path)
        for hunk in hunks:
            hunk.tagged = is_tagged(hunk, lines, window)
        reports[path] = FileReport(path, False, hunks)

    for path in sorted(added_files):
        if not in_scope(path):
            continue
        lines = read_lines(repo, path)
        hunk = Hunk(path, 1, len(lines), added=lines, tagged=any(MARKER.search(line) for line in lines))
        reports[path] = FileReport(path, True, [hunk])
    return [reports[p] for p in sorted(reports)]


def format_report(reports: Sequence[FileReport], base: str) -> str:
    hunks = [h for r in reports for h in r.hunks]
    untagged = [h for h in hunks if not h.tagged]
    added = sum(len(h.added) for h in hunks)
    removed = sum(len(h.removed) for h in hunks)
    coverage = 100.0 * (len(hunks) - len(untagged)) / len(hunks) if hunks else 100.0
    lines = [
        "# Bamboo patch audit",
        "",
        f"- Base: `{base}`",
        f"- Files touched: **{len(reports)}** ({sum(r.new_file for r in reports)} new)",
        f"- Patches (hunks): **{len(hunks)}**, lines added: {added}, removed: {removed}",
        f"- Tagged with `BAMBOO:`: **{len(hunks) - len(untagged)}/{len(hunks)} ({coverage:.1f}%)**",
        "",
        "| File | New | Hunks | Untagged |",
        "| :--- | :---: | ---: | ---: |",
    ]
    for r in reports:
        lines.append(f"| `{r.path}` | {'yes' if r.new_file else ''} | {len(r.hunks)} | {len(r.untagged)} |")
    if untagged:
        lines += ["", "## Untagged patches", ""]
        for h in untagged:
            preview = next((line.strip() for line in h.added if line.strip()), "(removed lines only)")
            lines.append(f"- `{h.path}:{h.new_start}` — `{preview[:100]}`")
    else:
        lines += ["", "All patches are tagged."]
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit `BAMBOO:` tags on patches to upstream Godot code.")
    parser.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    parser.add_argument(
        "--base", help=f"Upstream base ref (default: merge-base with upstream/master, else {FORK_BASE})."
    )
    parser.add_argument("--committed-only", action="store_true", help="Ignore uncommitted and untracked changes.")
    parser.add_argument("--window", type=int, default=15)
    parser.add_argument("--output", help="Write the Markdown report to this file.")
    parser.add_argument("--no-fail", action="store_true", help="Exit 0 even when untagged patches exist.")
    args = parser.parse_args(argv)

    base = resolve_base(args.repo, args.base)
    reports = audit(args.repo, base, args.committed_only, args.window)
    text = format_report(reports, base)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    untagged = sum(len(r.untagged) for r in reports)
    return 0 if untagged == 0 or args.no_fail else 1


if __name__ == "__main__":
    sys.exit(main())
