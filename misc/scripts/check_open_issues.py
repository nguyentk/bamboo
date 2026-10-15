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
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional, Sequence

PRIORITY_LABELS: dict[str, str] = {"P0": "P0-Blocker", "P1": "P1-High", "P2": "P2-Normal", "P3": "P3-Low"}
TICKET_RE = re.compile(r"(#\d+|\bBAMBOO-\d+\b)")


def parse_priorities(value: str) -> list[str]:
    priorities = [p.strip().upper() for p in value.split(",") if p.strip()]
    unknown = [p for p in priorities if p not in PRIORITY_LABELS]
    if unknown:
        raise ValueError(f"unknown priorities: {', '.join(unknown)} (expected {', '.join(PRIORITY_LABELS)})")
    return priorities


def label_names(issue: dict[str, Any]) -> list[str]:
    return [label["name"] if isinstance(label, dict) else str(label) for label in issue.get("labels", [])]


def filter_issues(issues: Sequence[dict[str, Any]], priorities: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    """Group open issues (pull requests excluded) by requested priority."""
    result: dict[str, list[dict[str, Any]]] = {p: [] for p in priorities}
    for issue in issues:
        if "pull_request" in issue or str(issue.get("state", "open")).lower() != "open":
            continue
        labels = label_names(issue)
        for priority in priorities:
            if PRIORITY_LABELS[priority] in labels:
                result[priority].append(issue)
    return result


def commits_without_ticket(subjects: Sequence[str]) -> list[str]:
    """Commit subjects that do not reference an issue (`#123` or `BAMBOO-123`)."""
    return [s for s in subjects if not TICKET_RE.search(s)]


def repo_from_git_remote() -> Optional[str]:
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"github\.com[:/]([^/]+/[^/.]+?)(?:\.git)?\s*$", url.strip())
    return match.group(1) if match else None


def github_get(path: str) -> Any:
    """GET a GitHub REST API path. Falls back to `curl` when Python has no CA certificates (SSL error)."""
    url = f"https://api.github.com/{path}"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
    cmd = ["curl", "-sf", "--max-time", "30"]
    for key, value in headers.items():
        cmd += ["-H", f"{key}: {value}"]
    try:
        out = subprocess.run(cmd + [url], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        raise OSError(f"curl failed: {e}") from e
    return json.loads(out)


def issues_enabled(repo: str) -> bool:
    """False when the repository has GitHub Issues disabled (the issues API then just returns [])."""
    return bool(github_get(f"repos/{repo}").get("has_issues", True))


def fetch_issues(repo: str, labels: Sequence[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for label in labels:
        query = urllib.parse.urlencode({"state": "open", "labels": label, "per_page": 100})
        issues += github_get(f"repos/{repo}/issues?{query}")
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
            if not issues_enabled(repo):
                # An empty issue list would look like "0 open P0" although nothing can be tracked.
                print(
                    f"ERROR: GitHub Issues are disabled for {repo}: open P0/P1 issues cannot be verified. "
                    "Enable Issues (Settings -> General -> Features) or pass --from-json.",
                    file=sys.stderr,
                )
                return 2
            issues = fetch_issues(repo, [PRIORITY_LABELS[p] for p in priorities])
        except (OSError, ValueError) as e:
            print(
                f"ERROR: cannot read issues from GitHub ({e}); set GITHUB_TOKEN for private repositories.",
                file=sys.stderr,
            )
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
