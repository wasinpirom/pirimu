#!/bin/bash
# PiriMU one-line installer for macOS
# ใช้งาน: เปิด Terminal แล้ววาง   curl -fsSL https://pirimu.com/install.sh | bash
set -e
BASE="https://pirimu.com"
DIR="$HOME/PiriMU"

echo ""
echo "  PiriMU - เว็บบราวเซอร์สำหรับสายมู โดย ดร.วศิน ภิรมย์"
echo "  กำลังติดตั้ง... (ครั้งแรกใช้เวลา 3-10 นาที)"
echo ""

if [ "$(uname)" != "Darwin" ]; then
  echo "คำสั่งนี้สำหรับ macOS ครับ Windows ให้ใช้คำสั่งใน PowerShell ตามหน้าเว็บ"; exit 1
fi

HAS_PY=""
for c in python3.13 python3.12 python3.11 python3.10 /usr/local/bin/python3 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >/dev/null 2>&1; then
    HAS_PY="$c"; break
  fi
done
if [ -z "$HAS_PY" ]; then
  echo "ยังไม่พบ Python 3 ในเครื่องครับ เลือกได้หนึ่งวิธี:"
  echo "  1) ถ้ามีหน้าต่างขึ้นมาให้ติดตั้ง Command Line Tools ให้กด Install รอจนเสร็จ"
  echo "  2) หรือติดตั้ง Python จาก https://www.python.org/downloads/"
  echo "แล้ววางคำสั่งเดิมอีกครั้ง"
  xcode-select --install >/dev/null 2>&1 || open "https://www.python.org/downloads/"
  exit 1
fi

echo "[1/2] กำลังดาวน์โหลด PiriMU..."
TMP="$(mktemp -d)"
curl -fsSL "$BASE/dl/mac-zip?src=cli" -o "$TMP/pirimu.zip"
unzip -oq "$TMP/pirimu.zip" -d "$TMP"
mkdir -p "$DIR"
cp -R "$TMP/PiriMU-Mac/." "$DIR/"
chmod +x "$DIR"/*.command
rm -rf "$TMP"

echo "[2/2] กำลังติดตั้ง..."
bash "$DIR/install.command" </dev/null
