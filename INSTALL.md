# วิธีติดตั้ง PiriMU บน GitHub + Coolify (ทีละขั้น)

## ภาพรวม: ใครทำอะไร

| ส่วน | ทำที่ไหน | คุณต้องทำ |
|---|---|---|
| ตัวติดตั้ง `PiriMU-Setup.exe` และ `PiriMU-Mac-App.zip` | ผมสร้างให้แล้ว คุณอัปโหลดไว้ใน **GitHub Releases** | ทำตามข้อ 1.1 |
| เว็บ pirimu.com + หน้า admin | **Coolify** | ตั้งค่าตามส่วนที่ 3 |

## สิ่งที่ต้องตั้งใน Coolify

| อย่าง | ค่า | ทำไมต้องมี |
|---|---|---|
| **Environment Variable** | `ADMIN_PASSWORD` = รหัสผ่านที่คุณตั้งเอง | ใช้เข้าหน้า admin ที่ `pirimu.com/admin` |
| **Environment Variable** | `GITHUB_REPO` = `ชื่อคุณ/pirimu` | ให้ปุ่มดาวน์โหลดบนเว็บชี้ไปที่ตัวติดตั้งใน GitHub Releases |
| **Persistent Storage** | Destination Path = `/data` | เก็บฐานข้อมูลสถิติและอีเมล ถ้าไม่ตั้ง **ข้อมูลจะหายทุกครั้งที่ Redeploy** |

ตัวแปรอื่นไม่บังคับ (ดูท้ายไฟล์) ใช้เวลาทั้งหมดประมาณ 15 นาที ทำครั้งเดียว

---

## ส่วนที่ 1: อัปโหลดขึ้น GitHub

1. แตกไฟล์ `pirimu-project.zip` จะได้โฟลเดอร์ชื่อ `pirimu`
2. เข้า https://github.com/new
3. ตั้ง **Repository name:** `pirimu` เลือก **Public** และ**ไม่ต้อง**ติ๊ก Add a README
4. กด **Create repository**
5. กดลิงก์ **uploading an existing file**
6. เปิดโฟลเดอร์ `pirimu` แล้วเลือก**ของข้างในทั้งหมด** (`Dockerfile`, `README.md`, `INSTALL.md`, โฟลเดอร์ `browser`, `installer`, `server`, `web`) ลากไปวางในหน้า GitHub
   - ⚠️ ห้ามลากตัวโฟลเดอร์ `pirimu` ทั้งก้อน เพราะ `Dockerfile` ต้องอยู่ชั้นนอกสุดของ repo
7. กด **Commit changes**
8. ตรวจว่าหน้าแรกของ repo เห็น `Dockerfile` อยู่ในรายการไฟล์ชั้นแรก
9. แก้ลิงก์ GitHub บนหน้าเว็บ: เปิดไฟล์ `web/data.js` กดรูปดินสอ ✏️ เปลี่ยน `https://github.com/YOUR-NAME/pirimu` เป็น URL repo ของคุณ แล้วกด **Commit changes**

> ⚠️ อย่าใส่ `ADMIN_PASSWORD` ลงในไฟล์ใดๆ บน GitHub เพราะ repo เป็น Public ให้ใส่ใน Coolify เท่านั้น

### 1.1 อัปโหลดตัวติดตั้งขึ้น GitHub Releases (ทำครั้งเดียวต่อเวอร์ชัน)

ไฟล์ติดตั้งใหญ่เกิน 100 MB จึงใส่ใน repo ตรงๆ ไม่ได้ ต้องใส่ใน Releases ซึ่งรับไฟล์ได้ถึง 2 GB

1. ในหน้า repo ดูแถบด้านขวา กด **Releases** (หรือ **Create a new release**)
   - หรือเข้าลิงก์ตรง `https://github.com/ชื่อคุณ/pirimu/releases/new`
2. กด **Choose a tag** พิมพ์ `v1.2.0` แล้วกด **Create new tag**
3. **Release title:** `PiriMU 1.2.0`
4. ลากไฟล์ `PiriMU-Setup.exe` และ `PiriMU-Mac-App.zip` ไปวางในช่อง **Attach binaries** (ชื่อไฟล์ต้องตรงแบบนี้เป๊ะ)
5. รอจนแถบอัปโหลดเต็มทั้งสองไฟล์
6. ติ๊ก **Set as the latest release** แล้วกด **Publish release**

ทดสอบ: เข้า `https://github.com/ชื่อคุณ/pirimu/releases/latest/download/PiriMU-Setup.exe` ต้องเริ่มดาวน์โหลดทันที

