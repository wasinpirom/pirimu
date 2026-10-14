(() => {
  // index 0 = อาทิตย์ (ตาม JS getDay)
  const DAYS = [
    { n: "อาทิตย์", c: "แดง", day: "#FA5252", dark: "#A51111", soft: "#FFF0F0", txt: "#FFFFFF" },
    { n: "จันทร์", c: "เหลือง", day: "#FFD43B", dark: "#8A6D00", soft: "#FFF9DB", txt: "#4A3A00" },
    { n: "อังคาร", c: "ชมพู", day: "#F783AC", dark: "#A61E4D", soft: "#FFF0F6", txt: "#5C0F2B" },
    { n: "พุธ", c: "เขียว", day: "#51CF66", dark: "#2B8A3E", soft: "#EBFBEE", txt: "#123D1D" },
    { n: "พฤหัสบดี", c: "ส้ม", day: "#FF922B", dark: "#A84B00", soft: "#FFF4E6", txt: "#4A2100" },
    { n: "ศุกร์", c: "ฟ้า", day: "#74C0FC", dark: "#1864AB", soft: "#E7F5FF", txt: "#0B2E52" },
    { n: "เสาร์", c: "ม่วง", day: "#9775FA", dark: "#5F3DC4", soft: "#F3F0FF", txt: "#FFFFFF" },
  ];
  const $ = (s) => document.querySelector(s);
  const today = new Date();
  const d = DAYS[today.getDay()];
  const root = document.documentElement.style;
  root.setProperty("--day", d.day); root.setProperty("--day-dark", d.dark);
  root.setProperty("--day-soft", d.soft); root.setProperty("--day-txt", d.txt);
  document.querySelectorAll("[data-today]").forEach((el) => (el.textContent = `วันนี้วัน${d.n} สีมงคลคือสี${d.c}`));

  const week = $("#week");
  if (week) {
    [1, 2, 3, 4, 5, 6, 0].forEach((i) => {
      const x = DAYS[i], el = document.createElement("div");
      el.style.background = x.day; el.style.color = x.txt;
      el.innerHTML = `${x.n}<span>สี${x.c}</span>`;
      if (i === today.getDay()) { el.classList.add("on"); el.setAttribute("aria-current", "date"); }
      week.appendChild(el);
    });
  }

  // แนะนำปุ่มดาวน์โหลดตามระบบปฏิบัติการ
  const ua = navigator.userAgent;
  const isMac = /Macintosh|Mac OS X/.test(ua), isWin = /Windows/.test(ua);
  const pick = isMac ? "mac" : isWin ? "win" : null;
  if (pick) {
    document.querySelector(`.os article[data-os="${pick}"]`)?.classList.add("pick");
    const main = $("#dl-main");
    if (main) {
      main.href = pick === "mac" ? "/dl/mac" : "/dl/windows";
      main.querySelector("span").textContent = pick === "mac" ? "ดาวน์โหลดสำหรับ Mac" : "ดาวน์โหลดสำหรับ Windows";
    }
  }

  // เวอร์ชันล่าสุด (สร้างอัตโนมัติตอน deploy)
  fetch("/version.json", { cache: "no-store" }).then((r) => r.json())
    .then((v) => document.querySelectorAll("[data-version]").forEach((el) => (el.textContent = v.version)))
    .catch(() => {});

  const P = window.PIRIMU || {};
  document.querySelectorAll("[data-github]").forEach((a) => (a.href = P.github || "#"));
  document.querySelectorAll("[data-contact]").forEach((a) => {
    a.href = "https://line.me/R/ti/p/" + encodeURIComponent(P.line || "@wasin");
    a.target = "_blank"; a.rel = "noopener";
    a.textContent = "ดร.วศิน ภิรมย์ Line OA: " + (P.line || "@wasin");
  });
  const cats = $("#cats");
  if (cats && P.links) {
    cats.innerHTML = P.links.map((c) => `<div><h3>${c.category}</h3><ul>${c.items.map((i) =>
      `<li><a href="${i.url}" target="_blank" rel="noopener">${i.name}</a><small>${i.note || ""}</small></li>`).join("")}</ul></div>`).join("");
  }
  const up = $("#updates");
  if (up && P.updates) up.innerHTML = P.updates.map((u) => `<li><b>${u.version}</b> (${u.date}) ${u.text}</li>`).join("");

  // ===== คัดลอกคำสั่งติดตั้ง =====
  document.querySelectorAll("[data-copy]").forEach((btn) => btn.addEventListener("click", async () => {
    const text = document.getElementById(btn.dataset.copy).textContent;
    try { await navigator.clipboard.writeText(text); btn.textContent = "คัดลอกแล้ว ✓"; }
    catch { btn.textContent = "กดค้างเพื่อคัดลอก"; }
    setTimeout(() => (btn.textContent = "คัดลอก"), 2000);
  }));

  // ===== สมัครรับข่าว (ไม่บังคับ) =====
  const sub = $("#sub-form");
  if (sub) sub.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("#sub-msg"), email = $("#sub-email").value.trim(), consent = $("#sub-consent").checked;
    const say = (t, ok) => { msg.textContent = t; msg.className = "sub-msg " + (ok ? "ok" : "err"); };
    if (!/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(email)) return say("ใส่อีเมลให้ถูกต้องก่อนนะครับ", false);
    if (!consent) return say("ติ๊กช่องยินยอมก่อนสมัครนะครับ", false);
    try {
      const r = await fetch("/api/subscribe", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, consent: true, os: pick || "" }) });
      const j = await r.json();
      if (j.ok) { say("สมัครเรียบร้อย ขอบคุณครับ 🪷", true); sub.reset(); } else say(j.error || "สมัครไม่สำเร็จ ลองใหม่อีกครั้ง", false);
    } catch { say("เชื่อมต่อไม่ได้ ลองใหม่อีกครั้ง", false); }
  });
  $("#sub-email")?.addEventListener("input", () => { $("#sub-msg").textContent = ""; });

  // ===== ตัวช่วยเลือกธีม (หน้า guide) =====
  const ZODIAC = [["ชวด","หนู","น้ำ"],["ฉลู","วัว","ดิน"],["ขาล","เสือ","ไม้"],["เถาะ","กระต่าย","ไม้"],["มะโรง","งูใหญ่","ดิน"],
    ["มะเส็ง","งูเล็ก","ไฟ"],["มะเมีย","ม้า","ไฟ"],["มะแม","แพะ","ดิน"],["วอก","ลิง","ทอง"],["ระกา","ไก่","ทอง"],["จอ","หมา","ดิน"],["กุน","หมู","น้ำ"]];
  const MOTHER = { "ไม้": "น้ำ", "ไฟ": "ไม้", "ดิน": "ไฟ", "ทอง": "ดิน", "น้ำ": "ทอง" };
  const ELEMENT_THEMES = {
    "ไม้": ["🍀 พุธ · เขียว", "💚 มรกต", "🐢 เต่า"],
    "ไฟ": ["☀️ อาทิตย์ · แดง", "❤️ ทับทิม", "🌸 อังคาร · ชมพู"],
    "ดิน": ["🌕 จันทร์ · เหลือง", "👑 ทองคำ", "💛 บุษราคัม"],
    "ทอง": ["🥈 เงิน", "💎 เพชร", "👑 ทองคำ"],
    "น้ำ": ["💧 ศุกร์ · ฟ้า", "💙 ไพลิน"],
  };
  const BIRTH_GEM = ["❤️ ทับทิม", "💛 บุษราคัม", "🌹 นาก", "💚 มรกต", "🧡 เพทาย", "💙 ไพลิน", "🤍 มุกดา"];
  const ZODIAC_ANIMAL_THEME = ["🐭 หนู","🐂 กระทิง","🐯 เสือ","🐰 กระต่าย","🐲 มังกร","🐍 งู","🐴 ม้า","🐐 แพะ","🐵 ลิง","🐔 ไก่","🐶 หมา","🐷 หมู"];
  const form = $("#picker-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const v = $("#bday").value, out = $("#picker-out");
      if (!v) { out.innerHTML = "<p>เลือกวันเกิดก่อนนะครับ</p>"; return; }
      const b = new Date(v + "T12:00:00");
      const wd = b.getDay(), zi = ((b.getFullYear() - 4) % 12 + 12) % 12;
      const z = ZODIAC[zi], mother = MOTHER[z[2]];
      const thisYear = ((today.getFullYear() - 4) % 12 + 12) % 12;
      let chong = "ปีนี้ไม่ชงตรงกับปีเกิดของคุณ";
      if (zi === thisYear) chong = "ปีนี้เป็นปีกงของคุณ แนะนำธีม 🌟 นพเก้ารวม ตลอดปี";
      else if ((zi + 6) % 12 === thisYear) chong = "ปีนี้เป็นปีชงตรงของคุณ แนะนำธีม 🌟 นพเก้ารวม ตลอดปี";
      const chip = (t) => `<span class="chip">${t}</span>`;
      out.innerHTML = `
        <p>คุณเกิด<b>วัน${DAYS[wd].n}</b> ปี<b>${z[0]} (${z[1]})</b> ธาตุ<b>${z[2]}</b></p>
        <p><b>ธีมประจำตัว (ใช้ได้ทุกวัน):</b><br>${chip(DAYS[wd].n + " · " + DAYS[wd].c)}${chip(BIRTH_GEM[wd])}${ZODIAC_ANIMAL_THEME[zi] ? chip(ZODIAC_ANIMAL_THEME[zi]) : ""}</p>
        <p><b>ธีมธาตุ${z[2]} (เสริมความเป็นตัวเอง):</b><br>${ELEMENT_THEMES[z[2]].map(chip).join("")}</p>
        <p><b>ธีมธาตุ${mother} (ธาตุที่ส่งเสริมคุณ ใช้ช่วงต้องการแรงหนุน):</b><br>${ELEMENT_THEMES[mother].map(chip).join("")}</p>
        <p>${chong}</p>
        <p><small>สูตรปิริ เพื่อความบันเทิง · ปีนักษัตรคิดจากปี ค.ศ. ถ้าเกิดม.ค.–ก.พ. ก่อนตรุษจีน อาจนับเป็นปีก่อนหน้า</small></p>`;
    });
  }
})();
