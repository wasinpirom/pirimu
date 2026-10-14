"""
pirimu.com server — เว็บ + ไฟล์ดาวน์โหลด + เก็บสถิติ + หน้า admin
โดย ดร.วศิน ภิรมย์

Environment variables (ตั้งใน Coolify):
  ADMIN_PASSWORD     (ต้องตั้ง) รหัสผ่านเข้า /admin
  IP_RETENTION_DAYS  (ไม่บังคับ, ค่าเริ่มต้น 90) ลบ IP ออกจากบันทึกเมื่อเก่ากว่านี้
  GITHUB_REPO        (แนะนำ) เช่น ชื่อคุณ/pirimu ให้ปุ่มดาวน์โหลดชี้ไปที่ตัวติดตั้งใน GitHub Releases
  COOKIE_SECURE      (ไม่บังคับ, ค่าเริ่มต้น 1) ตั้ง 0 เฉพาะตอนทดสอบในเครื่องแบบ http
ข้อมูลทั้งหมดอยู่ใน /data (ต้องผูก Persistent Storage ใน Coolify)
"""
import csv
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (Flask, Response, abort, jsonify, redirect, render_template_string, request,
                   send_from_directory, session)

STATIC = os.environ.get("STATIC_DIR", "/app/static")
DATA = os.environ.get("DATA_DIR", "/data")
os.makedirs(DATA, exist_ok=True)
DB_PATH = os.path.join(DATA, "pirimu.db")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
IP_RETENTION_DAYS = int(os.environ.get("IP_RETENTION_DAYS", "90"))
TZ = timezone(timedelta(hours=7))  # เวลาไทย
CONSENT_TEXT = ("ยินยอมให้ ดร.วศิน ภิรมย์ ใช้อีเมลนี้ส่งข่าวอัปเดต PiriMU เคล็ดลับสายมู "
                "และข้อเสนอสินค้าหรือคอร์สออนไลน์ ยกเลิกได้ทุกเมื่อผ่าน Line OA @wasin")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip().strip("/")
# ตัวติดตั้งจริง อัปโหลดไว้ใน GitHub Releases ของ repo
INSTALLERS = {"windows": "PiriMU-Setup.exe", "mac": "PiriMU-Mac-App.zip"}
# ไฟล์ zip สำรอง (แบบใช้ Python) แพ็กใน Docker
ZIPS = {"windows": "PiriMU-Windows.zip", "mac": "PiriMU-Mac.zip"}
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,}$")


def _secret_key():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    path = os.path.join(DATA, "secret.key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


app = Flask(__name__, static_folder=None)
app.secret_key = _secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)


# ======================= database =======================
def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con


with db() as _c:
    _c.execute("PRAGMA journal_mode=WAL")
    _c.executescript("""
    CREATE TABLE IF NOT EXISTS downloads(
        id INTEGER PRIMARY KEY, ts TEXT, day TEXT, os TEXT, src TEXT, version TEXT, ip TEXT, ua TEXT);
    CREATE INDEX IF NOT EXISTS idx_dl_day ON downloads(day);
    CREATE TABLE IF NOT EXISTS subscribers(
        id INTEGER PRIMARY KEY, email TEXT UNIQUE, os TEXT, consent TEXT, ts TEXT, ip TEXT);
    CREATE TABLE IF NOT EXISTS opens(
        day TEXT, version TEXT, os TEXT, n INTEGER, PRIMARY KEY(day, version, os));
    """)


def now():
    return datetime.now(TZ)


def client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return (xff.split(",")[0].strip() if xff else request.remote_addr) or ""


def current_version():
    try:
        with open(os.path.join(STATIC, "version.json"), encoding="utf-8") as f:
            return json.load(f).get("version", "")
    except Exception:
        return ""


def purge_old_ips():
    cutoff = (now() - timedelta(days=IP_RETENTION_DAYS)).isoformat()
    with db() as c:
        c.execute("UPDATE downloads SET ip=NULL, ua=NULL WHERE ts < ? AND ip IS NOT NULL", (cutoff,))
        c.execute("UPDATE subscribers SET ip=NULL WHERE ts < ? AND ip IS NOT NULL", (cutoff,))


# ======================= simple rate limit =======================
_hits = defaultdict(list)


def limited(key, limit, window):
    t = time.time()
    _hits[key] = [x for x in _hits[key] if t - x < window]
    if len(_hits[key]) >= limit:
        return True
    _hits[key].append(t)
    return False


# ======================= public routes =======================
@app.after_request
def headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


@app.get("/healthz")
def healthz():
    return "ok"


