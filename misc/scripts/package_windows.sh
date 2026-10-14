#!/bin/sh
# BAMBOO: Package the Bamboo editor for Windows as an NSIS installer (Bamboo_v<version>_win64_setup.exe).
#
# Usage: sh misc/scripts/package_windows.sh [path/to/bamboo.windows.editor.x86_64[.llvm].exe] [output.exe]
#   Defaults: the newest production editor in bin/ (not .dev / .console) and
#   bin/Bamboo_v<bamboo version>_win64_setup.exe.
#   The matching *.console.exe next to the editor is installed as Bamboo.console.exe.
#
# Environment:
#   MAKENSIS   path to makensis (NSIS 3). Default: makensis from PATH.
#
# The installer is not code-signed: Windows SmartScreen warns until it is signed with an
# Authenticode certificate (see docs/guides/code_signing.md).

set -eu

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VERSIONS="$(cd "$ROOT" && python3 -c 'import runpy; v = runpy.run_path("version.py"); s = "%d.%d.%d" % (v["bamboo_major"], v["bamboo_minor"], v["bamboo_patch"]); print((s + ("-" + v["bamboo_prerelease"] if v["bamboo_prerelease"] else "")) + " " + s + ".0 " + "%d.%d" % (v["major"], v["minor"]))')"
VERSION="$(echo "$VERSIONS" | cut -d' ' -f1)"
VERSION_NUMERIC="$(echo "$VERSIONS" | cut -d' ' -f2)"
GODOT_VERSION="$(echo "$VERSIONS" | cut -d' ' -f3)"

EXE="${1:-}"
if [ -z "$EXE" ]; then
    EXE="$(ls -t "$ROOT"/bin/bamboo.windows.editor.x86_64*.exe 2>/dev/null | grep -v -e '\.dev\.' -e '\.console\.' | head -n 1 || true)"
fi
if [ -z "$EXE" ] || [ ! -f "$EXE" ]; then
    echo "ERROR: Windows editor not found. Build it with:" >&2
    echo "  scons platform=windows arch=x86_64 target=editor production=yes" >&2
    exit 1
fi
CONSOLE_EXE="${EXE%.exe}.console.exe"
if [ ! -f "$CONSOLE_EXE" ]; then
    echo "ERROR: console wrapper not found: $CONSOLE_EXE" >&2
    exit 1
fi
OUT="${2:-$ROOT/bin/Bamboo_v${VERSION}_win64_setup.exe}"
MAKENSIS="${MAKENSIS:-makensis}"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp "$EXE" "$STAGE/Bamboo.exe"
cp "$CONSOLE_EXE" "$STAGE/Bamboo.console.exe"
cp "$ROOT/LICENSE.txt" "$ROOT/COPYRIGHT.txt" "$STAGE/"

echo "Bamboo $VERSION: $EXE -> $OUT"
# makensis needs a UTF-8 locale on macOS (it aborts with std::bad_alloc under the C locale).
LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 "$MAKENSIS" -V2 -WX \
    "-DVERSION=$VERSION" \
    "-DVERSION_NUMERIC=$VERSION_NUMERIC" \
    "-DGODOT_VERSION=$GODOT_VERSION" \
    "-DSOURCE_DIR=$STAGE" \
    "-DICON=$ROOT/platform/windows/godot.ico" \
    "-DOUTFILE=$OUT" \
    "$ROOT/misc/dist/windows/bamboo_installer.nsi"

echo "Wrote $OUT"
echo "Not code-signed: Windows SmartScreen will warn until it is signed."
