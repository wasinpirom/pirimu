# PiriMU — เว็บบราวเซอร์สำหรับสายมู โดย ดร.วศิน ภิรมย์

เว็บ **pirimu.com** โค้ดเบราว์เซอร์ **PiriMU** และหน้า **admin** อยู่ใน repo เดียวกัน
Deploy ด้วย Dockerfile บน Coolify แล้วระบบจะ:

1. เสิร์ฟหน้าเว็บ (`web/`) และคำสั่งติดตั้งแบบบรรทัดเดียว (`install.ps1`, `install.sh`)
2. แพ็ก `PiriMU-Windows.zip` และ `PiriMU-Mac.zip` จากโค้ดล่าสุดอัตโนมัติ
3. สร้าง `/version.json` จากเลขเวอร์ชันในโค้ด ให้เบราว์เซอร์ของผู้ใช้แจ้งเตือนอัปเดต
4. นับยอดดาวน์โหลด การเปิดโปรแกรม และเก็บอีเมลที่ผู้ใช้สมัครรับข่าว ดูได้ที่ `/admin`

```
pirimu/
├── Dockerfile            ← Coolify ใช้ไฟล์นี้
├── INSTALL.md            ← วิธีติดตั้งทีละขั้น (อ่านไฟล์นี้)
├── installer/        ← สคริปต์สร้าง PiriMU-Setup.exe (NSIS) และแอป Mac (build-installers.sh)
├── server/
│   ├── app.py            ← เซิร์ฟเวอร์ Flask: เว็บ + ดาวน์โหลด + สถิติ + admin
│   └── requirements.txt
├── browser/
│   ├── pirimu.py         ← โค้ดเบราว์เซอร์ (แก้ APP_VERSION ที่นี่)
│   ├── requirements.txt, icon.png, icon.ico
│   ├── windows/          ← install.bat, run.bat, README.txt
│   └── mac/              ← install.command, run.command, README.txt
└── web/
    ├── index.html        ← หน้าแรก + วิธีติดตั้ง + สมัครรับข่าว
    ├── guide.html        ← คู่มือสายมู
    ├── privacy.html      ← นโยบายความเป็นส่วนตัว (PDPA)
    ├── install.ps1       ← คำสั่งติดตั้งบรรทัดเดียว Windows
    ├── install.sh        ← คำสั่งติดตั้งบรรทัดเดียว Mac
    ├── data.js           ← แก้ลิงก์เว็บแนะนำ / มีอะไรใหม่ / GitHub / Line OA ที่นี่
    └── style.css, main.js, fonts/, icon.png, favicon.png
```

## ติดตั้งบน Coolify

ดู **INSTALL.md** ทีละขั้น สรุปสั้นๆ:

- Build Pack: **Dockerfile** · Port: **80**
- Environment Variable: **`ADMIN_PASSWORD`** (บังคับ) และ **`GITHUB_REPO`** (เช่น `ชื่อคุณ/pirimu`)
- Persistent Storage: Destination Path **`/data`** (บังคับ ไม่งั้นข้อมูลหายตอน Redeploy)

## ทดสอบในเครื่องก่อน deploy (ไม่บังคับ)

```bash
# เว็บ
docker build -t pirimu . && docker run --rm -p 8080:80 -e ADMIN_PASSWORD=test -e COOKIE_SECURE=0 -v pirimu-data:/data pirimu
# แล้วเปิด http://localhost:8080

# เบราว์เซอร์
cd browser
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python pirimu.py          # Windows: .venv\Scripts\python pirimu.py
```

## หมายเหตุ

- ข้อมูลในโปรแกรม (ธีม วันเกิด บุ๊กมาร์ก ประวัติ) เก็บที่ `~/.pirimu` ในเครื่องผู้ใช้
- ฝั่งเซิร์ฟเวอร์เก็บสถิติดาวน์โหลด (IP ลบเองใน 90 วัน) และอีเมลที่ผู้ใช้ยินยอม ไว้ใน `/data/pirimu.db`
- หน้าแรกของเบราว์เซอร์คือ `https://pirimu.com` แก้ได้ที่ `HOME_URL` ใน `pirimu.py`
- คำทำนายทั้งหมดเพื่อความบันเทิง
