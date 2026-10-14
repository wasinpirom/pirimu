#!/bin/bash
# สร้าง PiriMU-Setup.exe (Windows) และ PiriMU-Mac-App.zip (Mac Apple Silicon) บนเครื่อง Linux
# ต้องมี: python3, pip, unzip, zip, makensis (sudo apt install nsis)
# ใช้ Python สำเร็จรูปจาก python-build-standalone + PyQt6 wheels จาก PyPI (ไม่ต้องมีเครื่อง Windows/Mac)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
VER="$(sed -n 's/^APP_VERSION = "\(.*\)"/\1/p' browser/pirimu.py)"
PBS_TAG="${PBS_TAG:-20260924}"          # รุ่น python-build-standalone
PY="${PY:-3.12.14}"
QT="${QT:-6.11.0}"
OUT="$ROOT/dist-installer"; W="$(mktemp -d)"
mkdir -p "$OUT"
echo "== PiriMU $VER =="

fetch() { curl -fsSL -o "$W/$1" "https://github.com/astral-sh/python-build-standalone/releases/download/$PBS_TAG/$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$1")"; }
curl -fsSL -o "$W/SHA256SUMS" "https://github.com/astral-sh/python-build-standalone/releases/download/$PBS_TAG/SHA256SUMS"
WINPY="cpython-$PY+$PBS_TAG-x86_64-pc-windows-msvc-install_only.tar.gz"
MACPY="cpython-$PY+$PBS_TAG-aarch64-apple-darwin-install_only.tar.gz"
fetch "$WINPY"; fetch "$MACPY"
(cd "$W" && grep -E " ($WINPY|$MACPY)\$" SHA256SUMS | sha256sum -c -)

trim_qt() {  # $1 = PyQt6/Qt6 dir
  find "$1/translations" -maxdepth 1 -name "*.qm" ! -name "*_th.qm" ! -name "*_en.qm" -delete
  find "$1" -path "*qtwebengine_locales*" -name "*.pak" ! -name "th.pak" ! -name "en-US.pak" ! -name "en-GB.pak" -delete
  rm -rf "$1/qml"
}

# ---------- Windows ----------
pip download -q --only-binary=:all: --platform win_amd64 --python-version 3.12 --implementation cp \
  --abi cp312 --abi abi3 --abi none -d "$W/wh_win" "PyQt6==$QT" "PyQt6-WebEngine==$QT"
S="$W/win/PiriMU"; mkdir -p "$S"
tar xzf "$W/$WINPY" -C "$S"
rm -rf "$S/python/Lib/test" "$S/python/Lib/idlelib" "$S/python/Lib/tkinter" "$S/python/Lib/turtledemo" \
       "$S/python/tcl" "$S/python/include" "$S/python/Scripts" "$S/python/libs" "$S"/python/Lib/site-packages/pip*
find "$S/python" -name "*.pdb" -delete
for w in "$W"/wh_win/*.whl; do unzip -qo "$w" -d "$S/python/Lib/site-packages"; done
trim_qt "$S/python/Lib/site-packages/PyQt6/Qt6"
cp browser/pirimu.py browser/icon.png browser/icon.ico "$S/"
cp installer/pirimu.nsi "$W/win/"
(cd "$W/win" && makensis -V2 -DVERSION="$VER" -DSRC=PiriMU pirimu.nsi && mv PiriMU-Setup.exe "$OUT/")

# ---------- Mac (Apple Silicon) ----------
pip download -q --only-binary=:all: --platform macosx_14_0_arm64 --python-version 3.12 --implementation cp \
  --abi cp312 --abi abi3 --abi none -d "$W/wh_mac" "PyQt6==$QT" "PyQt6-WebEngine==$QT"
APP="$W/mac/PiriMU.app/Contents"; mkdir -p "$APP/MacOS" "$APP/Resources"
tar xzf "$W/$MACPY" -C "$APP/Resources"
SP="$APP/Resources/python/lib/python3.12/site-packages"
rm -rf "$APP/Resources/python/lib/python3.12/"{test,idlelib,tkinter,turtledemo} "$APP/Resources/python/"{include,share} "$SP"/pip*
for w in "$W"/wh_mac/*.whl; do unzip -qo "$w" -d "$SP"; done
trim_qt "$SP/PyQt6/Qt6"
cp browser/pirimu.py browser/icon.png "$APP/Resources/"
python3 -c "from PIL import Image; Image.open('browser/icon.png').save('$APP/Resources/PiriMU.icns')"
cp installer/mac/launcher.sh "$APP/MacOS/PiriMU"; chmod 755 "$APP/MacOS/PiriMU"
sed "s/__VERSION__/$VER/g" installer/mac/Info.plist > "$APP/Info.plist"
cp installer/mac/README.txt "$W/mac/"
(cd "$W/mac" && zip -qry -9 "$OUT/PiriMU-Mac-App.zip" PiriMU.app README.txt)

rm -rf "$W"
ls -la "$OUT"
echo "อัปโหลด 2 ไฟล์ใน dist-installer/ ขึ้น GitHub Releases (ดู INSTALL.md)"
