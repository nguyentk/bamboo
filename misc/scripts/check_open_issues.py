#!/usr/bin/env python3
"""List open GitHub issues by Bamboo priority label (P0-Blocker, P1-High, ...).

Reads the issues from the GitHub REST API (token from GITHUB_TOKEN / GH_TOKEN for private repos)
or from a JSON file exported earlier (`--from-json`, e.g. `gh issue list --json number,title,labels`).

Usage:
    python3 misc/scripts/check_open_issues.py --priority P0[,P1] [--repo owner/name]
        [--from-json issues.json] [--fail-if-open]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Sequence

PRIORITY_LABELS: Dict[str, str] = {"P0": "P0-Blocker", "P1": "P1-High", "P2": "P2-Normal", "P3": "P3-Low"}
TICKET_RE = re.compile(r"(#\d+|\bBAMBOO-\d+\b)")


def parse_priorities(value: str) -> List[str]:
    priorities = [p.strip().upper() for p in value.split(",") if p.strip()]
    unknown = [p for p in priorities if p not in PRIORITY_LABELS]
    if unknown:
        raise ValueError(f"unknown priorities: {', '.join(unknown)} (expected {', '.join(PRIORITY_LABELS)})")
    return priorities


def label_names(issue: dict) -> List[str]:
    return [l["name"] if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]


def filter_issues(issues: Sequence[dict], priorities: Sequence[str]) -> Dict[str, List[dict]]:
    """Group open issues (pull requests excluded) by requested priority."""
    result: Dict[str, List[dict]] = {p: [] for p in priorities}
    for issue in issues:
        if "pull_request" in issue or str(issue.get("state", "open")).lower() != "open":
            continue
        labels = label_names(issue)
        for priority in priorities:
            if PRIORITY_LABELS[priority] in labels:
                result[priority].append(issue)
    return result


def commits_without_ticket(subjects: Sequence[str]) -> List[str]:
    """Commit subjects that do not reference an issue (`#123` or `BAMBOO-123`)."""
    return [s for s in subjects if not TICKET_RE.search(s)]


def repo_from_git_remote() -> Optional[str]:
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"github\.com[:/]([^/]+/[^/.]+?)(?:\.git)?\s*$", url.strip())
    return match.group(1) if match else None


def fetch_issues(repo: str, labels: Sequence[str]) -> List[dict]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    issues: List[dict] = []
    for label in labels:
        query = urllib.parse.urlencode({"state": "open", "labels": label, "per_page": 100})
        request = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues?{query}")
        request.add_header("Accept", "application/vnd.github+json")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(request, timeout=30) as response:
            issues += json.load(response)
    return issues


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="List open Bamboo issues by priority.")
    parser.add_argument("--priority", default="P0", help="Comma-separated priorities, e.g. P0,P1.")
    parser.add_argument("--repo", help="owner/name (default: from the `origin` remote).")
    parser.add_argument("--from-json", help="Read issues from a JSON file instead of the GitHub API.")
    parser.add_argument("--fail-if-open", action="store_true", help="Exit 1 when any matching issue is open.")
    args = parser.parse_args(argv)

    try:
        priorities = parse_priorities(args.priority)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.from_json:
        with open(args.from_json, encoding="utf-8") as f:
            issues = json.load(f)
    else:
        repo = args.repo or repo_from_git_remote()
        if not repo:
            print("ERROR: cannot determine the GitHub repository; pass --repo owner/name.", file=sys.stderr)
            return 2
        try:
            issues = fetch_issues(repo, [PRIORITY_LABELS[p] for p in priorities])
        except OSError as e:
            print(f"ERROR: cannot read issues from GitHub ({e}); set GITHUB_TOKEN for private repositories.", file=sys.stderr)
            return 2

    grouped = filter_issues(issues, priorities)
    total = 0
    for priority in priorities:
        found = grouped[priority]
        total += len(found)
        print(f"{PRIORITY_LABELS[priority]}: {len(found)} open")
        for issue in found:
            print(f"  #{issue.get('number')} {issue.get('title')}")
    return 1 if (args.fail_if_open and total) else 0


if __name__ == "__main__":
    sys.exit(main())
