#!/bin/bash
cd "$(dirname "$0")" || exit 1
DIR="$(pwd)"
echo ""
echo "  ============================================="
echo "    PiriMU  เว็บบราวเซอร์สำหรับสายมู"
echo "    โดย ดร.วศิน ภิรมย์  -  pirimu.com"
echo "  ============================================="
echo ""

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "  ยังไม่พบ Python 3 ในเครื่องครับ"
  echo "  ติดตั้งจาก https://www.python.org/downloads/ แล้วดับเบิลคลิก install.command อีกครั้ง"
  open "https://www.python.org/downloads/"
  read -r -p "  กด Enter เพื่อปิด..." _
  exit 1
fi

echo "[1/3] กำลังสร้างพื้นที่ติดตั้ง ($PY)..."
"$PY" -m venv .venv || { echo "สร้าง venv ไม่สำเร็จ"; read -r _; exit 1; }

echo "[2/3] กำลังดาวน์โหลดเครื่องยนต์เบราว์เซอร์ (ประมาณ 150-250 MB รอสักครู่นะครับ)..."
.venv/bin/python -m pip install --upgrade pip --disable-pip-version-check -q
.venv/bin/python -m pip install -r requirements.txt --disable-pip-version-check || {
  echo "ติดตั้งไม่สำเร็จ ตรวจสอบอินเทอร์เน็ตแล้วลองใหม่ หรือแจ้งปัญหาได้ที่ ดร.วศิน ภิรมย์ Line OA: @wasin"
  read -r _; exit 1; }

echo "[3/3] กำลังสร้างแอป PiriMU ในโฟลเดอร์ Applications ของคุณ..."
APP="$HOME/Applications/PiriMU.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cat > "$APP/Contents/MacOS/PiriMU" <<LAUNCH
#!/bin/bash
cd "$DIR"
exec "$DIR/.venv/bin/python" "$DIR/pirimu.py"
LAUNCH
chmod +x "$APP/Contents/MacOS/PiriMU"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>PiriMU</string>
  <key>CFBundleDisplayName</key><string>PiriMU</string>
  <key>CFBundleIdentifier</key><string>com.pirimu.browser</string>
  <key>CFBundleExecutable</key><string>PiriMU</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
ICONSET="$(mktemp -d)/icon.iconset"
mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s icon.png --out "$ICONSET/icon_${s}x${s}.png" >/dev/null 2>&1
  d=$((s*2)); sips -z $d $d icon.png --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null 2>&1
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/icon.icns" >/dev/null 2>&1
touch "$APP"

echo ""
echo "  ติดตั้งเสร็จแล้ว! เปิด PiriMU ได้จาก Launchpad, Spotlight (กด ⌘+Space พิมพ์ PiriMU)"
echo "  หรือโฟลเดอร์ Applications ในโฮมของคุณ"
echo "  ห้ามลบหรือย้ายโฟลเดอร์นี้ เพราะโปรแกรมอยู่ในโฟลเดอร์นี้"
echo ""
open "$APP"
