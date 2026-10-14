; ตัวติดตั้ง PiriMU สำหรับ Windows (NSIS) — สร้างด้วย installer/build-installers.sh
Unicode true
!include "MUI2.nsh"

!ifndef VERSION
  !define VERSION "1.0.0"
!endif
!ifndef SRC
  !define SRC "PiriMU"
!endif

Name "PiriMU"
Caption "ติดตั้ง PiriMU เว็บบราวเซอร์สำหรับสายมู"
BrandingText "PiriMU โดย ดร.วศิน ภิรมย์ · pirimu.com"
OutFile "PiriMU-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\PiriMU"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 64
ShowInstDetails nevershow
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "PiriMU"
VIAddVersionKey "CompanyName" "Dr. Wasin Pirom"
VIAddVersionKey "FileDescription" "PiriMU Setup"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "pirimu.com"

!define MUI_ICON "${SRC}\icon.ico"
!define MUI_UNICON "${SRC}\icon.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "ยินดีต้อนรับสู่ PiriMU"
!define MUI_WELCOMEPAGE_TEXT "เว็บบราวเซอร์สำหรับสายมู โดย ดร.วศิน ภิรมย์$\r$\n$\r$\nธีมสีมงคลประจำวัน ทองคำ นพเก้า ธีม 12 นักษัตร หมอดูปิริ เลขมงคล และเซียมซี$\r$\n$\r$\nกด ถัดไป เพื่อเริ่มติดตั้ง"
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchPiriMU
!define MUI_FINISHPAGE_RUN_TEXT "เปิด PiriMU เลย"
!define MUI_FINISHPAGE_LINK "แจ้งปัญหาได้ที่ ดร.วศิน ภิรมย์ Line OA: @wasin"
!define MUI_FINISHPAGE_LINK_LOCATION "https://line.me/R/ti/p/@wasin"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Thai"

Function LaunchPiriMU
  SetOutPath "$INSTDIR"
  Exec '"$INSTDIR\python\pythonw.exe" "$INSTDIR\pirimu.py"'
FunctionEnd

!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\PiriMU"

Section "PiriMU"
  nsExec::Exec 'taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq PiriMU*"'
  RMDir /r "$INSTDIR\python"
  SetOutPath "$INSTDIR"
  File /r "${SRC}\*"

  CreateShortCut "$DESKTOP\PiriMU.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\pirimu.py"' "$INSTDIR\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\PiriMU.lnk" "$INSTDIR\python\pythonw.exe" '"$INSTDIR\pirimu.py"' "$INSTDIR\icon.ico" 0

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayName" "PiriMU เว็บบราวเซอร์สำหรับสายมู"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINST_KEY}" "Publisher" "ดร.วศิน ภิรมย์"
  WriteRegStr HKCU "${UNINST_KEY}" "URLInfoAbout" "https://pirimu.com"
  WriteRegStr HKCU "${UNINST_KEY}" "HelpLink" "https://line.me/R/ti/p/@wasin"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\icon.ico"
  WriteRegStr HKCU "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINST_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoRepair" 1
  WriteRegDWORD HKCU "${UNINST_KEY}" "EstimatedSize" 540000
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\PiriMU.lnk"
  Delete "$SMPROGRAMS\PiriMU.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "${UNINST_KEY}"
SectionEnd
