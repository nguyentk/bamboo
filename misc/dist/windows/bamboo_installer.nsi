; BAMBOO: Windows installer for the Bamboo editor (NSIS 3, Unicode). Built by misc/scripts/package_windows.sh.
;
; Required defines (passed with -D by the packaging script):
;   VERSION          Bamboo product version, e.g. 0.1.0-alpha.1
;   VERSION_NUMERIC  four-part numeric version for the file properties, e.g. 0.1.0.0
;   GODOT_VERSION    Godot base version, e.g. 4.8
;   SOURCE_DIR       staging folder containing Bamboo.exe, Bamboo.console.exe, LICENSE.txt, COPYRIGHT.txt
;   ICON             installer icon (.ico)
;   OUTFILE          output installer path
;
; Per-user install (no administrator rights), like Godot's own Inno Setup script (godot.iss).
; Editor settings and project data in %APPDATA%\Bamboo are kept on uninstall.

Unicode true
SetCompressor /SOLID lzma
RequestExecutionLevel user
ManifestDPIAware true

!define APP_NAME "Bamboo Engine"
!define APP_PUBLISHER "Bamboo Engine contributors"
!define APP_URL "https://godotengine.org/"
!define APP_EXE "Bamboo.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\BambooEngine"

Name "${APP_NAME} ${VERSION}"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\Programs\Bamboo Engine"
InstallDirRegKey HKCU "${UNINSTALL_KEY}" "InstallLocation"
BrandingText "${APP_NAME} ${VERSION} (Godot ${GODOT_VERSION})"

VIProductVersion "${VERSION_NUMERIC}"
VIAddVersionKey /LANG=0 "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=0 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=0 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=0 "FileDescription" "${APP_NAME} ${VERSION} Setup"
VIAddVersionKey /LANG=0 "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey /LANG=0 "LegalCopyright" "Bamboo Engine is based on Godot Engine. MIT License."

!include "MUI2.nsh"
!include "x64.nsh"

!define MUI_ICON "${ICON}"
!define MUI_UNICON "${ICON}"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${SOURCE_DIR}\LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Vietnamese"

Function .onInit
    ${IfNot} ${RunningX64}
        MessageBox MB_OK|MB_ICONSTOP "${APP_NAME} requires 64-bit Windows (x86_64)."
        Abort
    ${EndIf}
FunctionEnd

Section "!${APP_NAME}" SecMain
    SectionIn RO
    SetOutPath "$INSTDIR"
    File "${SOURCE_DIR}\Bamboo.exe"
    File "${SOURCE_DIR}\Bamboo.console.exe"
    File "${SOURCE_DIR}\LICENSE.txt"
    File "${SOURCE_DIR}\COPYRIGHT.txt"
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" "$INSTDIR\Uninstall.exe"

    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKCU "${UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section /o "Desktop shortcut" SecDesktop
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\Bamboo.exe"
    Delete "$INSTDIR\Bamboo.console.exe"
    Delete "$INSTDIR\LICENSE.txt"
    Delete "$INSTDIR\COPYRIGHT.txt"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"

    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"

    DeleteRegKey HKCU "${UNINSTALL_KEY}"
SectionEnd
