#!/usr/bin/env python3
"""Evaluate the Bamboo Go/No-go release criteria from evidence in the repository.

Automatic checks use files in the repository; criteria that need external systems (CI runs,
physical devices, Apple notarization service) must be confirmed in an evidence JSON file:
    {"ci_green": {"ok": true, "evidence": "https://github.com/.../actions/runs/123"}, ...}

Criteria (PROMPT_TL_GO_NOGO_AND_RELEASE.md):
  1 ci_green            CI green on the 6 platforms                       evidence file
  2 zero_p0             0 open P0 issues                                  evidence file or --check-github
  3 benchmark_baseline  benchmark baseline with >= 6 scenarios            benchmarks/baseline.json
  4 golden_images       golden images for Forward+, Mobile, Compatibility tests/visual/golden/
  5 ci_build_time       cached editor CI build <= 20 minutes              evidence file
  6 dogfood_devices     dogfood game runs on PC and a real Android device evidence file
  7 patch_tags          100% of core patches tagged `BAMBOO:`             audit_bamboo_patches.py
  8 rebase_rehearsal    rebase rehearsal report                           docs/rebase_reports/
  9 notarized_dmg       macOS .dmg notarized (Gatekeeper accepts it)      spctl on bin/Bamboo_v*_macOS.dmg
Plus, for the final release: stable version (bamboo_prerelease == "") and non-empty release notes.

Usage:
    python3 misc/scripts/release_readiness.py [--evidence evidence.json] [--final] [--json]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import runpy
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Optional, Sequence

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

MANUAL_CRITERIA = {
    "ci_green": "CI green on Windows, macOS, Linux, Android, iOS and Web",
    "zero_p0": "0 open P0 issues",
    "ci_build_time": "Cached editor CI build <= 20 minutes",
    "dogfood_devices": "Dogfood game runs on PC and a real Android device",
}


@dataclass
class Criterion:
    key: str
    title: str
    ok: bool
    detail: str


def check_benchmark_baseline(root: str) -> Criterion:
    path = os.path.join(root, "benchmarks", "baseline.json")
    title = "Benchmark baseline with >= 6 scenarios"
    if not os.path.isfile(path):
        return Criterion("benchmark_baseline", title, False, "benchmarks/baseline.json missing")
    with open(path, encoding="utf-8") as f:
        count = len(json.load(f).get("benchmarks", []))
    return Criterion("benchmark_baseline", title, count >= 6, f"{count} scenarios")


def check_golden_images(root: str) -> Criterion:
    golden = os.path.join(root, "tests", "visual", "golden")
    found = {m: len(glob.glob(os.path.join(golden, f"*_{m}.png"))) for m in ("forward_plus", "mobile", "gl_compatibility")}
    ok = all(count > 0 for count in found.values())
    return Criterion("golden_images", "Golden images for the 3 renderers", ok, ", ".join(f"{k}: {v}" for k, v in found.items()))


def check_patch_tags(root: str) -> Criterion:
    import audit_bamboo_patches as audit

    try:
        reports = audit.audit(root, audit.resolve_base(root, None))
    except subprocess.CalledProcessError as e:
        return Criterion("patch_tags", "100% of core patches tagged", False, f"audit failed: {e}")
    hunks = sum(len(r.hunks) for r in reports)
    untagged = sum(len(r.untagged) for r in reports)
    return Criterion("patch_tags", "100% of core patches tagged", untagged == 0, f"{hunks - untagged}/{hunks} tagged")


def check_rebase_rehearsal(root: str) -> Criterion:
    reports = glob.glob(os.path.join(root, "docs", "rebase_reports", "rebase_rehearsal_*.md"))
    return Criterion("rebase_rehearsal", "Upstream rebase rehearsal report", bool(reports), ", ".join(os.path.basename(r) for r in reports) or "none")


def check_notarized_dmg(root: str, runner: Callable = subprocess.run) -> Criterion:
    title = "Notarized macOS .dmg"
    dmgs = sorted(glob.glob(os.path.join(root, "bin", "Bamboo_v*_macOS.dmg")))
    if not dmgs:
        return Criterion("notarized_dmg", title, False, "no bin/Bamboo_v*_macOS.dmg")
    proc = runner(["spctl", "-a", "-vvv", "-t", "install", dmgs[-1]], capture_output=True, text=True)
    output = (proc.stdout + proc.stderr).strip().replace("\n", " ")
    ok = proc.returncode == 0 and "Notarized" in output
    return Criterion("notarized_dmg", title, ok, f"{os.path.basename(dmgs[-1])}: {output[:120]}")


def check_stable_version(version: Dict) -> Criterion:
    prerelease = str(version.get("bamboo_prerelease", ""))
    label = f"{version.get('bamboo_major')}.{version.get('bamboo_minor')}.{version.get('bamboo_patch')}"
    ok = prerelease == ""
    return Criterion("stable_version", "version.py marks a stable release", ok, label + (f"-{prerelease}" if prerelease else ""))


def check_release_notes(root: str, version: Dict) -> Criterion:
    pattern = os.path.join(root, "docs", "release_notes", f"Release_Notes_{version.get('bamboo_major')}.{version.get('bamboo_minor')}.{version.get('bamboo_patch')}_*.md")
    notes = sorted(glob.glob(pattern))
    ok = bool(notes) and os.path.getsize(notes[0]) > 0
    return Criterion("release_notes", "Release notes", ok, os.path.basename(notes[0]) if notes else "missing")


def check_manual(evidence: Dict) -> List[Criterion]:
    result = []
    for key, title in MANUAL_CRITERIA.items():
        item = evidence.get(key) or {}
        ok = bool(item.get("ok")) and bool(item.get("evidence"))
        detail = item.get("evidence") or "no evidence provided (confirm in the evidence file)"
        result.append(Criterion(key, title, ok, detail))
    return result


def evaluate(root: str, evidence: Dict, final: bool, runner: Callable = subprocess.run) -> List[Criterion]:
    version = runpy.run_path(os.path.join(root, "version.py"))
    criteria = check_manual(evidence) + [
        check_benchmark_baseline(root),
        check_golden_images(root),
        check_patch_tags(root),
        check_rebase_rehearsal(root),
        check_notarized_dmg(root, runner),
    ]
    if final:
        criteria += [check_stable_version(version), check_release_notes(root, version)]
    return criteria


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Bamboo Go/No-go release criteria.")
    parser.add_argument("--root", default=REPO_ROOT)
    parser.add_argument("--evidence", help="JSON file confirming the manual criteria.")
    parser.add_argument("--final", action="store_true", help="Also require a stable version and release notes.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    evidence = {}
    if args.evidence:
        with open(args.evidence, encoding="utf-8") as f:
            evidence = json.load(f)
    criteria = evaluate(args.root, evidence, args.final)
    go = all(c.ok for c in criteria)
    if args.json:
        print(json.dumps({"go": go, "criteria": [asdict(c) for c in criteria]}, indent=2))
    else:
        for c in criteria:
            print(f"[{'PASS' if c.ok else 'FAIL'}] {c.title}: {c.detail}")
        print("Decision: GO" if go else f"Decision: NO-GO ({sum(not c.ok for c in criteria)} criteria not met)")
    return 0 if go else 1


if __name__ == "__main__":
    sys.exit(main())
