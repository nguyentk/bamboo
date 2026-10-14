"""Shared helpers to read the Bamboo / Godot base versions from `version.py`.

Used by the Bamboo build tooling scripts (packaging, smoke tests).
"""

from __future__ import annotations

import os
import runpy
from dataclasses import dataclass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass(frozen=True)
class VersionInfo:
    name: str
    major: int
    minor: int
    patch: int
    status: str
    module_config: str
    bamboo_major: int
    bamboo_minor: int
    bamboo_patch: int
    bamboo_prerelease: str
    bamboo_codename: str

    @property
    def godot_number(self) -> str:
        # Mirrors GODOT_VERSION_NUMBER in core/version.h (patch omitted when 0).
        number = f"{self.major}.{self.minor}"
        if self.patch != 0:
            number += f".{self.patch}"
        return number

    @property
    def godot_full_config(self) -> str:
        # Mirrors GODOT_VERSION_FULL_CONFIG (single precision), e.g. "4.8.dev".
        # This is the export templates folder name and the content of `version.txt` in `.tpz` files.
        return f"{self.godot_number}.{self.status}{self.module_config}"

    @property
    def bamboo_string(self) -> str:
        version = f"{self.bamboo_major}.{self.bamboo_minor}.{self.bamboo_patch}"
        if self.bamboo_prerelease:
            version += f"-{self.bamboo_prerelease}"
        return version

    @property
    def header_prefix(self) -> str:
        # Start of the startup header printed by Main::print_header(), up to the build name,
        # e.g. "Bamboo Engine v0.1.0-alpha.1 (Godot 4.8.dev."
        return f"{self.name} v{self.bamboo_string} (Godot {self.godot_full_config}."


def load_version(version_path: str = os.path.join(REPO_ROOT, "version.py")) -> VersionInfo:
    data = runpy.run_path(version_path)
    status = os.environ.get("GODOT_VERSION_STATUS", str(data["status"]))
    return VersionInfo(
        name=str(data["name"]),
        major=int(data["major"]),
        minor=int(data["minor"]),
        patch=int(data["patch"]),
        status=status,
        module_config=str(data.get("module_config", "")),
        bamboo_major=int(data.get("bamboo_major", 0)),
        bamboo_minor=int(data.get("bamboo_minor", 0)),
        bamboo_patch=int(data.get("bamboo_patch", 0)),
        bamboo_prerelease=str(data.get("bamboo_prerelease", "")),
        bamboo_codename=str(data.get("bamboo_codename", "")),
    )
