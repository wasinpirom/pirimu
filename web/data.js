/* =========================================================
   ไฟล์นี้ไฟล์เดียว แก้ได้เองง่ายๆ แล้ว push GitHub + Redeploy
   ========================================================= */
window.PIRIMU = {
  github: "https://github.com/YOUR-NAME/pirimu",   // ← ใส่ลิงก์ GitHub ของคุณ
  line: "@wasin",                                   // ← Line OA สำหรับแจ้งปัญหา

  // เว็บแนะนำบนหน้าแรก: เรียงตามหมวด ลิงก์แรกของแต่ละหมวดจะเด่นที่สุด
  links: [
    { category: "เกมและบันเทิง", items: [
      { name: "popdeng.com", url: "https://popdeng.com", note: "ข่าวเกมและความบันเทิง" },
    ]},
    { category: "ข่าวและความรู้ AI", items: [
      { name: "panyapradit.com", url: "https://panyapradit.com", note: "ข่าว AI และเทคโนโลยีภาษาไทย" },
    ]},
    { category: "คอร์สและร้านค้า", items: [
      { name: "KWAY.app", url: "https://kway.app", note: "คอร์สออนไลน์และร้านค้า" },
    ]},
    { category: "การศึกษา", items: [
      { name: "exami.org", url: "https://exami.org", note: "เครื่องมือทำข้อสอบ" },
    ]},
  ],

  // มีอะไรใหม่ (ใหม่สุดไว้บนสุด)
  updates: [
    { version: "1.2.0", date: "ต.ค. 2569", text: "ตัวติดตั้งจริง PiriMU-Setup.exe สำหรับ Windows และแอปสำเร็จรูปสำหรับ Mac ดับเบิลคลิกจบ ไม่ต้องลง Python" },
    { version: "1.1.0", date: "ต.ค. 2569", text: "ธีมสัตว์ครบ 12 นักษัตร: หนู กระต่าย มังกร งู ม้า แพะ ลิง ไก่ เพิ่มเข้ามา รวมธีมสัตว์ 19 แบบ" },
    { version: "1.0.0", date: "ต.ค. 2569", text: "เปิดตัว PiriMU: ธีมสีมงคลประจำวัน ทอง เงิน นาก นพเก้า สัตว์น่ารัก 11 แบบ และหมอดูปิริ" },
  ],
};