@app.get("/version.json")
def version_json():
    v = request.args.get("v", "")[:20]
    osn = request.args.get("os", "")[:10]
    if v:  # นับการเปิดโปรแกรม (นับรวม ไม่เก็บ IP)
        with db() as c:
            c.execute("INSERT INTO opens(day, version, os, n) VALUES(?,?,?,1) "
                      "ON CONFLICT(day, version, os) DO UPDATE SET n = n + 1",
                      (now().date().isoformat(), v, osn))
    resp = send_from_directory(STATIC, "version.json", max_age=0)
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.get("/dl/<target>")
def download(target):
    osname, _, kind = target.partition("-")      # windows | mac | windows-zip | mac-zip
    if osname not in ZIPS or kind not in ("", "zip"):
        abort(404)
    if request.args.get("src") == "cli":
        src = "cli"
    elif kind == "zip" or not GITHUB_REPO:
        src = "zip"
    else:
        src = "installer"
    ts = now()
    with db() as c:
        c.execute("INSERT INTO downloads(ts, day, os, src, version, ip, ua) VALUES(?,?,?,?,?,?,?)",
                  (ts.isoformat(), ts.date().isoformat(), osname, src, current_version(), client_ip(),
                   request.headers.get("User-Agent", "")[:200]))
    if src == "installer":
        return redirect(f"https://github.com/{GITHUB_REPO}/releases/latest/download/{INSTALLERS[osname]}", code=302)
    return redirect(f"/downloads/{ZIPS[osname]}", code=302)


@app.post("/api/subscribe")
def subscribe():
    if limited("sub:" + client_ip(), 5, 3600):
        return jsonify(ok=False, error="ส่งบ่อยเกินไป ลองใหม่ภายหลัง"), 429
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    if not EMAIL_RE.match(email):
        return jsonify(ok=False, error="รูปแบบอีเมลไม่ถูกต้อง"), 400
    if data.get("consent") is not True:
        return jsonify(ok=False, error="กรุณาติ๊กยินยอมก่อนสมัคร"), 400
    osn = str(data.get("os", ""))[:10]
    with db() as c:
        c.execute("INSERT INTO subscribers(email, os, consent, ts, ip) VALUES(?,?,?,?,?) "
                  "ON CONFLICT(email) DO UPDATE SET consent=excluded.consent, ts=excluded.ts",
                  (email, osn, CONSENT_TEXT, now().isoformat(), client_ip()))
    return jsonify(ok=True)


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/<path:path>")
def static_files(path):
    full = os.path.join(STATIC, path)
    if os.path.isdir(full):
        path = os.path.join(path, "index.html")
    elif not os.path.exists(full) and os.path.exists(full + ".html"):
        path += ".html"
    if not os.path.exists(os.path.join(STATIC, path)):
        return send_from_directory(STATIC, "index.html"), 404
    resp = send_from_directory(STATIC, path)
    if path.endswith((".ps1", ".sh")):
        resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    if path.startswith("downloads/") or path.endswith((".ps1", ".sh", ".html")):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


# ======================= admin =======================
def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect("/admin/login")
        return fn(*a, **kw)
    return wrapper


def check_csrf():
    if not hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "")):
        abort(400)


ADMIN_CSS = """
<link rel="stylesheet" href="/style.css">
<style>
body{margin:0;font-family:Sarabun,system-ui,sans-serif;background:#FFF9FB;color:#2B1D3A}
.wrap{max-width:1100px;margin:0 auto;padding:24px}
h1,h2{font-family:Mitr,sans-serif;font-weight:500} h1{font-size:1.6rem;margin:0}
header{display:flex;align-items:center;gap:12px;margin-bottom:20px} header img{width:40px}
header form{margin-left:auto}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:28px}
.stat{background:#fff;border:2px solid #2B1D3A;border-radius:18px;padding:14px 18px}
.stat b{display:block;font-family:Mitr;font-size:1.9rem;font-weight:500}
.stat span{color:#5E4E6E;font-size:.92rem}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;margin-bottom:28px;font-size:.95rem}
th,td{padding:8px 12px;border-bottom:1px solid #F3E3EC;text-align:left}
th{background:#FFF3C4;font-family:Mitr;font-weight:500}
.bar{height:10px;background:#F49AC1;border-radius:5px;display:inline-block;vertical-align:middle}
.bar.mac{background:#74C0FC}
button,.btn{font:inherit;border:2px solid #2B1D3A;background:#fff;border-radius:999px;padding:6px 16px;cursor:pointer;text-decoration:none;color:#2B1D3A}
button.del{border-color:#C92A2A;color:#C92A2A;padding:2px 10px;font-size:.85rem}
.login{max-width:360px;margin:12vh auto;background:#fff;border:2px solid #2B1D3A;border-radius:24px;padding:28px}
.login input{width:100%;font:inherit;padding:10px 14px;border-radius:12px;border:2px solid #2B1D3A;margin:10px 0 16px;box-sizing:border-box}
.err{color:#C92A2A} .muted{color:#5E4E6E;font-size:.9rem}
.scroll{overflow-x:auto}
</style>
"""

