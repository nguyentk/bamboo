#!/usr/bin/env python3
"""Extract the translatable editor strings into a gettext template (`editor/translations/editor.pot`).

Scans C++/Objective-C++ sources for the translation macros that use the editor catalog, with
their context/plural arguments:
    TTR/TTRC/RTR/ETR("text"[, "context"])
    TTRN/RTRN/ETRN("singular", "plural", n[, "context"])
Adjacent string literals ("a" "b") are joined. Calls whose first argument is not a literal are
skipped (they translate runtime strings).

Usage:
    python3 misc/scripts/make_pot.py [--output editor/translations/editor.pot]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import OrderedDict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE_DIRS = ["editor", "platform", "modules", "scene", "servers", "main", "core"]
EXTENSIONS = (".cpp", ".h", ".mm")
MACRO_RE = re.compile(r"\b(TTRN|RTRN|ETRN|TTRC|TTR|RTR|ETR)\(")
PLURAL_MACROS = ("TTRN", "RTRN", "ETRN")
# String literal with an optional encoding prefix (U"...", u8"...", L"...").
STRING_RE = re.compile(r'(?:u8|[uUL])?"((?:[^"\\\n]|\\.)*)"')

Key = Tuple[str, str]  # (context, msgid)


class Entry:
    def __init__(self, msgid: str, context: str = "", plural: str = ""):
        self.msgid = msgid
        self.context = context
        self.plural = plural
        self.locations: List[str] = []


def _skip_space(text: str, pos: int) -> int:
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
        elif text.startswith("//", pos):
            end = text.find("\n", pos)
            pos = len(text) if end == -1 else end
        elif text.startswith("/*", pos):
            end = text.find("*/", pos)
            pos = len(text) if end == -1 else end + 2
        else:
            break
    return pos


def _read_literal(text: str, pos: int) -> Tuple[Optional[str], int]:
    """Read one or more adjacent string literals starting at `pos`."""
    parts = []
    pos = _skip_space(text, pos)
    while True:
        match = STRING_RE.match(text, pos)
        if not match:
            break
        parts.append(match.group(1))
        pos = _skip_space(text, match.end())
    return ("".join(parts) if parts else None), pos


def _skip_argument(text: str, pos: int) -> int:
    """Skip a non-literal argument up to the next top-level ',' or ')'."""
    depth = 0
    while pos < len(text):
        char = text[pos]
        if char == '"':
            match = STRING_RE.match(text, pos)
            pos = match.end() if match else pos + 1
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                return pos
            depth -= 1
        elif char == "," and depth == 0:
            return pos
        pos += 1
    return pos


def extract_from_text(text: str) -> Iterable[Tuple[int, str, str, str]]:
    """Yield (line, msgid, context, plural) for every translatable call in `text`."""
    for match in MACRO_RE.finditer(text):
        # Ignore macro definitions and identifiers such as `MY_TTR(`.
        if text[max(0, match.start() - 8) : match.start()].rstrip().endswith("#define"):
            continue
        macro = match.group(1)
        msgid, pos = _read_literal(text, match.end())
        if msgid is None:
            continue
        line = text.count("\n", 0, match.start()) + 1
        context = plural = ""
        if macro in PLURAL_MACROS:
            pos = _skip_space(text, pos)
            if pos < len(text) and text[pos] == ",":
                plural, pos = _read_literal(text, pos + 1)
                plural = plural or ""
                pos = _skip_space(text, pos)
                if pos < len(text) and text[pos] == ",":
                    pos = _skip_argument(text, pos + 1)  # The count argument.
                    if pos < len(text) and text[pos] == ",":
                        context, pos = _read_literal(text, pos + 1)
                        context = context or ""
        else:
            pos = _skip_space(text, pos)
            if pos < len(text) and text[pos] == ",":
                context, pos = _read_literal(text, pos + 1)
                context = context or ""
        yield line, msgid, context, plural


def collect(root: str = REPO_ROOT) -> "OrderedDict[Key, Entry]":
    entries: "OrderedDict[Key, Entry]" = OrderedDict()
    for directory in SOURCE_DIRS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, directory)):
            dirnames[:] = sorted(d for d in dirnames if d not in ("thirdparty", "tests"))
            for filename in sorted(filenames):
                if not filename.endswith(EXTENSIONS):
                    continue
                path = os.path.join(dirpath, filename)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                for line, msgid, context, plural in extract_from_text(text):
                    key = (context, msgid)
                    if key not in entries:
                        entries[key] = Entry(msgid, context, plural)
                    entries[key].locations.append(f"{rel}:{line}")
    return entries


def format_pot(entries: "OrderedDict[Key, Entry]", project: str = "Bamboo Engine editor") -> str:
    lines = [
        f"# {project} translation template.",
        "# Copyright (c) 2026 Bamboo Engine contributors.",
        "# Copyright (c) 2014-present Godot Engine contributors.",
        "# Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.",
        "# This file is distributed under the same license as the Bamboo source code (MIT).",
        "#",
        "#, fuzzy",
        'msgid ""',
        'msgstr ""',
        f'"Project-Id-Version: {project}\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8-bit\\n"',
        "",
    ]
    for entry in entries.values():
        for location in entry.locations:
            lines.append(f"#: {location}")
        if entry.context:
            lines.append(f'msgctxt "{entry.context}"')
        lines.append(f'msgid "{entry.msgid}"')
        if entry.plural:
            lines.append(f'msgid_plural "{entry.plural}"')
            lines += ['msgstr[0] ""', 'msgstr[1] ""']
        else:
            lines.append('msgstr ""')
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract editor strings into a gettext .pot template.")
    parser.add_argument("--output", default=os.path.join(REPO_ROOT, "editor", "translations", "editor.pot"))
    args = parser.parse_args(argv)
    entries = collect()
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(format_pot(entries))
    print(f"Wrote {len(entries)} messages to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
