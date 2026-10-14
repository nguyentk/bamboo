"""Minimal reader for Unity text-serialized YAML (scenes, prefabs, materials).

Unity YAML uses custom tags (`--- !u!<class_id> &<file_id>`) and flow mappings such as
`{x: 0, y: 1, z: 0}` or `{fileID: 2800000, guid: abc, type: 3}`. This reader supports the subset
used by Unity assets without depending on PyYAML.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

_DOC_HEADER = re.compile(r"^--- !u!(\d+) &(-?\d+)(?: stripped)?\s*$")
_FLOW_ITEM = re.compile(r"(\w+):\s*([^,}]*)")


@dataclass
class UnityObject:
    class_id: int
    file_id: int
    type_name: str
    data: dict[str, Any] = field(default_factory=dict)


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return {k: parse_scalar(v) for k, v in _FLOW_ITEM.findall(text[1:-1])}
    if text in ("", "~", "null"):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    return text


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list[str], start: int, indent: int) -> tuple[Any, int]:
    """Parse a block (mapping or sequence) whose lines are indented by `indent`."""
    i = start
    # Skip blank lines.
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return None, i
    if lines[i].lstrip(" ").startswith("- "):
        result_list: list[Any] = []
        while (
            i < len(lines)
            and lines[i].strip()
            and _indent(lines[i]) == indent
            and lines[i].lstrip(" ").startswith("- ")
        ):
            item_text = lines[i].lstrip(" ")[2:]
            item_indent = indent + 2
            # Treat "- key: value" as a mapping whose first line is the item line.
            if re.match(r"^[\w.]+:", item_text) and not item_text.startswith("{"):
                sub_lines = [" " * item_indent + item_text]
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or _indent(lines[j]) >= item_indent):
                    sub_lines.append(lines[j])
                    j += 1
                value, _ = _parse_block(sub_lines, 0, item_indent)
                result_list.append(value)
                i = j
            else:
                result_list.append(parse_scalar(item_text))
                i += 1
        return result_list, i

    result: dict[str, Any] = {}
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        current = _indent(line)
        if current < indent:
            break
        if current > indent:
            i += 1
            continue
        key, _, rest = line.strip().partition(":")
        rest = rest.strip()
        if rest:
            result[key] = parse_scalar(rest)
            i += 1
        else:
            # Nested block: sequences may share the parent indentation in Unity YAML.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and (
                _indent(lines[j]) > indent or (_indent(lines[j]) == indent and lines[j].lstrip(" ").startswith("- "))
            ):
                value, i = _parse_block(lines, j, _indent(lines[j]))
                result[key] = value
            else:
                result[key] = None
                i += 1
    return result, i


def parse_documents(text: str) -> list[UnityObject]:
    objects: list[UnityObject] = []
    current_header: Optional[re.Match[str]] = None
    body: list[str] = []

    def flush() -> None:
        if current_header is None or not body:
            return
        type_line = next((line for line in body if line.strip()), "")
        type_name = type_line.strip().rstrip(":")
        data, _ = _parse_block(body[1:], 0, 2)
        objects.append(UnityObject(int(current_header.group(1)), int(current_header.group(2)), type_name, data or {}))

    for line in text.splitlines():
        if line.startswith("%"):
            continue
        match = _DOC_HEADER.match(line)
        if match:
            flush()
            current_header, body = match, []
        else:
            body.append(line)
    flush()
    return objects


def load(path: str) -> list[UnityObject]:
    with open(path, "r", encoding="utf-8") as f:
        return parse_documents(f.read())


def build_guid_index(unity_project: str) -> dict[str, str]:
    """Map asset GUID -> path relative to the Unity `Assets/` folder (read from `.meta` files)."""
    index: dict[str, str] = {}
    assets = os.path.join(unity_project, "Assets")
    guid_re = re.compile(r"^guid:\s*([0-9a-fA-F]+)", re.M)
    for root, _, names in os.walk(assets):
        for name in names:
            if not name.endswith(".meta"):
                continue
            meta_path = os.path.join(root, name)
            try:
                with open(meta_path, "r", encoding="utf-8", errors="replace") as f:
                    match = guid_re.search(f.read(4096))
            except OSError:
                continue
            if match:
                asset_path = os.path.relpath(meta_path[: -len(".meta")], assets)
                index[match.group(1)] = asset_path.replace(os.sep, "/")
    return index