---

## ส่วนที่ 2: ตั้งค่า DNS ของ pirimu.com

ไปที่ผู้ให้บริการโดเมน แล้วเพิ่ม record:

| Type | Name | Value |
|---|---|---|
| A | `@` | IP ของ VPS ที่ติดตั้ง Coolify |
| A | `www` | IP เดียวกัน |

ถ้าใช้ Cloudflare ให้ตั้ง Proxy status เป็น **DNS only** (เมฆสีเทา) ก่อน เพื่อให้ Coolify ขอ SSL ได้

---

## ส่วนที่ 3: สร้างแอปใน Coolify

1. เข้า Coolify → **Projects** → เลือกโปรเจกต์ หรือกด **+ Add** สร้างใหม่ชื่อ `PiriMU`
2. เลือก environment **production** แล้วกด **+ New**
3. เลือก **Public Repository** วาง URL repo เช่น `https://github.com/ชื่อคุณ/pirimu` แล้วกด **Check repository**
4. ตั้งค่า:

| ช่อง | ใส่ค่า |
|---|---|
| Branch | `main` |
| Build Pack | **Dockerfile** (ค่าเริ่มต้นมักเป็น Nixpacks ต้องเปลี่ยน) |
| Base Directory | `/` |
| Dockerfile Location | `/Dockerfile` |
| Ports Exposes | `80` |

5. กด **Continue**
6. ช่อง **Domains** ใส่ `https://pirimu.com,https://www.pirimu.com` แล้วกด **Save**

### 6.1 ตั้ง Environment Variable
1. เมนูด้านซ้ายของแอป กด **Environment Variables**
2. กด **+ Add**
3. **Key:** `ADMIN_PASSWORD`  **Value:** รหัสผ่านที่ยาวและเดายาก เช่น `PiriMu-ทองคำ-2569!`
4. กด **Save**

และเพิ่มอีกตัว:
- **Key:** `GITHUB_REPO`  **Value:** `ชื่อคุณ/pirimu` (ส่วนท้ายของ URL repo เช่น repo `https://github.com/wasinpirom/pirimu` ให้ใส่ `wasinpirom/pirimu`)

### 6.2 ตั้ง Persistent Storage
1. เมนูด้านซ้ายของแอป กด **Persistent Storage** (บางเวอร์ชันชื่อ **Storages**)
2. กด **+ Add** เลือกแบบ **Volume**
3. **Name:** `pirimu-data`  **Destination Path:** `/data`
4. กด **Save**

### 6.3 Deploy
กด **Deploy** แล้วรอจน Logs ขึ้นว่าเสร็จ (ครั้งแรก 2–4 นาที) ใน log จะเห็นบรรทัด `PiriMU version 1.2.0 packaged`

---

## ส่วนที่ 4: ตรวจว่าใช้งานได้

- [ ] `https://pirimu.com` เห็นหน้าเว็บ
- [ ] `https://pirimu.com/version.json` เห็น `{"version":"1.2.0",...}`
- [ ] `https://pirimu.com/dl/windows` เริ่มดาวน์โหลด `PiriMU-Setup.exe` (ถ้าได้ไฟล์ .zip แทน แปลว่ายังไม่ได้ตั้ง `GITHUB_REPO`)
- [ ] `https://pirimu.com/dl/mac` เริ่มดาวน์โหลด `PiriMU-Mac-App.zip`
- [ ] `https://pirimu.com/install.ps1` เห็นข้อความสคริปต์
- [ ] `https://pirimu.com/admin` ใส่รหัสผ่านแล้วเข้าได้ และเห็นยอดดาวน์โหลด 1 ครั้งจากข้อก่อนหน้า
- [ ] กด **Redeploy** หนึ่งครั้ง แล้วเข้า admin อีกรอบ ยอดดาวน์โหลดต้องยังอยู่ (แปลว่า Persistent Storage ทำงาน)

---

## หน้า admin ทำอะไรได้บ้าง

เข้าที่ `https://pirimu.com/admin`

- ยอดดาวน์โหลดทั้งหมด วันนี้ 7 วัน แยก Windows/Mac และแยกว่าโหลดผ่านคำสั่งหรือผ่านเว็บ
- จำนวนครั้งที่ผู้ใช้เปิดโปรแกรมต่อวัน และเวอร์ชันที่ใช้อยู่
- รายชื่ออีเมลที่สมัครรับข่าวพร้อมยินยอมแล้ว กด **ดาวน์โหลด CSV** เปิดใน Excel ได้ทันที
- ปุ่ม **ลบ** อีเมล ใช้เมื่อมีคนขอยกเลิกทาง Line OA (ต้องลบตามกฎหมาย PDPA)
- ดาวน์โหลดล่าสุด 50 รายการพร้อม IP (IP ถูกลบอัตโนมัติเมื่อครบ 90 วัน)

