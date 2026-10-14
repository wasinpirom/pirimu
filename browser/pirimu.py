"""
PiriMU — เว็บบราวเซอร์สำหรับสายมู โดย ดร.วศิน ภิรมย์  (https://pirimu.com)
Python + PyQt6 (Chromium engine) — ไม่ใช้ AI API ใดๆ ทุกอย่างคำนวณในเครื่อง

จุดเด่น:
  ✨ ธีมสีมงคลประจำวัน เปลี่ยนเองอัตโนมัติทุกวัน (จันทร์เหลือง อังคารชมพู ...)
  👑 ธีมทองคำ เงิน นาก | 💎 ธีมอัญมณีนพเก้า 9 เม็ด + นพเก้ารวม
  🐼 ธีมสัตว์น่ารัก 19 แบบ ครบ 12 นักษัตร (มีหู มีจมูก มีรอยยิ้ม)
  🔮 หมอดูปิริ: ดวงรายวันจากวันเกิด, วิเคราะห์เลขมงคล, เขย่าเซียมซี, ปีนักษัตร/ปีชง
  🔢 คลิกขวาที่ตัวเลขบนเว็บ (เบอร์โทร ทะเบียนรถ) → ดูเลขมงคลทันที
  🪷 ปัดเป่าสิ่งอัปมงคล (บล็อกโฆษณาและตัวติดตาม) | 🌙 โหมดมืด | 🧅 Proxy/Tor
  ⭐ แท็บ บุ๊กมาร์ก ประวัติ ดาวน์โหลด | 🆕 แจ้งเตือนเวอร์ชันใหม่จาก pirimu.com

ติดตั้ง:  pip install PyQt6 PyQt6-WebEngine
รัน:      python pirimu.py

อัปเดตเวอร์ชัน: แก้ APP_VERSION ด้านล่าง แล้ว push ขึ้น GitHub + Redeploy ใน Coolify
เว็บจะสร้าง version.json ให้อัตโนมัติ และเบราว์เซอร์ของผู้ใช้จะแจ้งว่ามีเวอร์ชันใหม่

คีย์ลัด: Ctrl+T แท็บใหม่ | Ctrl+W ปิดแท็บ | Ctrl+L แถบ URL | F5 รีโหลด | Alt+←/→
         Ctrl+D บุ๊กมาร์ก | Ctrl+H ประวัติ | Ctrl+=/-/0 ซูม | Ctrl+J หมอดูปิริ | F12 DevTools
"""
import sys
import os
import json
import random
import hashlib
from datetime import datetime, date
from pathlib import Path
from urllib.parse import quote_plus

from PyQt6.QtCore import QUrl, Qt, QTimer, QPointF, QDate
from PyQt6.QtGui import (
    QAction, QActionGroup, QKeySequence, QIcon, QPainter, QColor, QPainterPath, QPen, QPolygonF,
)
from PyQt6.QtNetwork import QNetworkProxy, QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QLineEdit, QMenu,
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QProgressBar, QFileDialog, QPushButton, QDockWidget, QWidget,
    QTextBrowser, QFormLayout, QDialogButtonBox, QLabel, QComboBox, QSpinBox,
    QCheckBox, QDateEdit, QSizePolicy, QMessageBox,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineSettings, QWebEngineUrlRequestInterceptor,
)

APP_NAME = "PiriMU"
APP_VERSION = "1.2.0"
HOME_URL = "https://pirimu.com"
GUIDE_URL = "https://pirimu.com/guide.html"
ABOUT_TEXT = "PiriMU — เว็บบราวเซอร์สำหรับสายมู\nโดย ดร.วศิน ภิรมย์\n\nใช้ฟรี · pirimu.com\nแจ้งปัญหาได้ที่ ดร.วศิน ภิรมย์ Line OA: @wasin"
APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))  # รองรับตอนแพ็กเป็น .exe/.app
VERSION_URL = "https://pirimu.com/version.json"
SEARCH_URL = "https://www.google.com/search?q={}"
DATA_DIR = Path.home() / ".pirimu"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
HISTORY_FILE = DATA_DIR / "history.json"
CONFIG_FILE = DATA_DIR / "config.json"
MAX_HISTORY = 1000

DEFAULT_CONFIG = {
    "theme": "auto_day",
    "birthdate": "",
    "adblock": True,
    "dark_mode": False,
    "proxy_type": "none",
    "proxy_host": "127.0.0.1",
    "proxy_port": 9150,
}


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def mix(hex_color, t, target=(255, 255, 255)):
    """ผสมสีเข้าหาสีขาว (หรือ target) ตามสัดส่วน t (0-1)"""
    c = QColor(hex_color)
    r, g, b = (round(a + (b_ - a) * t) for a, b_ in zip((c.red(), c.green(), c.blue()), target))
    return QColor(r, g, b).name()


def darken(hex_color, t):
    return mix(hex_color, t, (0, 0, 0))


# ======================= Themes =======================
def T(name, bg, face, dark, acc, txt, kind):
    return {"name": name, "bg": bg, "face": face, "dark": dark, "acc": acc, "txt": txt, "kind": kind}


DAY_NAMES = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]   # index = date.weekday()
DAY_COLORS = ["เหลือง", "ชมพู", "เขียว", "ส้ม", "ฟ้า", "ม่วง", "แดง"]
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

DAY_THEMES = {
    "mon": T("🌕 จันทร์ · เหลือง", "#FFF9DB", "#FFD43B", "#8A6D00", "#FFFFFF", "#4A3A00", "day"),
    "tue": T("🌸 อังคาร · ชมพู", "#FFF0F6", "#F783AC", "#A61E4D", "#FFFFFF", "#5C0F2B", "day"),
    "wed": T("🍀 พุธ · เขียว", "#EBFBEE", "#51CF66", "#2B8A3E", "#FFFFFF", "#123D1D", "day"),
    "thu": T("🍊 พฤหัสบดี · ส้ม", "#FFF4E6", "#FF922B", "#A84B00", "#FFFFFF", "#4A2100", "day"),
    "fri": T("💧 ศุกร์ · ฟ้า", "#E7F5FF", "#74C0FC", "#1864AB", "#FFFFFF", "#0B2E52", "day"),
    "sat": T("🔮 เสาร์ · ม่วง", "#F3F0FF", "#9775FA", "#5F3DC4", "#FFFFFF", "#FFFFFF", "day"),
    "sun": T("☀️ อาทิตย์ · แดง", "#FFF5F5", "#FA5252", "#A51111", "#FFE8A3", "#FFFFFF", "day"),
}

LUX_THEMES = {
    "gold": T("👑 ทองคำ", "#FFF8E1", "#E6B422", "#8A6100", "#FFF3B0", "#3D2A00", "lux"),
    "silver": T("🥈 เงิน", "#F4F5F7", "#C9CED6", "#6B7280", "#FFFFFF", "#1F2937", "lux"),
    "nak": T("🌹 นาก", "#FFF1EC", "#D9967A", "#8C4A33", "#FFE3D6", "#3D1A0E", "lux"),
}


def gem(name, color, txt="#FFFFFF"):
    return T(name, mix(color, 0.88), color, darken(color, 0.45), "#FFFFFF", txt, "gem")


GEM_THEMES = {
    "diamond": gem("💎 เพชร", "#D6ECFF", "#1E3A5F"),
    "ruby": gem("❤️ ทับทิม", "#D0104C"),
    "emerald": gem("💚 มรกต", "#169B62"),
    "topaz": gem("💛 บุษราคัม", "#F2C200", "#3D3000"),
    "garnet": gem("🍷 โกเมน", "#7E1F3A"),
    "sapphire": gem("💙 ไพลิน", "#1F4FA8"),
    "moonstone": gem("🤍 มุกดา", "#CFC6EE", "#2E2552"),
    "zircon": gem("🧡 เพทาย", "#C07A36"),
    "catseye": gem("👁️ ไพฑูรย์", "#A3A86A", "#2A2C12"),
}
NAVARATNA = T("🌟 นพเก้ารวม 9 เม็ด", "#FFF8E1", "#E6B422", "#8A6100", "#FFF3B0", "#3D2A00", "navaratna")