LOGIN_HTML = ADMIN_CSS + """
<title>PiriMU Admin</title>
<form class="login" method="post">
  <h1>🔐 PiriMU Admin</h1>
  {% if not configured %}<p class="err">ยังไม่ได้ตั้ง ADMIN_PASSWORD ใน Coolify</p>{% endif %}
  {% if error %}<p class="err">{{ error }}</p>{% endif %}
  <label>รหัสผ่าน<input type="password" name="password" autofocus required></label>
  <button type="submit">เข้าสู่ระบบ</button>
</form>
"""

DASH_HTML = ADMIN_CSS + """
<title>PiriMU Admin</title>
<div class="wrap">
<header><img src="/icon.png" alt=""><h1>PiriMU Admin</h1>
  <form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="{{ csrf }}">
  <button>ออกจากระบบ</button></form></header>

<div class="stats">
  <div class="stat"><span>ดาวน์โหลดทั้งหมด</span><b>{{ "{:,}".format(t.total) }}</b></div>
  <div class="stat"><span>ดาวน์โหลดวันนี้</span><b>{{ "{:,}".format(t.today) }}</b></div>
  <div class="stat"><span>7 วันล่าสุด</span><b>{{ "{:,}".format(t.week) }}</b></div>
  <div class="stat"><span>Windows / Mac</span><b>{{ t.win }} / {{ t.mac }}</b></div>
  <div class="stat"><span>ตัวติดตั้ง / คำสั่ง / zip</span><b>{{ t.inst }} / {{ t.cli }} / {{ t.zip }}</b></div>
  <div class="stat"><span>เปิดโปรแกรมวันนี้</span><b>{{ "{:,}".format(t.opens_today) }}</b></div>
  <div class="stat"><span>อีเมลที่ยินยอม</span><b>{{ "{:,}".format(t.subs) }}</b></div>
</div>

<h2>14 วันล่าสุด</h2>
<div class="scroll"><table>
<tr><th>วันที่</th><th>Windows</th><th>Mac</th><th>รวม</th><th></th><th>เปิดโปรแกรม</th></tr>
{% for d in days %}
<tr><td>{{ d.day }}</td><td>{{ d.win }}</td><td>{{ d.mac }}</td><td>{{ d.win + d.mac }}</td>
<td style="width:30%"><span class="bar" style="width:{{ d.wpct }}%"></span><span class="bar mac" style="width:{{ d.mpct }}%"></span></td>
<td>{{ d.opens }}</td></tr>
{% endfor %}
</table></div>

<h2>เวอร์ชันที่ผู้ใช้เปิดใช้ (7 วันล่าสุด)</h2>
<table><tr><th>เวอร์ชัน</th><th>ระบบ</th><th>จำนวนครั้งที่เปิด</th></tr>
{% for v in versions %}<tr><td>{{ v.version }}</td><td>{{ v.os }}</td><td>{{ v.n }}</td></tr>{% else %}
<tr><td colspan="3" class="muted">ยังไม่มีข้อมูล</td></tr>{% endfor %}</table>

<h2>อีเมลผู้สมัครรับข่าว ({{ t.subs }})
  <a class="btn" href="/admin/export.csv" style="font-size:.9rem;margin-left:8px">ดาวน์โหลด CSV</a></h2>
<p class="muted">ทุกคนในรายการนี้ติ๊กยินยอมรับข่าวและข้อเสนอแล้ว ถ้ามีคนขอยกเลิกทาง Line OA ให้กดลบ</p>
<div class="scroll"><table><tr><th>อีเมล</th><th>ระบบ</th><th>วันที่สมัคร</th><th></th></tr>
{% for s in subs %}<tr><td>{{ s.email }}</td><td>{{ s.os }}</td><td>{{ s.ts[:16].replace("T", " ") }}</td>
<td><form method="post" action="/admin/subscribers/{{ s.id }}/delete" onsubmit="return confirm('ลบ {{ s.email }}?')">
<input type="hidden" name="csrf" value="{{ csrf }}"><button class="del">ลบ</button></form></td></tr>
{% else %}<tr><td colspan="4" class="muted">ยังไม่มีผู้สมัคร</td></tr>{% endfor %}</table></div>

<h2>ดาวน์โหลดล่าสุด 50 รายการ</h2>
<p class="muted">IP จะถูกลบอัตโนมัติเมื่อเก่ากว่า {{ retention }} วัน</p>
<div class="scroll"><table><tr><th>เวลา</th><th>ระบบ</th><th>ช่องทาง</th><th>เวอร์ชัน</th><th>IP</th></tr>
{% for d in recent %}<tr><td>{{ d.ts[:16].replace("T", " ") }}</td><td>{{ d.os }}</td><td>{{ {"installer": "ตัวติดตั้ง", "cli": "คำสั่ง"}.get(d.src, "zip") }}</td>
<td>{{ d.version }}</td><td>{{ d.ip or "-" }}</td></tr>
{% else %}<tr><td colspan="5" class="muted">ยังไม่มีการดาวน์โหลด</td></tr>{% endfor %}</table></div>
</div>
"""


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        ip = client_ip()
        if limited("login:" + ip, 5, 900):
            error = "ลองผิดหลายครั้งเกินไป รอ 15 นาที"
        elif ADMIN_PASSWORD and hmac.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session.clear()
            session["admin"] = True
            session["csrf"] = secrets.token_hex(16)
            session.permanent = True
            return redirect("/admin")
        else:
            time.sleep(1)
            error = "รหัสผ่านไม่ถูกต้อง"
    return render_template_string(LOGIN_HTML, error=error, configured=bool(ADMIN_PASSWORD))