**เวลาส่งอีเมลขายของ:** ส่งเฉพาะคนในรายการนี้ ใส่ช่องทางยกเลิกทุกครั้ง เช่น "ไม่อยากรับข่าวแล้ว แจ้งที่ Line OA @wasin"

---

## ส่วนที่ 5: อัปเดตครั้งต่อไป

| อยากทำอะไร | แก้ไฟล์ | แล้ว |
|---|---|---|
| แก้เนื้อหาเว็บ ลิงก์ หรือ "มีอะไรใหม่" | `web/data.js`, `web/*.html` | Redeploy |
| ออกเบราว์เซอร์เวอร์ชันใหม่ | `browser/pirimu.py` เปลี่ยน `APP_VERSION` เป็นเลขที่ใหม่กว่าเดิม | สร้างตัวติดตั้งใหม่ด้วย `installer/build-installers.sh` (บน Linux) หรือส่งไฟล์มาให้ Claude สร้าง แล้วอัปโหลดเป็น Release ใหม่ตามข้อ 1.1 จากนั้น Redeploy |

ข้อมูลใน admin ไม่หายเวลา Redeploy (ถ้าตั้ง Persistent Storage แล้ว)

ถ้าอยากให้ deploy เองทุกครั้งที่แก้ GitHub: Coolify → แอป → **Webhooks** คัดลอก URL ไปใส่ที่ GitHub → **Settings → Webhooks → Add webhook** (Content type `application/json`)

---

## แก้ปัญหาที่พบบ่อย

| อาการ | วิธีแก้ |
|---|---|
| Deploy ขึ้นว่าหา Dockerfile ไม่เจอ | ย้ายไฟล์ทั้งหมดขึ้นมาชั้นนอกสุดของ repo |
| Build Pack เป็น Nixpacks แล้ว deploy พัง | เปลี่ยนเป็น **Dockerfile** แล้ว Redeploy |
| เข้าเว็บแล้วขึ้น 502 / Bad Gateway | ตรวจว่า Ports Exposes เป็น `80` |
| หน้า admin ขึ้นว่า "ยังไม่ได้ตั้ง ADMIN_PASSWORD" | ตั้งตามข้อ 6.1 แล้ว Redeploy |
| ใส่รหัสถูกแต่เข้า admin ไม่ได้ | เข้าผ่าน `https://` เท่านั้น ห้ามใช้ `http://` |
| Redeploy แล้วสถิติกับอีเมลหายหมด | ยังไม่ได้ตั้ง Persistent Storage `/data` ตามข้อ 6.2 |
| ขึ้น SSL ไม่ปลอดภัย | รอ DNS อัปเดต 5–30 นาที แล้ว Redeploy |
| ปุ่มดาวน์โหลดได้ไฟล์ .zip ไม่ใช่ .exe | ตั้ง `GITHUB_REPO` ใน Coolify แล้ว Redeploy |
| กดดาวน์โหลด .exe แล้วขึ้น 404 ของ GitHub | ยังไม่ได้ Publish release หรือชื่อไฟล์ไม่ตรง (`PiriMU-Setup.exe`, `PiriMU-Mac-App.zip`) หรือไม่ได้ติ๊ก latest |
| Mac ขึ้นว่าแอปเสียหาย หรือเปิดไม่ขึ้น | เปิด Terminal วาง `xattr -cr /Applications/PiriMU.app` แล้วเปิดใหม่ |
| Windows ขึ้น “Windows protected your PC” | ปกติสำหรับโปรแกรมที่ยังไม่ซื้อใบรับรอง กด More info → Run anyway |

---

## ตัวแปรเสริม (ไม่บังคับ)

| Key | ค่าเริ่มต้น | ใช้ทำอะไร |
|---|---|---|
| `IP_RETENTION_DAYS` | `90` | ลบ IP ออกจากบันทึกเมื่อเก่ากว่ากี่วัน (ถ้าเปลี่ยน ต้องแก้ตัวเลขในหน้า privacy ให้ตรงด้วย) |
| `COOKIE_SECURE` | `1` | ตั้ง `0` เฉพาะตอนทดสอบในเครื่องแบบ http |