ANIMAL_THEMES = {
    "panda": T("🐼 หมีแพนด้า", "#E3F1DD", "#FFFFFF", "#2B2B2B", "#F4A9C0", "#2B2B2B", "animal"),
    "tiger": T("🐯 เสือ", "#FFF3DF", "#F28C28", "#3B2412", "#FFF3E0", "#3B2412", "animal"),
    "lion": T("🦁 สิงโต", "#FFF6E0", "#F2C46D", "#B5651D", "#8A4A12", "#5A3108", "animal"),
    "bull": T("🐂 กระทิง", "#F2E8DC", "#7A4A2E", "#3B2416", "#F3E3C3", "#FFF4E6", "animal"),
    "rhino": T("🦏 แรด", "#EDF1F4", "#9AA3AD", "#4B5563", "#E5E7EB", "#1F2937", "animal"),
    "buffalo": T("🐃 ควาย", "#E6EEDC", "#4A4A4A", "#1F1F1F", "#D9CBB0", "#F5F0E6", "animal"),
    "elephant": T("🐘 ช้าง", "#EEF1F6", "#A7B4C2", "#5B6B7C", "#F2C9D4", "#1F2A37", "animal"),
    "pig": T("🐷 หมู", "#FFF0F4", "#F7B6C8", "#C9607F", "#FFE1EA", "#6B1E36", "animal"),
    "dog": T("🐶 หมา", "#FBF1E4", "#E3B47A", "#7A4E26", "#F28BA0", "#3B2412", "animal"),
    "cat": T("🐱 แมว", "#FFF4E6", "#FFB347", "#6B3E10", "#FFC9D6", "#3B2108", "animal"),
    "turtle": T("🐢 เต่า", "#E8F6EC", "#7BC67B", "#2F6B2F", "#C8E6A0", "#16361A", "animal"),
    "rat": T("🐭 หนู", "#F3F3F7", "#B8B8C4", "#55556A", "#F7B6C8", "#22222E", "animal"),
    "rabbit": T("🐰 กระต่าย", "#FDF2F8", "#FFFFFF", "#8A7F8F", "#F7B6C8", "#3A3340", "animal"),
    "dragon": T("🐲 มังกร", "#FFF5F5", "#E03131", "#7A0A0A", "#FFD43B", "#FFF4D6", "animal"),
    "snake": T("🐍 งู", "#EEFBF1", "#69DB7C", "#2B8A3E", "#FF6B6B", "#0F3A1B", "animal"),
    "horse": T("🐴 ม้า", "#FBF1E8", "#A0522D", "#4A2511", "#F3D9B1", "#FFF4E6", "animal"),
    "goat": T("🐐 แพะ", "#F8F5EC", "#F1EAD8", "#7A6A4F", "#C9B48A", "#3A3020", "animal"),
    "monkey": T("🐵 ลิง", "#FBF3EA", "#A9744F", "#5A3820", "#F3D3B0", "#FFF4E6", "animal"),
    "rooster": T("🐔 ไก่", "#FFFBEF", "#FFF8E7", "#B5651D", "#E03131", "#4A2A0A", "animal"),
}
ZODIAC_MENU = ["rat", "bull", "tiger", "rabbit", "dragon", "snake", "horse", "goat", "monkey", "rooster", "dog", "pig"]
ZODIAC_LABEL = ["ชวด", "ฉลู", "ขาล", "เถาะ", "มะโรง", "มะเส็ง", "มะเมีย", "มะแม", "วอก", "ระกา", "จอ", "กุน"]
CUTE_MENU = ["panda", "lion", "rhino", "buffalo", "elephant", "cat", "turtle"]

THEMES = {**DAY_THEMES, **LUX_THEMES, **GEM_THEMES, "navaratna": NAVARATNA, **ANIMAL_THEMES}


def effective_theme(config):
    key = config.get("theme", "auto_day")
    if key == "auto_day" or key not in THEMES:
        key = DAY_KEYS[date.today().weekday()]
    return key, THEMES[key]


def theme_stylesheet(t):
    focus = t["dark"] if t["kind"] != "animal" else "#3b82f6"
    return f"""
QMainWindow, QMenuBar, QToolBar#ears {{ background: {t['bg']}; }}
QMenuBar {{ color: {t['dark']}; }}
QMenuBar::item:selected {{ background: {t['face']}; color: {t['txt']}; border-radius: 6px; }}
QToolBar#nav {{ background: {t['face']}; border: 2px solid {t['dark']}; border-radius: 14px;
               margin: 0 8px; padding: 6px; spacing: 4px; }}
QToolBar#ears {{ border: none; padding: 0; margin: 0; }}
QToolButton {{ color: {t['txt']}; font-size: 16px; padding: 4px 8px; border-radius: 8px; }}
QToolButton:hover {{ background: rgba(127,127,127,0.25); }}
QLineEdit {{ background: #fff; color: #222; padding: 6px 14px; border-radius: 15px;
            border: 2px solid {t['dark']}; font-size: 14px; }}
QLineEdit:focus {{ border-color: {focus}; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: {t['bg']}; color: {t['dark']}; padding: 6px 12px; min-width: 90px;
               border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 2px; }}
QTabBar::tab:selected {{ background: #fff; }}
QStatusBar {{ background: {t['bg']}; color: {t['dark']}; }}
QStatusBar QPushButton {{ background: {t['face']}; color: {t['txt']}; border: 1px solid {t['dark']};
                         border-radius: 8px; padding: 2px 10px; }}
QDockWidget {{ color: {t['dark']}; }}
QDockWidget QPushButton {{ background: {t['face']}; color: {t['txt']}; padding: 8px; border-radius: 10px;
                          border: 1px solid {t['dark']}; font-size: 14px; }}
QDockWidget QPushButton:hover {{ background: {t['bg']}; color: {t['dark']}; }}
QTextBrowser {{ background: #fff; color: #222; font-size: 14px; border-radius: 10px; padding: 6px; }}
QLabel#bigNumber {{ color: {t['dark']}; font-size: 48px; }}
"""


# ======================= Decorations =======================
def sparkle(p, x, y, r, color):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    k = 0.28
    p.drawPolygon(QPolygonF([
        QPointF(x, y - r), QPointF(x + r * k, y - r * k), QPointF(x + r, y), QPointF(x + r * k, y + r * k),
        QPointF(x, y + r), QPointF(x - r * k, y + r * k), QPointF(x - r, y), QPointF(x - r * k, y - r * k),
    ]))


