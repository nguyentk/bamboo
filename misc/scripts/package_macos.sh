#!/bin/sh
# Package the Bamboo editor for macOS: sign the .app bundle, build a .dmg, notarize and staple it.
#
# Usage: sh misc/scripts/package_macos.sh [path/to/Bamboo.app] [output.dmg]
#   Defaults: the editor bundle created by `scons ... target=editor generate_bundle=yes` in bin/,
#   and bin/Bamboo_v<bamboo version>_macOS.dmg.
#
# Environment:
#   BAMBOO_SIGN_IDENTITY     "Developer ID Application: <Org> (TEAMID)". Unset: ad-hoc signature
#                            (runs on the build machine only, Gatekeeper rejects it elsewhere).
#   BAMBOO_NOTARY_PROFILE    keychain profile created with `xcrun notarytool store-credentials`, or
#   BAMBOO_NOTARY_APPLE_ID / BAMBOO_NOTARY_TEAM_ID / BAMBOO_NOTARY_PASSWORD (app-specific password).
#   Notarization is skipped when neither is set or when the signature is ad-hoc.

set -eu

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VERSION="$(cd "$ROOT" && python3 -c 'import runpy; v = runpy.run_path("version.py"); s = "%d.%d.%d" % (v["bamboo_major"], v["bamboo_minor"], v["bamboo_patch"]); print(s + ("-" + v["bamboo_prerelease"] if v["bamboo_prerelease"] else ""))')"

APP="${1:-}"
if [ -z "$APP" ]; then
    APP="$(ls -d "$ROOT"/bin/*_macos_editor*.app 2>/dev/null | head -n 1 || true)"
fi
if [ -z "$APP" ] || [ ! -d "$APP" ]; then
    echo "ERROR: editor .app bundle not found. Build it with:" >&2
    echo "  scons platform=macos target=editor generate_bundle=yes" >&2
    exit 1
fi
DMG="${2:-$ROOT/bin/Bamboo_v${VERSION}_macOS.dmg}"
IDENTITY="${BAMBOO_SIGN_IDENTITY:--}"
ENTITLEMENTS="$ROOT/misc/dist/macos/editor.entitlements"

echo "Bamboo $VERSION: $APP -> $DMG"

# 1. Sign (hardened runtime + entitlements; ad-hoc when no identity is configured).
codesign --force --deep --timestamp=none --options runtime --entitlements "$ENTITLEMENTS" --sign "$IDENTITY" "$APP" 2>/dev/null \
    || codesign --force --deep --options runtime --entitlements "$ENTITLEMENTS" --sign "$IDENTITY" "$APP"
if [ "$IDENTITY" != "-" ]; then
    codesign --force --deep --timestamp --options runtime --entitlements "$ENTITLEMENTS" --sign "$IDENTITY" "$APP"
fi
codesign --verify --deep --strict "$APP"
echo "Signed with: $([ "$IDENTITY" = "-" ] && echo "ad-hoc signature" || echo "$IDENTITY")"

# 2. Build the disk image (app + /Applications shortcut).
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
cp -R "$APP" "$STAGING/Bamboo.app"
ln -s /Applications "$STAGING/Applications"
rm -f "$DMG"
hdiutil create -quiet -volname "Bamboo Engine $VERSION" -srcfolder "$STAGING" -fs HFS+ -format UDZO "$DMG"
if [ "$IDENTITY" != "-" ]; then
    codesign --force --timestamp --sign "$IDENTITY" "$DMG"
fi

# 3. Notarize and staple (Developer ID only).
if [ "$IDENTITY" = "-" ]; then
    echo "Notarization skipped: ad-hoc signature (set BAMBOO_SIGN_IDENTITY)."
elif [ -n "${BAMBOO_NOTARY_PROFILE:-}" ]; then
    xcrun notarytool submit "$DMG" --keychain-profile "$BAMBOO_NOTARY_PROFILE" --wait
    xcrun stapler staple "$DMG"
elif [ -n "${BAMBOO_NOTARY_APPLE_ID:-}" ]; then
    xcrun notarytool submit "$DMG" --apple-id "$BAMBOO_NOTARY_APPLE_ID" --team-id "$BAMBOO_NOTARY_TEAM_ID" \
        --password "$BAMBOO_NOTARY_PASSWORD" --wait
    xcrun stapler staple "$DMG"
else
    echo "Notarization skipped: no notary credentials (BAMBOO_NOTARY_PROFILE or BAMBOO_NOTARY_APPLE_ID)."
fi

# 4. Gatekeeper assessment (only meaningful for notarized Developer ID builds).
if spctl -a -vvv -t install "$DMG" 2>&1; then
    echo "Gatekeeper: accepted."
else
    echo "Gatekeeper: rejected (expected for ad-hoc / non-notarized builds)."
fi
echo "Wrote $DMG"
