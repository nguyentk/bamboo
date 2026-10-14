#!/usr/bin/env python3
# BAMBOO: Bamboo build tooling test.
"""Checks of the editor translation template (editor/translations/editor.pot) and translations.

Run: python3 -m unittest tests/python_build/test_localization_pot.py
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "misc", "scripts"))

import make_pot  # noqa: E402

POT_PATH = os.path.join(REPO_ROOT, "editor", "translations", "editor.pot")
PO_DIR = os.path.join(REPO_ROOT, "editor", "translations", "editor")
SPECIFIER_RE = re.compile(r"%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[sdifuxXc]")
# Placeholder mismatches inherited from upstream Godot translations, other than Vietnamese (which
# Bamboo maintains and must have none). Bamboo must not add new ones; lower this number when
# upstream fixes are merged.
UPSTREAM_MISMATCH_BASELINE = 31


def parse_po(text):
    """Return a list of entries {ctx, id, plural, str: [..], flags, obsolete} from PO text."""
    entries, current, field = [], None, None

    def finish():
        if current is not None and (current["id"] or current["str"]):
            entries.append(current)

    def new_entry():
        return {"ctx": None, "id": "", "plural": None, "str": [], "flags": "", "obsolete": False}

    for raw in text.splitlines():
        line = raw.strip()
        obsolete = line.startswith("#~")
        if obsolete:
            line = line[2:].strip()
        if not line:
            finish()
            current, field = None, None
            continue
        if line.startswith("#,"):
            current = current or new_entry()
            current["flags"] += line[2:]
            continue
        if line.startswith("#"):
            current = current or new_entry()
            continue
        current = current or new_entry()
        current["obsolete"] |= obsolete
        match = re.match(r'^(msgctxt|msgid_plural|msgid|msgstr(?:\[(\d+)\])?)\s+"(.*)"$', line)
        if match:
            keyword, value = match.group(1), match.group(3)
            if keyword == "msgctxt":
                current["ctx"], field = value, "ctx"
            elif keyword == "msgid":
                current["id"], field = value, "id"
            elif keyword == "msgid_plural":
                current["plural"], field = value, "plural"
            else:
                current["str"].append(value)
                field = "str"
        elif line.startswith('"') and line.endswith('"') and field:
            value = line[1:-1]
            if field == "str":
                current["str"][-1] += value
            else:
                current[field] = (current[field] or "") + value
        else:
            raise ValueError(f"Invalid PO line: {raw!r}")
    finish()
    return entries


def specifiers(text):
    return sorted(SPECIFIER_RE.findall(text))


def placeholder_mismatches(entries):
    result = []
    for e in entries:
        if e["obsolete"] or "fuzzy" in e["flags"] or not e["id"]:
            continue
        for translation in e["str"]:
            if translation and specifiers(e["id"]) != specifiers(translation) and (
                e["plural"] is None or specifiers(e["plural"]) != specifiers(translation)
            ):
                result.append((e["id"], translation))
    return result


class TestPotTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(POT_PATH, encoding="utf-8") as f:
            cls.text = f.read()
        cls.entries = parse_po(cls.text)

    def test_pot_is_up_to_date_with_sources(self):
        regenerated = make_pot.format_pot(make_pot.collect())
        self.assertEqual(self.text, regenerated, "Run: python3 misc/scripts/make_pot.py")

    def test_syntax_and_empty_translations(self):
        self.assertGreater(len(self.entries), 5000)
        header = self.entries[0]
        self.assertEqual(header["id"], "")
        for e in self.entries[1:]:
            self.assertTrue(e["id"])
            self.assertTrue(all(s == "" for s in e["str"]), e["id"])
            self.assertEqual(len(e["str"]), 2 if e["plural"] is not None else 1, e["id"])

    def test_no_duplicate_msgids(self):
        counts = Counter((e["ctx"], e["id"]) for e in self.entries[1:])
        duplicates = [key for key, count in counts.items() if count > 1]
        self.assertEqual(duplicates, [])

    def test_bamboo_strings_present(self):
        ids = {e["id"] for e in self.entries}
        for msgid in ("About Bamboo Engine...", "About Bamboo Engine", "Files have been modified outside Bamboo", "%s - Bamboo Engine"):
            self.assertIn(msgid, ids)
        self.assertNotIn("About Godot...", ids)

    @unittest.skipIf(shutil.which("msgfmt") is None, "GNU gettext msgfmt not installed")
    def test_msgfmt_check(self):
        proc = subprocess.run(["msgfmt", "--check", "-o", os.devnull, POT_PATH], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestExtractor(unittest.TestCase):
    def test_extracts_context_plural_and_concatenation(self):
        source = '''
            label->set_text(TTR("Hello " "World"));
            x = TTRC("Open", "Menu");
            y = TTRN("%d file", "%d files", count);
            z = RTRN("%d node", "%d nodes", n, "Tree");
            w = TTR(U"Size: %d × %d");
            v = TTR(dynamic_text);  // Not a literal, skipped.
        '''
        found = [(msgid, ctx, plural) for _, msgid, ctx, plural in make_pot.extract_from_text(source)]
        self.assertEqual(
            found,
            [
                ("Hello World", "", ""),
                ("Open", "Menu", ""),
                ("%d file", "", "%d files"),
                ("%d node", "Tree", "%d nodes"),
                ("Size: %d × %d", "", ""),
            ],
        )

    def test_pot_format_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "src.cpp")
            entries = make_pot.OrderedDict()
            entry = make_pot.Entry("A \\\"quoted\\\" %s", "Ctx")
            entry.locations.append("src.cpp:1")
            entries[("Ctx", entry.msgid)] = entry
            parsed = parse_po(make_pot.format_pot(entries))
            self.assertEqual(parsed[1]["ctx"], "Ctx")
            self.assertEqual(parsed[1]["id"], 'A \\"quoted\\" %s')


class TestTranslations(unittest.TestCase):
    def test_vietnamese_placeholders_match(self):
        with open(os.path.join(PO_DIR, "vi.po"), encoding="utf-8") as f:
            self.assertEqual(placeholder_mismatches(parse_po(f.read())), [])

    def test_no_new_placeholder_mismatches(self):
        total = 0
        for path in sorted(glob.glob(os.path.join(PO_DIR, "*.po"))):
            if os.path.basename(path) == "vi.po":
                continue
            with open(path, encoding="utf-8") as f:
                total += len(placeholder_mismatches(parse_po(f.read())))
        self.assertLessEqual(total, UPSTREAM_MISMATCH_BASELINE)

    def test_mismatch_detection(self):
        entries = parse_po('msgid "%s of %d"\nmsgstr "%d / %s"\n\nmsgid "Plain"\nmsgstr "Có %s"\n')
        self.assertEqual(placeholder_mismatches(entries), [("Plain", "Có %s")])


if __name__ == "__main__":
    unittest.main()