@app.post("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")


@app.get("/admin")
@admin_required
def admin():
    purge_old_ips()
    today = now().date()
    days14 = [(today - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    with db() as c:
        q = lambda sql, *a: c.execute(sql, a).fetchone()[0]
        t = {
            "total": q("SELECT COUNT(*) FROM downloads"),
            "today": q("SELECT COUNT(*) FROM downloads WHERE day=?", today.isoformat()),
            "week": q("SELECT COUNT(*) FROM downloads WHERE day>=?", days14[7]),
            "win": q("SELECT COUNT(*) FROM downloads WHERE os='windows'"),
            "mac": q("SELECT COUNT(*) FROM downloads WHERE os='mac'"),
            "inst": q("SELECT COUNT(*) FROM downloads WHERE src='installer'"),
            "cli": q("SELECT COUNT(*) FROM downloads WHERE src='cli'"),
            "zip": q("SELECT COUNT(*) FROM downloads WHERE src IN ('zip','web')"),
            "opens_today": q("SELECT COALESCE(SUM(n),0) FROM opens WHERE day=?", today.isoformat()),
            "subs": q("SELECT COUNT(*) FROM subscribers"),
        }
        per = {d: {"day": d, "win": 0, "mac": 0, "opens": 0} for d in days14}
        for r in c.execute("SELECT day, os, COUNT(*) n FROM downloads WHERE day>=? GROUP BY day, os", (days14[0],)):
            if r["day"] in per:
                per[r["day"]]["win" if r["os"] == "windows" else "mac"] = r["n"]
        for r in c.execute("SELECT day, SUM(n) n FROM opens WHERE day>=? GROUP BY day", (days14[0],)):
            if r["day"] in per:
                per[r["day"]]["opens"] = r["n"]
        mx = max([d["win"] + d["mac"] for d in per.values()] + [1])
        for d in per.values():
            d["wpct"], d["mpct"] = round(d["win"] / mx * 100), round(d["mac"] / mx * 100)
        versions = c.execute("SELECT version, os, SUM(n) n FROM opens WHERE day>=? GROUP BY version, os "
                             "ORDER BY n DESC", (days14[7],)).fetchall()
        subs = c.execute("SELECT * FROM subscribers ORDER BY ts DESC").fetchall()
        recent = c.execute("SELECT * FROM downloads ORDER BY id DESC LIMIT 50").fetchall()
    return render_template_string(DASH_HTML, t=t, days=list(per.values())[::-1], versions=versions, subs=subs,
                                  recent=recent, csrf=session["csrf"], retention=IP_RETENTION_DAYS)


@app.get("/admin/export.csv")
@admin_required
def export_csv():
    buf = io.StringIO()
    buf.write("\ufeff")  # ให้ Excel อ่านภาษาไทยได้
    w = csv.writer(buf)
    w.writerow(["email", "os", "subscribed_at", "consent"])
    with db() as c:
        for r in c.execute("SELECT email, os, ts, consent FROM subscribers ORDER BY ts"):
            w.writerow([r["email"], r["os"], r["ts"], r["consent"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=pirimu-subscribers.csv"})


@app.post("/admin/subscribers/<int:sid>/delete")
@admin_required
def delete_subscriber(sid):
    check_csrf()
    with db() as c:
        c.execute("DELETE FROM subscribers WHERE id=?", (sid,))
    return redirect("/admin")