class EarsHeader(QWidget):
    """แถบบนสุด: หู/เขา (ธีมสัตว์), ดอกบัว (ธีมสีวัน/ทอง), อัญมณี (ธีมนพเก้า)"""

    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _):
        k, t = effective_theme(self.browser.config)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        w, h = self.width(), self.height()
        kind = t["kind"]
        if kind == "animal":
            self.paint_animal(p, k, t, w, h)
        elif kind in ("day", "lux"):
            self.paint_lotus(p, t, w, h)
        elif kind == "gem":
            self.paint_gem(p, t, w, h)
        elif kind == "navaratna":
            self.paint_navaratna(p, t, w, h)
        p.end()

    def paint_sparkles(self, p, w, color):
        for fx, y, r in ((0.12, 14, 7), (0.22, 30, 5), (0.33, 12, 4), (0.67, 12, 4), (0.78, 30, 5), (0.88, 14, 7)):
            sparkle(p, w * fx, y, r, color)

    def paint_lotus(self, p, t, w, h):
        self.paint_sparkles(p, w, t["dark"] if t["kind"] == "lux" else t["face"])
        cx, base = w / 2, h + 2
        face, dark = QColor(t["face"]), QColor(t["dark"])
        light = QColor(mix(t["face"], 0.55))
        for ang, color in ((-66, face), (66, face), (-34, light), (34, light), (0, face)):
            p.save()
            p.translate(cx, base)
            p.rotate(ang)
            p.setPen(QPen(dark, 1.5))
            p.setBrush(color)
            p.drawEllipse(QPointF(0, -21), 9, 21)
            p.restore()

    def paint_gem(self, p, t, w, h):
        self.paint_sparkles(p, w, t["dark"])
        cx = w / 2
        face, dark = QColor(t["face"]), QColor(t["dark"])
        p.setPen(QPen(dark, 1.8))
        p.setBrush(face)
        top, girdle, tip = 4, 16, h - 2
        p.drawPolygon(QPolygonF([QPointF(cx - 16, top), QPointF(cx + 16, top), QPointF(cx + 30, girdle),
                                 QPointF(cx, tip), QPointF(cx - 30, girdle)]))
        p.setPen(QPen(dark, 1))
        p.drawLine(QPointF(cx - 30, girdle), QPointF(cx + 30, girdle))
        for a, b in (((cx - 16, top), (cx - 8, girdle)), ((cx + 16, top), (cx + 8, girdle)),
                     ((cx - 8, girdle), (cx, tip)), ((cx + 8, girdle), (cx, tip)), ((cx, top), (cx - 8, girdle)),
                     ((cx, top), (cx + 8, girdle))):
            p.drawLine(QPointF(*a), QPointF(*b))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawPolygon(QPolygonF([QPointF(cx - 12, top + 2), QPointF(cx - 4, top + 2), QPointF(cx - 10, girdle - 2)]))

    def paint_navaratna(self, p, t, w, h):
        self.paint_sparkles(p, w, t["dark"])
        colors = [g["face"] for g in GEM_THEMES.values()]
        n = len(colors)
        for i, c in enumerate(colors):
            x = w * (0.30 + 0.40 * i / (n - 1))
            y = h - 12 - (6 if i == n // 2 else 0)
            p.setPen(QPen(QColor(t["dark"]), 1.5))
            p.setBrush(QColor(c))
            p.drawEllipse(QPointF(x, y), 10, 10)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 210))
            p.drawEllipse(QPointF(x - 3, y - 3), 3, 3)

    def paint_animal(self, p, k, t, w, h):
        L, R, B = w * 0.30, w * 0.70, h + 4
        dark, face, acc = QColor(t["dark"]), QColor(t["face"]), QColor(t["acc"])

        def circle(x, y, r, color):
            p.setBrush(color)
            p.drawEllipse(QPointF(x, y), r, r)

        if k == "panda":
            for x in (L, R):
                circle(x, B, 40, dark)
                circle(x, B, 20, QColor("#555555"))
        elif k == "tiger":
            for x in (L, R):
                circle(x, B, 40, dark)
                circle(x, B, 35, face)
                circle(x, B, 17, acc)
        elif k == "lion":
            x = 10
            while x < w:
                circle(x, B + 8, 24, dark)
                x += 34
            for x in (L, R):
                circle(x, B, 24, face)
        elif k == "bull":
            p.setBrush(acc)
            p.setPen(QPen(dark, 1.5))
            for sign, base in ((-1, w * 0.42), (1, w * 0.58)):
                path = QPainterPath(QPointF(base, h))
                path.quadTo(QPointF(base + sign * w * 0.12, h - 4), QPointF(base + sign * w * 0.20, 2))
                path.quadTo(QPointF(base + sign * w * 0.08, h - 14), QPointF(base - sign * 14, h))
                p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            for x in (w * 0.24, w * 0.76):
                p.setBrush(face)
                p.drawEllipse(QPointF(x, h), 26, 14)
        elif k == "rhino":
            for x in (L, R):
                circle(x, B, 26, dark)
            p.setBrush(acc)
            p.setPen(QPen(dark, 2))
            p.drawPolygon(QPolygonF([QPointF(w / 2 - 18, h), QPointF(w / 2, 1), QPointF(w / 2 + 18, h)]))
        elif k == "buffalo":
            p.setBrush(acc)
            p.setPen(QPen(dark, 1.5))
            for sign in (-1, 1):
                base = w / 2 + sign * 30
                path = QPainterPath(QPointF(base, h + 2))
                path.cubicTo(QPointF(base + sign * w * 0.18, h - 4), QPointF(base + sign * w * 0.30, h - 10),
                             QPointF(base + sign * w * 0.34, 3))
                path.cubicTo(QPointF(base + sign * w * 0.27, h - 18), QPointF(base + sign * w * 0.12, h - 12),
                             QPointF(base - sign * 6, h + 2))
                p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            for x in (w * 0.40, w * 0.60):
                p.setBrush(face)
                p.drawEllipse(QPointF(x, h + 2), 16, 10)
        elif k == "elephant":
            for x in (w * 0.18, w * 0.82):
                p.setBrush(dark)
                p.drawEllipse(QPointF(x, h + 8), w * 0.13, 34)
                p.setBrush(acc)
                p.drawEllipse(QPointF(x, h + 10), w * 0.09, 24)
        elif k in ("cat", "pig"):
            for x, sign in ((L, -1), (R, 1)):
                tip = 12 if k == "pig" else 0
                p.setPen(QPen(dark, 2) if k == "pig" else Qt.PenStyle.NoPen)
                p.setBrush(face if k == "pig" else dark)
                p.drawPolygon(QPolygonF([QPointF(x - 24, h + 4), QPointF(x + sign * tip, 2), QPointF(x + 24, h + 4)]))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(acc)
                p.drawPolygon(QPolygonF([QPointF(x - 12, h + 4), QPointF(x + sign * tip * 0.6, 12),
                                         QPointF(x + 12, h + 4)]))
        elif k == "dog":
            for x, sign in ((L, -1), (R, 1)):
                p.save()
                p.translate(x, h + 4)
                p.rotate(sign * 25)
                p.setBrush(dark)
                p.drawEllipse(QPointF(0, -10), 16, 26)
                p.restore()
        elif k == "turtle":
            p.setBrush(dark)
            p.drawEllipse(QPointF(w / 2, h + 10), w * 0.22, 40)
            p.setBrush(acc)
            for dx, dy in ((0, 14), (-w * 0.1, 22), (w * 0.1, 22), (-w * 0.05, 28), (w * 0.05, 28)):
                p.drawEllipse(QPointF(w / 2 + dx, dy), 11, 7)
        elif k == "rat":
            for x in (L, R):
                circle(x, h - 4, 30, dark)
                circle(x, h - 4, 24, face)
                circle(x, h - 4, 15, acc)
        elif k == "rabbit":
            for x, sign in ((w * 0.42, -1), (w * 0.58, 1)):
                p.save()
                p.translate(x, h + 6)
                p.rotate(sign * 8)
                p.setPen(QPen(dark, 2))
                p.setBrush(face)
                p.drawEllipse(QPointF(0, -24), 13, 30)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(acc)
                p.drawEllipse(QPointF(0, -22), 6, 22)
                p.restore()
        elif k == "dragon":
            pen = QPen(acc, 6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            for sign in (-1, 1):
                bx = w / 2 + sign * 40
                p.drawLine(QPointF(bx, h + 2), QPointF(bx + sign * 30, 6))
                p.drawLine(QPointF(bx + sign * 14, h - 16), QPointF(bx + sign * 40, h - 22))
                p.drawLine(QPointF(bx + sign * 22, 18), QPointF(bx + sign * 14, 4))
            p.setPen(Qt.PenStyle.NoPen)
            for i in range(-3, 4):
                x = w / 2 + i * 14
                p.setBrush(dark)
                p.drawPolygon(QPolygonF([QPointF(x - 6, h + 2), QPointF(x, h - 12 - (4 if i == 0 else 0)),
                                         QPointF(x + 6, h + 2)]))
        elif k == "snake":
            x = w * 0.18
            path = QPainterPath(QPointF(x, h - 8))
            step = w * 0.08
            up = True
            while x < w * 0.74:
                path.quadTo(QPointF(x + step / 2, 6 if up else h + 4), QPointF(x + step, h - 8))
                x += step
                up = not up
            for color, width in ((dark, 14), (face, 9)):
                pen = QPen(color, width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(path)
            hx = x + 10
            p.setPen(QPen(dark, 2))
            p.setBrush(face)
            p.drawEllipse(QPointF(hx, h - 10), 14, 11)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(dark)
            p.drawEllipse(QPointF(hx + 4, h - 13), 2.5, 2.5)
            p.setPen(QPen(acc, 2))
            p.drawLine(QPointF(hx + 14, h - 9), QPointF(hx + 24, h - 9))
            p.drawLine(QPointF(hx + 24, h - 9), QPointF(hx + 29, h - 13))
            p.drawLine(QPointF(hx + 24, h - 9), QPointF(hx + 29, h - 5))
        elif k == "horse":
            for x in (L, R):
                p.setPen(QPen(dark, 2))
                p.setBrush(face)
                p.drawPolygon(QPolygonF([QPointF(x - 14, h + 4), QPointF(x, 2), QPointF(x + 14, h + 4)]))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(acc)
                p.drawPolygon(QPolygonF([QPointF(x - 6, h + 4), QPointF(x, 14), QPointF(x + 6, h + 4)]))
            p.setBrush(dark)
            for i, dx in enumerate((-30, -12, 6, 24)):
                p.drawEllipse(QPointF(w / 2 + dx, h - 6 - (i % 2) * 4), 14, 12)
        elif k == "goat":
            pen = QPen(acc, 7)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            for sign in (-1, 1):
                bx = w / 2 + sign * 26
                horn = QPainterPath(QPointF(bx, h + 2))
                horn.cubicTo(QPointF(bx + sign * 4, 0), QPointF(bx + sign * 40, 0), QPointF(bx + sign * 34, 22))
                horn.quadTo(QPointF(bx + sign * 28, 30), QPointF(bx + sign * 20, 22))
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(horn)
            p.setPen(QPen(dark, 2))
            p.setBrush(face)
            for x, sign in ((w * 0.36, -1), (w * 0.64, 1)):
                p.save()
                p.translate(x, h)
                p.rotate(sign * 70)
                p.drawEllipse(QPointF(0, -14), 9, 18)
                p.restore()
        elif k == "monkey":
            for x in (w * 0.16, w * 0.84):
                circle(x, h - 2, 30, face)
                circle(x, h - 2, 18, acc)
            p.setBrush(dark)
            for dx in (-10, 0, 10):
                p.drawEllipse(QPointF(w / 2 + dx, h - 4 - (6 if dx == 0 else 0)), 8, 12)
        elif k == "rooster":
            p.setPen(QPen(QColor(darken(t["acc"], 0.3)), 2))
            p.setBrush(acc)
            for dx, r in ((-26, 13), (-8, 17), (12, 15), (28, 11)):
                p.drawEllipse(QPointF(w / 2 + dx, h - 10), r, r)


class SmileFooter(QWidget):
    """แถบล่าง: จมูกกับรอยยิ้ม"""

    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setFixedHeight(30)

    def paintEvent(self, _):
        k, t = effective_theme(self.browser.config)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx = w / 2
        p.setPen(QPen(QColor(t["dark"]), 2))
        p.setBrush(QColor(t["face"]))
        p.drawRoundedRect(8, 1, w - 16, h - 3, 12, 12)

        if k == "pig":
            p.setPen(QPen(QColor(t["dark"]), 1.5))
            p.setBrush(QColor(t["acc"]))
            p.drawEllipse(QPointF(cx, h / 2), 20, 10)
            p.setBrush(QColor(t["dark"]))
            p.drawEllipse(QPointF(cx - 7, h / 2), 3, 4)
            p.drawEllipse(QPointF(cx + 7, h / 2), 3, 4)
            p.end()
            return

        line = QColor(t["acc"] if k in ("bull", "buffalo") else t["dark"])
        if t["kind"] == "animal":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(line)
            p.drawEllipse(QPointF(cx, 9), 8, 5)
        path = QPainterPath(QPointF(cx - 18, 14))
        path.quadTo(QPointF(cx - 9, 26), QPointF(cx, 14))
        path.quadTo(QPointF(cx + 9, 26), QPointF(cx + 18, 14))
        pen = QPen(line, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        if k == "panda" or t["kind"] != "animal":   # แก้มชมพู
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#F4A9C0"))
            p.drawEllipse(QPointF(cx - 40, 15), 7, 4)
            p.drawEllipse(QPointF(cx + 40, 15), 7, 4)
        if k == "cat":
            p.setPen(QPen(line, 1.5))
            for dy in (-4, 2, 8):
                p.drawLine(QPointF(cx - 28, 12 + dy / 2), QPointF(cx - 70, 10 + dy))
                p.drawLine(QPointF(cx + 28, 12 + dy / 2), QPointF(cx + 70, 10 + dy))
        if k == "dog":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t["acc"]))
            p.drawEllipse(QPointF(cx + 5, 23), 5, 5)
        if k in ("rat", "rabbit"):
            p.setPen(QPen(QColor(t["dark"]), 1.2))
            for dy in (-3, 3):
                p.drawLine(QPointF(cx - 24, 11 + dy / 2), QPointF(cx - 58, 9 + dy))
                p.drawLine(QPointF(cx + 24, 11 + dy / 2), QPointF(cx + 58, 9 + dy))
        if k == "rabbit":
            p.setPen(QPen(QColor(t["dark"]), 1))
            p.setBrush(QColor("#FFFFFF"))
            p.drawRect(int(cx - 5), 19, 5, 6)
            p.drawRect(int(cx), 19, 5, 6)
        if k == "dragon":
            pen = QPen(QColor(t["acc"]), 2.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            for sign in (-1, 1):
                wh = QPainterPath(QPointF(cx + sign * 12, 10))
                wh.cubicTo(QPointF(cx + sign * 40, 2), QPointF(cx + sign * 50, 26), QPointF(cx + sign * 80, 14))
                p.drawPath(wh)
        if k == "snake":
            p.setPen(QPen(QColor(t["acc"]), 2))
            p.drawLine(QPointF(cx, 21), QPointF(cx, 27))
            p.drawLine(QPointF(cx, 27), QPointF(cx - 4, 29))
            p.drawLine(QPointF(cx, 27), QPointF(cx + 4, 29))
        if k == "horse":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t["acc"]))
            p.drawEllipse(QPointF(cx - 30, 14), 5, 4)
            p.drawEllipse(QPointF(cx + 30, 14), 5, 4)
        if k == "goat":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t["acc"]))
            p.drawPolygon(QPolygonF([QPointF(cx - 6, 22), QPointF(cx + 6, 22), QPointF(cx, 29)]))
        if k == "monkey":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t["acc"]))
            p.drawEllipse(QPointF(cx - 34, 15), 10, 7)
            p.drawEllipse(QPointF(cx + 34, 15), 10, 7)
        if k == "rooster":
            p.setPen(QPen(QColor(t["dark"]), 1.5))
            p.setBrush(QColor("#FFC107"))
            p.drawPolygon(QPolygonF([QPointF(cx - 30, 10), QPointF(cx - 30, 20), QPointF(cx - 42, 15)]))
        if k == "elephant":
            pen = QPen(QColor(t["dark"]), 5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            trunk = QPainterPath(QPointF(cx + 26, 6))
            trunk.cubicTo(QPointF(cx + 40, 6), QPointF(cx + 46, 24), QPointF(cx + 58, 20))
            p.drawPath(trunk)
        p.end()


# ======================= หมอดูปิริ (rule-based ทั้งหมด) =======================
PLANETS = {
    1: ("อาทิตย์", "ความเป็นผู้นำ มีเกียรติ คนนับหน้าถือตา"),
    2: ("จันทร์", "อ่อนโยน มีเสน่ห์ คนรอบข้างรักใคร่"),
    3: ("อังคาร", "กล้าหาญ ขยัน ลงมือทำจริง"),
    4: ("พุธ", "เจรจาเก่ง ค้าขายคล่อง สื่อสารดี"),
    5: ("พฤหัสบดี", "ปัญญาดี ผู้ใหญ่เมตตา เหมาะกับการเรียนรู้"),
    6: ("ศุกร์", "โชคลาภ ความรัก ความสวยงาม ศิลปะ"),
    7: ("เสาร์", "อดทน หนักแน่น สำเร็จด้วยความพยายาม"),
    8: ("ราหู", "ไหวพริบดี กล้าเสี่ยง แต่ควรระวังความใจร้อน"),
    9: ("เกตุ", "สิ่งศักดิ์สิทธิ์คุ้มครอง ลางสังหรณ์แม่น"),
}
SUM_LEVEL = {5: "ดีมาก ✨", 6: "ดีมาก ✨", 9: "ดีมาก ✨", 1: "ดี 👍", 2: "ดี 👍", 4: "ดี 👍",
             3: "กลางๆ 🙂", 7: "ต้องอาศัยความอดทน 💪", 8: "ลุ้นๆ ต้องมีสติ 🧘"}

FORTUNE_TEXT = {
    "ภาพรวม": ["วันนี้พลังบวกล้นเหลือ ทำอะไรก็ราบรื่น", "มีเรื่องให้ตัดสินใจ ใจเย็นแล้วจะเลือกถูก",
              "เจอคนดีช่วยเหลือโดยไม่คาดคิด", "ควรพักบ้าง อย่าแบกทุกอย่างไว้คนเดียว",
              "เรื่องค้างคาจะคลี่คลายในช่วงบ่าย", "ข่าวดีเล็กๆ ทำให้ยิ้มได้ทั้งวัน"],
    "การงาน": ["งานที่ทำไว้เริ่มเห็นผล ผู้ใหญ่สังเกตเห็น", "มีงานด่วนแทรก ทำทีละอย่างจะเสร็จไว",
               "ไอเดียใหม่ใช้ได้จริง กล้าเสนอเลย", "ระวังการสื่อสารผิดพลาด ทวนให้ชัดก่อนส่ง",
               "ทีมเวิร์กดีเป็นพิเศษ ขอความช่วยเหลือได้", "เหมาะกับการวางแผนมากกว่าลงมือ"],
    "การเงิน": ["มีรายรับเข้ามาเล็กๆ น้อยๆ", "ระวังของชิ้นเล็กที่ซื้อเพลิน รวมแล้วไม่เล็ก",
                "เงินหมุนคล่อง แต่ควรเก็บออมสักส่วน", "มีคนนำโชคมาให้ผ่านการแนะนำ",
                "ยังไม่ใช่วันลงทุนก้อนใหญ่ รอจังหวะก่อน", "ได้คืนเงินหรือของที่คิดว่าหายไปแล้ว"],
    "ความรัก": ["เสน่ห์แรง มีคนแอบมองอยู่", "คนข้างกายต้องการเวลาจากคุณมากขึ้น",
                "คุยกันตรงๆ แล้วเรื่องค้างใจจะหายไป", "คนโสดมีโอกาสเจอคนคุยใหม่จากเพื่อนแนะนำ",
                "ความรักเรียบง่ายแต่อบอุ่น", "อย่าเอาอารมณ์จากเรื่องงานมาลงกับคนที่รัก"],
}
TIPS = ["ทำบุญด้วยการแบ่งปันของกินให้คนรอบตัว", "ใส่เครื่องประดับสีประจำวันเสริมดวง",
        "ไหว้พระก่อนออกจากบ้านสักนิด ใจจะนิ่ง", "จัดโต๊ะทำงานให้โล่ง พลังงานจะไหลดี",
        "ยิ้มให้คนแรกที่เจอวันนี้", "ดื่มน้ำให้เพียงพอ ร่างกายดีดวงก็ดี", "โทรหาพ่อแม่หรือคนที่คิดถึง"]

SEAMSI = [
    ("ดีมาก", "ดุจดอกบัวพ้นน้ำ สิ่งที่หวังจะสำเร็จสมใจ ผู้ใหญ่ให้การสนับสนุน"),
    ("ดีมาก", "ดุจลมพัดใบเรือ การเดินทางและการงานราบรื่น ลาภลอยเข้ามา"),
    ("ดีมาก", "ดุจพระจันทร์เต็มดวง ชื่อเสียงขจรไกล คนรักใคร่"),
    ("ดี", "ดุจต้นไม้ผลิใบ ค่อยเป็นค่อยไปแต่มั่นคง อดทนอีกนิด"),
    ("ดี", "ดุจนกได้รัง มีที่พึ่งพิง ครอบครัวอบอุ่น"),
    ("ดี", "ดุจน้ำซึมบ่อทราย เงินทองค่อยๆ เพิ่มพูน อย่าใจร้อน"),
    ("ดี", "ดุจได้แผนที่ขุมทรัพย์ มีคนแนะนำทางสว่าง ฟังผู้ใหญ่ไว้"),
    ("ดี", "ดุจฝนตกต้องตามฤดูกาล จังหวะเวลาเป็นใจ ลงมือได้"),
    ("ปานกลาง", "ดุจเดินบนทางคดเคี้ยว ถึงจุดหมายแน่แต่ต้องใช้เวลา"),
    ("ปานกลาง", "ดุจเมฆบังจันทร์ชั่วครู่ ปัญหาเล็กน้อยจะผ่านไปเอง"),
    ("ปานกลาง", "ดุจเรือรอน้ำขึ้น ยังไม่ถึงเวลา เตรียมตัวให้พร้อม"),
    ("ปานกลาง", "ดุจปลูกต้นกล้า ผลยังไม่เห็นวันนี้ แต่อนาคตงอกงาม"),
    ("ควรระวัง", "ดุจข้ามสะพานไม้ เดินช้าๆ ระวังคำพูดและการเซ็นเอกสาร"),
    ("ควรระวัง", "ดุจลมแรงพัดเทียน ระวังใจร้อน คิดก่อนพูดสามรอบ"),
    ("ควรระวัง", "ดุจหมอกยามเช้า เรื่องบางอย่างยังไม่ชัด อย่าเพิ่งตัดสินใจใหญ่"),
    ("ดีมาก", "ดุจมังกรได้น้ำ ความสามารถได้แสดงออกเต็มที่ โอกาสใหญ่มาถึง"),
    ("ดี", "ดุจเพื่อนแท้ยื่นมือ มีคนช่วยในยามจำเป็น อย่าอายที่จะขอ"),
    ("ดี", "ดุจตะเกียงในความมืด สติปัญญานำพาให้พ้นปัญหา"),
    ("ปานกลาง", "ดุจดอกไม้รอบาน รักและงานต้องการความใส่ใจอีกสักหน่อย"),
    ("ดีมาก", "ดุจพบแก้วสารพัดนึก สิ่งที่ตามหามานานกำลังจะพบ"),
]

ZODIAC = [("ชวด", "หนู", "🐭"), ("ฉลู", "วัว", "🐮"), ("ขาล", "เสือ", "🐯"), ("เถาะ", "กระต่าย", "🐰"),
          ("มะโรง", "งูใหญ่", "🐲"), ("มะเส็ง", "งูเล็ก", "🐍"), ("มะเมีย", "ม้า", "🐴"), ("มะแม", "แพะ", "🐐"),
          ("วอก", "ลิง", "🐵"), ("ระกา", "ไก่", "🐔"), ("จอ", "หมา", "🐶"), ("กุน", "หมู", "🐷")]
ZODIAC_THEME = dict(enumerate(ZODIAC_MENU))
DISCLAIMER = "\n\n---\n_🪷 เพื่อความบันเทิงและเป็นกำลังใจ โปรดใช้วิจารณญาณ_"


def zodiac_index(year):
    return (year - 4) % 12


def analyze_number(text):
    digits = [int(c) for c in text if c.isdigit()]
    if not digits:
        return None
    total = sum(digits)
    reduced = total
    while reduced > 9:
        reduced = sum(int(c) for c in str(reduced))
    lines = [f"### 🔢 {''.join(map(str, digits))}", f"**ผลรวม:** {total}" + (f" → {reduced}" if total > 9 else "")]
    if reduced == 0:
        lines.append("เลขศูนย์ล้วน ว่างเปล่าเหมือนกระดาษขาว เริ่มต้นใหม่ได้เสมอ")
    else:
        planet, meaning = PLANETS[reduced]
        lines += [f"**ดาวประจำผลรวม:** {planet} — {meaning}", f"**ระดับ:** {SUM_LEVEL[reduced]}"]
    counts = {d: digits.count(d) for d in range(1, 10) if d in digits}
    if counts:
        top = sorted(counts.items(), key=lambda x: -x[1])[:3]
        lines.append("\n**ดาวเด่นในตัวเลข:**")
        for d, c in top:
            lines.append(f"- เลข {d} ({PLANETS[d][0]}) ×{c}: {PLANETS[d][1]}")
    if digits.count(0) >= 3:
        lines.append("\n_มีเลข 0 หลายตัว พลังกระจาย ควรตั้งเป้าหมายให้ชัด_")
    return "\n".join(lines) + DISCLAIMER


def daily_fortune(birth, today):
    seed = int(hashlib.md5(f"{birth.isoformat()}|{today.isoformat()}".encode()).hexdigest(), 16)
    r = random.Random(seed)
    wd = today.weekday()
    out = [f"### วัน{DAY_NAMES[wd]}ที่ {today.day}/{today.month}/{today.year + 543}",
           f"คุณเกิดวัน**{DAY_NAMES[birth.weekday()]}** · สีประจำวันนี้: **{DAY_COLORS[wd]}**\n"]
    for topic, phrases in FORTUNE_TEXT.items():
        stars = r.randint(2, 5)
        out.append(f"**{topic}** {'★' * stars}{'☆' * (5 - stars)}  \n{r.choice(phrases)}\n")
    a, b = r.sample(range(10), 2)
    out.append(f"**เลขนำโชค:** {a}{b} · {b}{a}")
    out.append(f"**สีเสริมดวง:** {r.choice(DAY_COLORS)}")
    out.append(f"**คำแนะนำ:** {r.choice(TIPS)}")
    return "\n\n".join(out) + DISCLAIMER


class BirthDialog(QDialog):
    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser
        self.setWindowTitle("ตั้งวันเกิด")
        form = QFormLayout(self)
        self.edit = QDateEdit(calendarPopup=True, displayFormat="d MMMM yyyy")
        b = browser.birthdate()
        self.edit.setDate(QDate(b.year, b.month, b.day) if b else QDate(1990, 1, 1))
        form.addRow("วันเกิด (ค.ศ.):", self.edit)
        form.addRow(QLabel("<small>ข้อมูลเก็บในเครื่องคุณเท่านั้น ไม่ส่งไปที่ไหน</small>"))
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def save(self):
        self.browser.config["birthdate"] = self.edit.date().toPyDate().isoformat()
        self.browser.save_config()
        self.browser.mordu.refresh()
        self.accept()


class MorduSidebar(QTabWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

        # --- ดวงวันนี้ ---
        page = QWidget()
        lay = QVBoxLayout(page)
        self.fortune = QTextBrowser()
        set_birth = QPushButton("🎂 ตั้งวันเกิด")
        set_birth.clicked.connect(lambda: BirthDialog(browser).exec())
        lay.addWidget(self.fortune, 1)
        lay.addWidget(set_birth)
        self.addTab(page, "🌞 ดวงวันนี้")

        # --- เลขมงคล ---
        page = QWidget()
        lay = QVBoxLayout(page)
        row = QHBoxLayout()
        self.num_input = QLineEdit(placeholderText="เบอร์โทร / ทะเบียนรถ / บ้านเลขที่")
        self.num_input.returnPressed.connect(self.do_number)
        go = QPushButton("ดูเลข")
        go.clicked.connect(self.do_number)
        row.addWidget(self.num_input, 1)
        row.addWidget(go)
        self.num_out = QTextBrowser()
        self.num_out.setMarkdown("พิมพ์ตัวเลขแล้วกด **ดูเลข** หรือไฮไลต์ตัวเลขบนเว็บ แล้วคลิกขวา → **ดูเลขมงคล**")
        lay.addLayout(row)
        lay.addWidget(self.num_out, 1)
        self.addTab(page, "🔢 เลขมงคล")

        # --- เซียมซี ---
        page = QWidget()
        lay = QVBoxLayout(page)
        self.big = QLabel("🎋", objectName="bigNumber", alignment=Qt.AlignmentFlag.AlignCenter)
        self.seamsi_out = QTextBrowser()
        self.seamsi_out.setMarkdown("ตั้งจิตอธิษฐานถึงเรื่องที่อยากรู้ แล้วกด **เขย่าเซียมซี**")
        shake = QPushButton("🎋 เขย่าเซียมซี")
        shake.clicked.connect(self.shake)
        lay.addWidget(self.big)
        lay.addWidget(shake)
        lay.addWidget(self.seamsi_out, 1)
        self.addTab(page, "🎋 เซียมซี")
        self.shake_timer = QTimer(self, interval=70)
        self.shake_timer.timeout.connect(self._shake_tick)
        self.shake_left = 0

        # --- ปีนักษัตร ---
        page = QWidget()
        lay = QVBoxLayout(page)
        self.zodiac_out = QTextBrowser()
        self.zodiac_btn = QPushButton("ใช้ธีมสัตว์ประจำปีเกิด")
        self.zodiac_btn.clicked.connect(self.use_zodiac_theme)
        lay.addWidget(self.zodiac_out, 1)
        lay.addWidget(self.zodiac_btn)
        self.addTab(page, "🐉 นักษัตร")

        self.refresh()

    def refresh(self):
        birth = self.browser.birthdate()
        today = date.today()
        if birth:
            self.fortune.setMarkdown(daily_fortune(birth, today))
        else:
            wd = today.weekday()
            self.fortune.setMarkdown(
                f"### วันนี้วัน{DAY_NAMES[wd]} · สี{DAY_COLORS[wd]}\n\n"
                "ตั้ง **วันเกิด** ก่อน แล้วหมอดูปิริจะดูดวงให้ทุกวันครับ 🔮")
        this_year = zodiac_index(today.year)
        z = ZODIAC[this_year]
        text = [f"### ปีนี้ {today.year + 543}: ปี{z[0]} ({z[1]}) {z[2]}"]
        self.zodiac_btn.setVisible(False)
        if birth:
            idx = zodiac_index(birth.year)
            mz = ZODIAC[idx]
            text.append(f"คุณเกิดปี**{mz[0]}** ({mz[1]}) {mz[2]}")
            if idx == this_year:
                text.append("⚠️ **ปีกง** (ปีเดียวกับปีเกิด) ตามคติจีน ควรใจเย็นและระวังเรื่องสุขภาพ")
            elif (idx + 6) % 12 == this_year:
                text.append("⚠️ **ปีชงตรง** ตามคติจีน ควรเลี่ยงการตัดสินใจใหญ่แบบรีบร้อน ไหว้เทพเจ้าไท่ส่วยเสริมดวงได้")
            else:
                text.append("✅ ปีนี้ไม่ชงแบบตรงกับปีเกิดของคุณ")
            text.append("_หมายเหตุ: คิดจากปี ค.ศ. คนเกิดช่วงม.ค.–ก.พ. ก่อนตรุษจีนอาจเป็นปีก่อนหน้า_")
            self.zodiac_btn.setVisible(idx in ZODIAC_THEME)
            self.zodiac_idx = idx
        clash = ZODIAC[(this_year + 6) % 12]
        text.append(f"\nปีที่ชงตรงกับปีนี้: ปี{clash[0]} ({clash[1]}) {clash[2]}")
        self.zodiac_out.setMarkdown("\n\n".join(text) + DISCLAIMER)

    def do_number(self):
        res = analyze_number(self.num_input.text())
        self.num_out.setMarkdown(res or "ไม่พบตัวเลขครับ ลองพิมพ์ใหม่อีกครั้ง")

    def show_number(self, text):
        self.browser.mordu_dock.show()
        self.setCurrentIndex(1)
        self.num_input.setText(text.strip()[:60])
        self.do_number()

    def shake(self):
        self.browser.mordu_dock.show()
        self.setCurrentIndex(2)
        self.shake_left = 18
        self.shake_timer.start()

    def _shake_tick(self):
        self.shake_left -= 1
        n = random.randint(1, len(SEAMSI))
        self.big.setText(str(n))
        if self.shake_left <= 0:
            self.shake_timer.stop()
            level, text = SEAMSI[n - 1]
            self.seamsi_out.setMarkdown(f"### ใบที่ {n} · {level}\n\n{text}{DISCLAIMER}")

    def use_zodiac_theme(self):
        self.browser.set_theme(ZODIAC_THEME[self.zodiac_idx])


# ======================= Ad blocker (ปัดเป่าสิ่งอัปมงคล) =======================
AD_DOMAINS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com", "adservice.google.com",
    "google-analytics.com", "googletagservices.com", "amazon-adsystem.com", "adnxs.com", "criteo.com",
    "criteo.net", "taboola.com", "outbrain.com", "scorecardresearch.com", "quantserve.com", "pubmatic.com",
    "rubiconproject.com", "openx.net", "casalemedia.com", "adsrvr.org", "moatads.com", "zedo.com",
    "popads.net", "propellerads.com", "hotjar.com", "mgid.com", "revcontent.com", "yieldmo.com",
    "smartadserver.com",
}


class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.blocked = 0
        self.domains = set(AD_DOMAINS)
        extra = DATA_DIR / "blocklist.txt"
        if extra.exists():
            self.domains |= {l.strip() for l in extra.read_text().splitlines() if l.strip()}

    def interceptRequest(self, info):
        if not self.config.get("adblock"):
            return
        parts = info.requestUrl().host().lower().split(".")
        for i in range(len(parts) - 1):
            if ".".join(parts[i:]) in self.domains:
                info.block(True)
                self.blocked += 1
                return


def apply_network(config):
    kind = config.get("proxy_type", "none")
    if kind == "none":
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        return
    ptype = QNetworkProxy.ProxyType.Socks5Proxy if kind == "socks5" else QNetworkProxy.ProxyType.HttpProxy
    QNetworkProxy.setApplicationProxy(QNetworkProxy(ptype, config["proxy_host"], int(config["proxy_port"])))


class NetworkDialog(QDialog):
    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser
        cfg = browser.config
        self.setWindowTitle("ตั้งค่า Proxy")
        form = QFormLayout(self)
        self.kind = QComboBox()
        self.kind.addItems(["none", "socks5", "http"])
        self.kind.setCurrentText(cfg["proxy_type"])
        self.host = QLineEdit(cfg["proxy_host"])
        self.port = QSpinBox(maximum=65535)
        self.port.setValue(int(cfg["proxy_port"]))
        form.addRow("Proxy:", self.kind)
        form.addRow("Host:", self.host)
        form.addRow("Port:", self.port)
        form.addRow(QLabel("<small>Tor Browser เปิดค้างไว้: socks5 127.0.0.1:9150<br>"
                           "Tor service: socks5 127.0.0.1:9050<br>VPN ที่มีโหมด SOCKS5: ใส่ตามผู้ให้บริการ</small>"))
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def save(self):
        self.browser.config.update(proxy_type=self.kind.currentText(), proxy_host=self.host.text().strip(),
                                   proxy_port=self.port.value())
        self.browser.save_config()
        apply_network(self.browser.config)
        self.browser.update_status_labels()
        self.browser.view().reload()
        self.accept()


# ======================= Browser =======================
class BrowserView(QWebEngineView):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setPage(QWebEnginePage(browser.profile, self))

    def createWindow(self, _type):
        return self.browser.add_tab()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        sel = self.page().selectedText().strip()
        if sel and any(c.isdigit() for c in sel):
            menu.addSeparator()
            menu.addAction("🔢 ดูเลขมงคล", lambda: self.browser.mordu.show_number(sel))
        menu.exec(event.globalPos())


class HistoryDialog(QDialog):
    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser
        self.setWindowTitle("ประวัติการเข้าชม")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        self.search = QLineEdit(placeholderText="ค้นหาในประวัติ...")
        self.search.textChanged.connect(self.refresh)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.open_item)
        clear_btn = QPushButton("ล้างประวัติทั้งหมด")
        clear_btn.clicked.connect(self.clear)
        layout.addWidget(self.search)
        layout.addWidget(self.list)
        layout.addWidget(clear_btn)
        self.refresh()

    def refresh(self):
        q = self.search.text().lower()
        self.list.clear()
        for h in reversed(self.browser.history):
            if q and q not in h["title"].lower() and q not in h["url"].lower():
                continue
            item = QListWidgetItem(f'{h["time"]}   {h["title"]}\n{h["url"]}')
            item.setData(Qt.ItemDataRole.UserRole, h["url"])
            self.list.addItem(item)

    def open_item(self, item):
        self.browser.add_tab(QUrl(item.data(Qt.ItemDataRole.UserRole)))
        self.close()

    def clear(self):
        self.browser.history = []
        save_json(HISTORY_FILE, [])
        self.refresh()


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — เว็บบราวเซอร์สำหรับสายมู")
        self.resize(1400, 850)

        self.config = {**DEFAULT_CONFIG, **load_json(CONFIG_FILE, {})}
        self.bookmarks = load_json(BOOKMARKS_FILE, [])
        self.history = load_json(HISTORY_FILE, [])
        self.devtools = None
        self.today = date.today()
        self.update_url = HOME_URL

        apply_network(self.config)
        self.profile = QWebEngineProfile("PiriMU", self)
        self.profile.setPersistentStoragePath(str(DATA_DIR / "storage"))
        self.profile.setCachePath(str(DATA_DIR / "cache"))
        self.profile.downloadRequested.connect(self.on_download)
        self.adblocker = AdBlocker(self.config)
        self.profile.setUrlRequestInterceptor(self.adblocker)
        self.apply_dark_mode()

        self.tabs = QTabWidget(documentMode=True, tabsClosable=True, movable=True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        plus = QPushButton("+")
        plus.setFixedWidth(30)
        plus.clicked.connect(lambda: self.add_tab(QUrl(HOME_URL)))
        self.tabs.setCornerWidget(plus)

        central = QWidget()
        cl = QVBoxLayout(central)
        cl.setContentsMargins(0, 4, 0, 4)
        cl.setSpacing(4)
        cl.addWidget(self.tabs, 1)
        self.footer = SmileFooter(self)
        cl.addWidget(self.footer)
        self.setCentralWidget(central)

        self.mordu = MorduSidebar(self)
        self.mordu_dock = QDockWidget("🔮 หมอดูปิริ", self)
        self.mordu_dock.setWidget(self.mordu)
        self.mordu_dock.setMinimumWidth(340)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.mordu_dock)

        self.build_toolbar()
        self.build_menus()

        sb = self.statusBar()
        self.progress = QProgressBar(maximumWidth=160, visible=False)
        self.update_btn = QPushButton(visible=False)
        self.update_btn.clicked.connect(lambda: self.add_tab(QUrl(self.update_url)))
        self.day_label, self.block_label, self.net_label = QLabel(), QLabel(), QLabel()
        for wdg in (self.progress, self.update_btn, self.net_label, self.block_label, self.day_label):
            sb.addPermanentWidget(wdg)

        self.tick = QTimer(self, interval=1000)
        self.tick.timeout.connect(self.on_tick)
        self.tick.start()

        self.apply_theme()
        self.update_status_labels()
        self.add_tab(QUrl(HOME_URL))
        self.check_update()

    # ---------- helpers ----------
    def save_config(self):
        save_json(CONFIG_FILE, self.config)

    def birthdate(self):
        try:
            return date.fromisoformat(self.config.get("birthdate", ""))
        except ValueError:
            return None

    def view(self):
        return self.tabs.currentWidget()

    # ---------- UI ----------
    def build_toolbar(self):
        ears_tb = QToolBar("Ears", movable=False, objectName="ears")
        self.ears = EarsHeader(self)
        ears_tb.addWidget(self.ears)
        self.addToolBar(ears_tb)
        self.addToolBarBreak()

        tb = QToolBar("Navigation", movable=False, objectName="nav")
        self.addToolBar(tb)

        def act(text, tip, slot, shortcut=None):
            a = QAction(text, self, toolTip=tip)
            a.triggered.connect(slot)
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))
            tb.addAction(a)

        act("◀", "ย้อนกลับ (Alt+←)", lambda: self.view().back(), "Alt+Left")
        act("▶", "ไปหน้า (Alt+→)", lambda: self.view().forward(), "Alt+Right")
        act("⟳", "รีโหลด (F5)", lambda: self.view().reload(), "F5")
        act("🏠", "หน้าแรก PiriMU", lambda: self.view().setUrl(QUrl(HOME_URL)))
        self.url_bar = QLineEdit(placeholderText="พิมพ์ URL หรือคำค้นหา...")
        self.url_bar.returnPressed.connect(self.navigate)
        tb.addWidget(self.url_bar)
        act("★", "บุ๊กมาร์ก (Ctrl+D)", self.add_bookmark, "Ctrl+D")
        act("🎋", "เขย่าเซียมซี", lambda: self.mordu.shake())
        act("🔮", "หมอดูปิริ (Ctrl+J)", lambda: self.mordu_dock.setVisible(not self.mordu_dock.isVisible()), "Ctrl+J")

    def build_menus(self):
        mb = self.menuBar()

        def add(menu, text, slot, sc=None, checkable=False, checked=False):
            a = menu.addAction(text)
            a.triggered.connect(slot)
            if sc:
                a.setShortcut(QKeySequence(sc))
            if checkable:
                a.setCheckable(True)
                a.setChecked(checked)
            return a

        m = mb.addMenu("ไฟล์")
        add(m, "แท็บใหม่", lambda: self.add_tab(QUrl(HOME_URL)), "Ctrl+T")
        add(m, "ปิดแท็บ", lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        add(m, "ไปที่แถบ URL", self.focus_url, "Ctrl+L")
        add(m, "ออก", self.close, "Ctrl+Q")

        m = mb.addMenu("มุมมอง")
        add(m, "ซูมเข้า", lambda: self.zoom(0.1), "Ctrl+=")
        add(m, "ซูมออก", lambda: self.zoom(-0.1), "Ctrl+-")
        add(m, "ขนาดปกติ", lambda: self.zoom(None), "Ctrl+0")
        m.addSeparator()
        add(m, "🌙 โหมดมืดทุกเว็บ", self.toggle_dark, checkable=True, checked=self.config["dark_mode"])
        add(m, "🪷 ปัดเป่าสิ่งอัปมงคล (บล็อกโฆษณา)", self.toggle_adblock, checkable=True,
            checked=self.config["adblock"])
        m.addSeparator()
        add(m, "DevTools", self.open_devtools, "F12")

        m = mb.addMenu("🎨 ธีม")
        group = QActionGroup(self)

        def theme_item(menu, key, label):
            a = add(menu, label, lambda _, k=key: self.set_theme(k), checkable=True,
                    checked=self.config["theme"] == key)
            group.addAction(a)

        theme_item(m, "auto_day", "✨ สีมงคลประจำวัน (เปลี่ยนเองทุกวัน)")
        m.addSeparator()
        for title, items in (("🌈 สีประจำวัน", DAY_THEMES), ("👑 ทอง เงิน นาก", LUX_THEMES),
                             ("💎 อัญมณีนพเก้า", {**GEM_THEMES, "navaratna": NAVARATNA}),
                             ):
            sub = m.addMenu(title)
            for key, t in items.items():
                theme_item(sub, key, t["name"])
        sub = m.addMenu("🐉 12 นักษัตร")
        for key, label in zip(ZODIAC_MENU, ZODIAC_LABEL):
            theme_item(sub, key, f"{ANIMAL_THEMES[key]['name']} · ปี{label}")
        sub = m.addMenu("🐾 สัตว์น่ารัก")
        for key in CUTE_MENU:
            theme_item(sub, key, ANIMAL_THEMES[key]["name"])

        m = mb.addMenu("🔮 มู")
        add(m, "🌞 ดวงวันนี้", lambda: (self.mordu_dock.show(), self.mordu.setCurrentIndex(0)))
        add(m, "🔢 ดูเลขมงคล", lambda: (self.mordu_dock.show(), self.mordu.setCurrentIndex(1)))
        add(m, "🎋 เขย่าเซียมซี", self.mordu.shake)
        add(m, "🐉 ปีนักษัตร / ปีชง", lambda: (self.mordu_dock.show(), self.mordu.setCurrentIndex(3)))
        m.addSeparator()
        add(m, "🎂 ตั้งวันเกิด...", lambda: BirthDialog(self).exec())

        self.bm_menu = mb.addMenu("บุ๊กมาร์ก")
        self.bm_menu.aboutToShow.connect(self.rebuild_bookmarks_menu)
        add(mb.addMenu("🧅 เครือข่าย"), "ตั้งค่า Proxy / Tor...", lambda: NetworkDialog(self).exec())
        add(mb, "ประวัติ", lambda: HistoryDialog(self).exec(), "Ctrl+H")

        m = mb.addMenu("ช่วยเหลือ")
        add(m, "📖 คู่มือสายมู", lambda: self.add_tab(QUrl(GUIDE_URL)))
        add(m, "🌐 pirimu.com", lambda: self.add_tab(QUrl(HOME_URL)))
        add(m, "💬 แจ้งปัญหา (Line OA: @wasin)", lambda: self.add_tab(QUrl("https://line.me/R/ti/p/@wasin")))
        add(m, "🔒 นโยบายความเป็นส่วนตัว", lambda: self.add_tab(QUrl(HOME_URL + "/privacy.html")))
        add(m, "เกี่ยวกับ PiriMU", lambda: QMessageBox.about(self, "เกี่ยวกับ PiriMU",
                                                             f"{ABOUT_TEXT}\n\nเวอร์ชัน {APP_VERSION}"))

    # ---------- theme / status ----------
    def set_theme(self, key):
        self.config["theme"] = key
        self.save_config()
        self.apply_theme()

    def apply_theme(self):
        _, t = effective_theme(self.config)
        QApplication.instance().setStyleSheet(theme_stylesheet(t))
        self.ears.update()
        self.footer.update()
        self.update_status_labels()

    def update_status_labels(self):
        wd = date.today().weekday()
        self.day_label.setText(f"วัน{DAY_NAMES[wd]} · สี{DAY_COLORS[wd]}")
        c = self.config
        self.net_label.setText(f"🧅 {c['proxy_type']} {c['proxy_host']}:{c['proxy_port']}"
                               if c["proxy_type"] != "none" else "")

    def on_tick(self):
        if self.config["adblock"]:
            self.block_label.setText(f"🪷 ปัดเป่าสิ่งอัปมงคลแล้ว {self.adblocker.blocked:,}")
        else:
            self.block_label.setText("🪷 ปิดการปัดเป่า")
        if date.today() != self.today:   # ข้ามเที่ยงคืน → เปลี่ยนสีวันและดวงใหม่
            self.today = date.today()
            self.apply_theme()
            self.mordu.refresh()

    def apply_dark_mode(self):
        attr = getattr(QWebEngineSettings.WebAttribute, "ForceDarkMode", None)
        if attr is not None:
            self.profile.settings().setAttribute(attr, self.config["dark_mode"])

    def toggle_dark(self, on):
        if getattr(QWebEngineSettings.WebAttribute, "ForceDarkMode", None) is None:
            self.statusBar().showMessage("โหมดมืดต้องใช้ PyQt6-WebEngine 6.7 ขึ้นไป", 5000)
            return
        self.config["dark_mode"] = on
        self.save_config()
        self.apply_dark_mode()

    def toggle_adblock(self, on):
        self.config["adblock"] = on
        self.save_config()
        self.view().reload()

    # ---------- update check ----------
    def check_update(self):
        self.nam = QNetworkAccessManager(self)
        plat = {"win32": "windows", "darwin": "mac"}.get(sys.platform, sys.platform)
        reply = self.nam.get(QNetworkRequest(QUrl(f"{VERSION_URL}?v={APP_VERSION}&os={plat}")))
        reply.finished.connect(lambda r=reply: self.on_version(r))

    def on_version(self, reply):
        try:
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            new = data["version"]
            if tuple(map(int, new.split("."))) > tuple(map(int, APP_VERSION.split("."))):
                self.update_url = data.get("url", HOME_URL)
                self.update_btn.setText(f"🆕 มีเวอร์ชันใหม่ {new}")
                self.update_btn.setToolTip(data.get("note", ""))
                self.update_btn.show()
        except Exception:
            pass
        reply.deleteLater()

    # ---------- tabs / navigation ----------
    def add_tab(self, url=None):
        view = BrowserView(self)
        idx = self.tabs.addTab(view, "แท็บใหม่")
        self.tabs.setCurrentIndex(idx)
        view.urlChanged.connect(lambda u, v=view: self.on_url_changed(v, u))
        view.titleChanged.connect(lambda t, v=view: self.on_title_changed(v, t))
        view.iconChanged.connect(lambda i, v=view: self.tabs.setTabIcon(self.tabs.indexOf(v), i))
        view.loadProgress.connect(lambda p, v=view: self.on_progress(v, p))
        view.loadFinished.connect(lambda ok, v=view: self.on_load_finished(v, ok))
        view.page().linkHovered.connect(lambda link: self.statusBar().showMessage(link))
        if url is not None:
            view.setUrl(url)
        return view

    def close_tab(self, index):
        if self.tabs.count() <= 1:
            self.view().setUrl(QUrl(HOME_URL))
            return
        w = self.tabs.widget(index)
        self.tabs.removeTab(index)
        w.deleteLater()

    def on_tab_changed(self, _):
        v = self.view()
        if v:
            self.url_bar.setText(v.url().toString())
            self.setWindowTitle(f"{v.title() or 'แท็บใหม่'} — {APP_NAME}")

    def navigate(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if "://" in text or text.startswith("about:"):
            url = QUrl(text)
        elif text.startswith("localhost"):
            url = QUrl("http://" + text)
        elif " " not in text and "." in text:
            url = QUrl("https://" + text)
        else:
            url = QUrl(SEARCH_URL.format(quote_plus(text)))
        self.view().setUrl(url)
        self.view().setFocus()

    def focus_url(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def zoom(self, delta):
        v = self.view()
        v.setZoomFactor(1.0 if delta is None else max(0.25, min(5.0, v.zoomFactor() + delta)))

    def on_url_changed(self, view, url):
        if view is self.view():
            self.url_bar.setText(url.toString())
            self.url_bar.setCursorPosition(0)

    def on_title_changed(self, view, title):
        idx = self.tabs.indexOf(view)
        self.tabs.setTabText(idx, (title[:22] + "…" if len(title) > 24 else title) or "แท็บใหม่")
        self.tabs.setTabToolTip(idx, title)
        if view is self.view():
            self.setWindowTitle(f"{title} — {APP_NAME}")

    def on_progress(self, view, p):
        if view is self.view():
            self.progress.setVisible(p < 100)
            self.progress.setValue(p)

    def on_load_finished(self, view, ok):
        if view is self.view():
            self.progress.setVisible(False)
        url = view.url().toString()
        if ok and url.startswith("http"):
            self.history.append({"url": url, "title": view.title() or url,
                                 "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            self.history = self.history[-MAX_HISTORY:]
            save_json(HISTORY_FILE, self.history)

    # ---------- bookmarks ----------
    def add_bookmark(self):
        v = self.view()
        url = v.url().toString()
        if any(b["url"] == url for b in self.bookmarks):
            self.statusBar().showMessage("มีบุ๊กมาร์กนี้อยู่แล้ว", 3000)
            return
        self.bookmarks.append({"title": v.title() or url, "url": url})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self.statusBar().showMessage("เพิ่มบุ๊กมาร์กแล้ว ★", 3000)

    def rebuild_bookmarks_menu(self):
        self.bm_menu.clear()
        self.bm_menu.addAction("บุ๊กมาร์กหน้านี้", self.add_bookmark)
        self.bm_menu.addSeparator()
        if not self.bookmarks:
            self.bm_menu.addAction("(ยังไม่มีบุ๊กมาร์ก)").setEnabled(False)
        for b in self.bookmarks:
            sub = QMenu(b["title"][:40], self.bm_menu)
            sub.addAction("เปิด", lambda u=b["url"]: self.view().setUrl(QUrl(u)))
            sub.addAction("เปิดในแท็บใหม่", lambda u=b["url"]: self.add_tab(QUrl(u)))
            sub.addAction("ลบ", lambda u=b["url"]: self.remove_bookmark(u))
            self.bm_menu.addMenu(sub)

    def remove_bookmark(self, url):
        self.bookmarks = [b for b in self.bookmarks if b["url"] != url]
        save_json(BOOKMARKS_FILE, self.bookmarks)

    # ---------- downloads / devtools ----------
    def on_download(self, req):
        default = str(Path.home() / "Downloads" / req.downloadFileName())
        path, _ = QFileDialog.getSaveFileName(self, "บันทึกไฟล์", default)
        if not path:
            req.cancel()
            return
        req.setDownloadDirectory(os.path.dirname(path))
        req.setDownloadFileName(os.path.basename(path))
        req.receivedBytesChanged.connect(lambda: self.statusBar().showMessage(
            f"กำลังดาวน์โหลด {req.downloadFileName()} {req.receivedBytes() // 1024:,} KB"))
        req.isFinishedChanged.connect(lambda: self.statusBar().showMessage(f"ดาวน์โหลดเสร็จ: {path}", 5000))
        req.accept()

    def open_devtools(self):
        if self.devtools is None:
            self.devtools = QWebEngineView()
            self.devtools.setWindowTitle("DevTools")
            self.devtools.resize(900, 600)
        self.view().page().setDevToolsPage(self.devtools.page())
        self.devtools.show()
        self.devtools.raise_()


if __name__ == "__main__":
    if sys.platform == "win32":   # ให้ taskbar แสดงไอคอน PiriMU แทนไอคอน Python
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.pirimu.browser")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon = APP_DIR / "icon.png"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    win = Browser()
    win.show()
    sys.exit(app.exec())
