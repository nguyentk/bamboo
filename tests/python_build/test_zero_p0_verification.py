#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Release gate: no open P0 issue, and release commits reference a ticket.

Run: python3 -m unittest tests/python_build/test_zero_p0_verification.py
The live check against GitHub runs when BAMBOO_CHECK_GITHUB=1 (needs network; GITHUB_TOKEN for
private repositories). The logic is always tested with fixtures.
"""

import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import check_open_issues as coi  # noqa: E402

FIXTURE = [
    {
        "number": 1,
        "title": "Crash on export",
        "state": "open",
        "labels": [{"name": "P0-Blocker"}, {"name": "area/platform"}],
    },
    {"number": 2, "title": "Wrong tooltip", "state": "open", "labels": [{"name": "P2-Normal"}]},
    {"number": 3, "title": "Fixed crash", "state": "closed", "labels": [{"name": "P0-Blocker"}]},
    {"number": 4, "title": "PR fixing #1", "state": "open", "labels": [{"name": "P0-Blocker"}], "pull_request": {}},
    {"number": 5, "title": "Physics jitter", "state": "open", "labels": ["P1-High"]},
]


def run(*args):
    with redirect_stdout(StringIO()) as out, redirect_stderr(StringIO()) as err:
        code = coi.main(list(args))
    return code, out.getvalue() + err.getvalue()


class TestIssueFiltering(unittest.TestCase):
    def test_open_p0_only_counts_open_issues(self):
        grouped = coi.filter_issues(FIXTURE, ["P0", "P1"])
        self.assertEqual([i["number"] for i in grouped["P0"]], [1])
        self.assertEqual([i["number"] for i in grouped["P1"]], [5])

    def test_zero_p0_list_is_empty(self):
        resolved = [dict(i, state="closed") if i["number"] == 1 else i for i in FIXTURE]
        self.assertEqual(coi.filter_issues(resolved, ["P0"])["P0"], [])

    def test_priority_parsing(self):
        self.assertEqual(coi.parse_priorities("p0, P1"), ["P0", "P1"])
        with self.assertRaises(ValueError):
            coi.parse_priorities("P5")

    def test_cli_with_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "issues.json")
            with open(path, "w") as f:
                json.dump(FIXTURE, f)
            code, output = run("--priority", "P0", "--from-json", path, "--fail-if-open")
            self.assertEqual(code, 1)
            self.assertIn("P0-Blocker: 1 open", output)
            self.assertIn("#1 Crash on export", output)
            code, _ = run("--priority", "P3", "--from-json", path, "--fail-if-open")
            self.assertEqual(code, 0)


class TestTicketReferences(unittest.TestCase):
    def test_commits_must_reference_a_ticket(self):
        subjects = [
            "[Bamboo Fix] Fix crash on export (#12)",
            "fix: physics jitter BAMBOO-34",
            "fix: typo",
            "[Bamboo Release] Bump version to 0.1.0-rc.1",
        ]
        self.assertEqual(
            coi.commits_without_ticket(subjects), ["fix: typo", "[Bamboo Release] Bump version to 0.1.0-rc.1"]
        )


@unittest.skipUnless(os.environ.get("BAMBOO_CHECK_GITHUB"), "Set BAMBOO_CHECK_GITHUB=1 to query GitHub")
class TestLiveRepository(unittest.TestCase):
    def test_no_open_p0_issue(self):
        repo = coi.repo_from_git_remote()
        self.assertIsNotNone(repo)
        grouped = coi.filter_issues(coi.fetch_issues(repo, ["P0-Blocker"]), ["P0"])
        self.assertEqual(grouped["P0"], [], "Open P0 issues block the release")


if __name__ == "__main__":
    unittest.main()
