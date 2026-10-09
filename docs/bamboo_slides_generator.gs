/**
 * Bamboo Engine — Google Slides Generator Script (Updated Q4/2026)
 * 
 * HƯỚNG DẪN SỬ DỤNG:
 * 1. Truy cập https://slides.new để tạo một trang trình bày Google Slides mới.
 * 2. Trên thanh menu, chọn: Tiện ích mở rộng (Extensions) > Apps Script.
 * 3. Xóa code mặc định và dán toàn bộ nội dung script này vào.
 * 4. Nhấn nút "Chạy" (Run) với hàm `generateBambooRoadmapSlides`.
 * 5. Cấp quyền truy cập Google Slides khi được yêu cầu. Toàn bộ các slide sẽ được tạo tự động!
 */

function generateBambooRoadmapSlides() {
  const presentation = SlidesApp.getActivePresentation();
  
  const BG_COLOR = '#0F172A';      // Slate 900
  const CARD_BG = '#1E293B';       // Slate 800
  const BORDER_COLOR = '#334155';  // Slate 700
  const ACCENT_EMERALD = '#10B981';
  const ACCENT_TEAL = '#14B8A6';
  const ACCENT_CYAN = '#06B6D4';
  const ACCENT_AMBER = '#F59E0B';
  const TEXT_MAIN = '#F8FAFC';
  const TEXT_MUTED = '#94A3B8';

  function setupSlide(slide) {
    slide.getBackground().setSolidFill(BG_COLOR);
    return slide;
  }

  function addHeader(slide, tag, title, subtitle) {
    const box = slide.insertTextBox(tag.toUpperCase() + "\n" + title + "\n" + subtitle, 40, 20, 880, 80);
    const text = box.getText();
    
    const tagRange = text.getRange(0, tag.length);
    tagRange.getTextStyle().setForegroundColor(ACCENT_EMERALD).setFontSize(10).setBold(true);
    
    const titleStart = tag.length + 1;
    const titleEnd = titleStart + title.length;
    const titleRange = text.getRange(titleStart, titleEnd);
    titleRange.getTextStyle().setForegroundColor(TEXT_MAIN).setFontSize(18).setBold(true);

    const subStart = titleEnd + 1;
    const subRange = text.getRange(subStart, text.getLength());
    subRange.getTextStyle().setForegroundColor(TEXT_MUTED).setFontSize(10);
  }

  // ==========================================
  // SLIDE 1: COVER
  // ==========================================
  const s1 = presentation.appendSlide();
  setupSlide(s1);

  const bar = s1.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, 0, 960, 8);
  bar.getFill().setSolidFill(ACCENT_EMERALD);
  bar.getBorder().setTransparent();

  const covBox = s1.insertTextBox(
    "🎋 BAMBOO GAME ENGINE\n" +
    "Kế Hoạch Roadmap Chiến Lược Q4/2026\n" +
    "Giai đoạn: Nền Móng (Foundation) • Mục tiêu Bản phát hành v0.1.0 'Sprout'\n" +
    "Thời gian: 12/10/2026 – 31/12/2026 (12 tuần)  |  Upstream Base: Godot 4.8.dev @ c24bf5d",
    80, 100, 800, 220
  );
  const ct = covBox.getText();
  ct.getRange(0, 22).getTextStyle().setForegroundColor(ACCENT_EMERALD).setFontSize(14).setBold(true);
  ct.getRange(23, 59).getTextStyle().setForegroundColor(TEXT_MAIN).setFontSize(26).setBold(true);
  ct.getRange(60, 127).getTextStyle().setForegroundColor(ACCENT_TEAL).setFontSize(13);
  ct.getRange(128, ct.getLength()).getTextStyle().setForegroundColor(TEXT_MUTED).setFontSize(11);

  // 3 Stats cards on cover
  const stats = [
    { t: "6 / 6 NỀN TẢNG CI", sub: "Win, Mac, Linux, Android, iOS, Web", col: ACCENT_EMERALD },
    { t: "PORT GAME UNITY3D", sub: "Chuyển đổi ≥ 1 game chạy PC + Android", col: ACCENT_CYAN },
    { t: "18/12/2026 GA", sub: "Bản phát hành chính thức 0.1.0 Sprout", col: ACCENT_AMBER }
  ];
  stats.forEach((st, i) => {
    const x = 80 + i * 275;
    const card = s1.insertShape(SlidesApp.ShapeType.ROUNDED_RECTANGLE, x, 340, 250, 110);
    card.getFill().setSolidFill(CARD_BG);
    card.getBorder().setSolidFill(st.col).setWeight(1.5);
    const tb = s1.insertTextBox(st.t + "\n" + st.sub, x + 15, 355, 220, 80);
    const t = tb.getText();
    t.getRange(0, st.t.length).getTextStyle().setForegroundColor(st.col).setFontSize(13).setBold(true);
    t.getRange(st.t.length + 1, t.getLength()).getTextStyle().setForegroundColor(TEXT_MUTED).setFontSize(10);
  });

  // ==========================================
  // SLIDE 2: THE 1-SLIDE MASTER ROADMAP PLAN
  // ==========================================
  const s2 = presentation.appendSlide();
  setupSlide(s2);
  addHeader(s2, "Bamboo Engine • Q4/2026 Master Plan", "Roadmap Tổng Quan Giai Đoạn Nền Móng (Foundation)", "Thời gian: 12/10/2026 – 31/12/2026 (12 tuần)  •  Mục tiêu cuối quý: Bamboo 0.1.0 'Sprout'");

  // 6 Objectives (Updated O6 to Port Unity3D Game)
  const objs = [
    { code: "O1", t: "Fork Ổn Định & Rebranding", d: "CI Editor & Templates 6/6 nền tảng; logo/icon Bamboo.", col: ACCENT_EMERALD },
    { code: "O2", t: "Đo Lường Hiệu Năng", d: "Benchmark nightly ≥ 6 kịch bản; golden image 3 renderer.", col: ACCENT_TEAL },
    { code: "O3", t: "Quy Chuẩn Kỹ Thuật", d: "Diễn tập rebase; repo bamboo_modules; 100% // BAMBOO: patch.", col: ACCENT_CYAN },
    { code: "O4", t: "Cấu Hình Mặc Định", d: "Jolt Physics mặc định; 3 build profile (2D, Mobile, PC).", col: '#A855F7' },
    { code: "O5", t: "Dogfooding Thực Chiến", d: "Đội game kiểm thử engine, đo độ ổn định, thu crash log.", col: ACCENT_AMBER },
    { code: "O6", t: "Port Game Unity3D → Bamboo", d: "Pipeline di chuyển; port hoàn chỉnh ≥ 1 game PC + Android.", col: ACCENT_CYAN }
  ];

  objs.forEach((o, idx) => {
    const colIdx = idx % 3;
    const rowIdx = Math.floor(idx / 3);
    const ox = 40 + colIdx * 298;
    const oy = 110 + rowIdx * 95;
    const ocard = s2.insertShape(SlidesApp.ShapeType.ROUNDED_RECTANGLE, ox, oy, 285, 85);
    ocard.getFill().setSolidFill(CARD_BG);
    ocard.getBorder().setSolidFill(BORDER_COLOR).setWeight(1);
    
    const otb = s2.insertTextBox(o.code + " • " + o.t + "\n" + o.d, ox + 10, oy + 8, 265, 70);
    const ot = otb.getText();
    const titleLen = (o.code + " • " + o.t).length;
    ot.getRange(0, titleLen).getTextStyle().setForegroundColor(o.col).setFontSize(11).setBold(true);
    ot.getRange(titleLen + 1, ot.getLength()).getTextStyle().setForegroundColor(TEXT_MUTED).setFontSize(9.5);
  });

  // 5 Timeline Phases (Updated with Unity porting steps)
  const phases = [
    { w: "W1–W2 (12-23/10)", t: "Setup & CI Desktop", items: "• Branching & env\n• Khảo sát game Unity\n• CI Win/Mac/Linux", ms: "★ 0.1.0-alpha.1 (23/10)", col: ACCENT_EMERALD },
    { w: "W3–W4 (26/10-6/11)", t: "CI Mobile & Bench", items: "• CI Android, iOS, Web\n• Pipeline port Unity\n• Golden image CI", ms: "★ 0.1.0-alpha.2 (06/11)", col: ACCENT_TEAL },
    { w: "W5–W6 (09-20/11)", t: "Upstream & Porting v1", items: "• Diễn tập rebase\n• Convert asset Unity\n• Jolt Physics default", ms: "★ 0.1.0-alpha.3 (20/11)", col: ACCENT_CYAN },
    { w: "W7–W8 (23/11-4/12)", t: "Hoàn Tất Port & Freeze", items: "• Game Unity chạy PC/Andr\n• Branch release/0.1\n• Bug bash toàn đội", ms: "★ 0.1.0-beta.1 (04/12)", col: ACCENT_AMBER },
    { w: "W9–W10 (07-18/12)", t: "Ổn Định & Release", items: "• Tối ưu game đã port\n• RC.1 regression (15/12)\n• Go/No-go meeting", ms: "🚀 0.1.0 Sprout (18/12)", col: ACCENT_EMERALD }
  ];

  phases.forEach((p, idx) => {
    const px = 40 + idx * 179;
    const py = 315;
    const pcard = s2.insertShape(SlidesApp.ShapeType.ROUNDED_RECTANGLE, px, py, 172, 185);
    pcard.getFill().setSolidFill(CARD_BG);
    pcard.getBorder().setSolidFill(p.col).setWeight(1.2);

    const ptb = s2.insertTextBox(p.w + "\n" + p.t + "\n" + p.items + "\n\n" + p.ms, px + 8, py + 8, 156, 170);
    const pt = ptb.getText();
    pt.getRange(0, p.w.length).getTextStyle().setForegroundColor(p.col).setFontSize(9).setBold(true);
    const tStart = p.w.length + 1;
    const tEnd = tStart + p.t.length;
    pt.getRange(tStart, tEnd).getTextStyle().setForegroundColor(TEXT_MAIN).setFontSize(10).setBold(true);
    
    const msIndex = pt.asString().indexOf(p.ms);
    if (msIndex !== -1) {
      pt.getRange(msIndex, msIndex + p.ms.length).getTextStyle().setForegroundColor(p.col).setFontSize(9).setBold(true);
    }
  });

  const fn = s2.insertTextBox("* W11–W12 (21–31/12): Kỳ nghỉ lễ cuối năm, trực lỗi on-call 0.1.0, nghiệm thu KPI và lập kế hoạch Q1/2027.", 40, 510, 880, 25);
  fn.getText().getTextStyle().setForegroundColor(TEXT_MUTED).setFontSize(8.5).setItalic(true);

  // ==========================================
  // SLIDE 3: KPIS & RISKS (UPDATED)
  // ==========================================
  const s3 = presentation.appendSlide();
  setupSlide(s3);
  addHeader(s3, "Bamboo Engine • Kiểm Soát & Nghiệm Thu", "Chỉ Số Đo Lường KPI & Ma Trận Quản Trị Rủi Ro Q4", "Tiêu chuẩn bàn giao chất lượng nghiêm ngặt cho nội bộ và đối tác trước kỳ nghỉ lễ");

  // Left card: KPIs
  const cardK = s3.insertShape(SlidesApp.ShapeType.ROUNDED_RECTANGLE, 40, 110, 425, 400);
  cardK.getFill().setSolidFill(CARD_BG);
  cardK.getBorder().setSolidFill(BORDER_COLOR).setWeight(1);

  const tbK = s3.insertTextBox(
    "📊 BẢNG CHỈ SỐ KPI NGHIỆM THU\n\n" +
    "• Nền tảng CI xanh hoàn chỉnh: 6 / 6 (Win, Mac, Linux, Android, iOS, Web)\n" +
    "• Kịch bản benchmark baseline: ≥ 6 kịch bản (Draw calls, physics, RAM...)\n" +
    "• Golden-image rendering test: 3 renderer × ≥ 10 scene (Forward+, Mobile, Compat)\n" +
    "• Thời gian CI build Editor: ≤ 20 phút (với SCons cache)\n" +
    "• Game Unity3D nội bộ port thành công: ≥ 1 game (chạy mượt mà PC + Android)\n" +
    "• Tài liệu hướng dẫn Migration: Hoàn thành API cheatsheet & workflow asset\n" +
    "• Quy chuẩn patch mã nguồn lõi: 100% gắn thẻ // BAMBOO:\n" +
    "• Diễn tập rebase upstream: ≥ 1 lần có biên bản phân tích\n" +
    "• Lỗi nghiêm trọng (P0) tại GA: 0 P0 mở (chặn phát hành nếu > 0)",
    55, 120, 395, 380
  );
  const kt = tbK.getText();
  kt.getRange(0, 30).getTextStyle().setForegroundColor(ACCENT_EMERALD).setFontSize(13).setBold(true);
  kt.getRange(31, kt.getLength()).getTextStyle().setForegroundColor(TEXT_MAIN).setFontSize(10);

  // Right card: Risks
  const cardR = s3.insertShape(SlidesApp.ShapeType.ROUNDED_RECTANGLE, 495, 110, 425, 400);
  cardR.getFill().setSolidFill(CARD_BG);
  cardR.getBorder().setSolidFill(BORDER_COLOR).setWeight(1);

  const tbR = s3.insertTextBox(
    "🛡️ MA TRẬN QUẢN TRỊ RỦI RO\n\n" +
    "⚠️ CI Runner thiếu GPU thật [Xác suất: Cao | Tác động: TB]\n" +
    "   ↳ Dùng lavapipe/llvmpipe trên Linux; runner macOS dùng Metal; ngưỡng sai số ảnh.\n\n" +
    "⚠️ Rebase upstream xung đột lớn [Xác suất: TB | Tác động: TB]\n" +
    "   ↳ Diễn tập sớm W5; giữ patch lõi nhỏ; chuyển tính năng sang bamboo_modules.\n\n" +
    "⚠️ Khác biệt kiến trúc Unity vs Bamboo [Xác suất: Cao | Tác động: TB]\n" +
    "   ↳ Chọn game scope vừa phải (2D/3D mid-core); lập API cheatsheet; dùng pipeline FBX/glTF chuẩn.\n\n" +
    "⚠️ Chậm thiết kế logo/icon mới [Xác suất: TB | Tác động: Thấp]\n" +
    "   ↳ Dùng logo tạm có typo Bamboo cho alpha/beta; thay bản chuẩn ở 0.1.0/0.1.1.\n\n" +
    "⚠️ Thiếu người kỳ nghỉ lễ cuối năm [Xác suất: Cao | Tác động: Thấp]\n" +
    "   ↳ Khóa phát hành GA trước 18/12 (W10); 2 tuần cuối năm chỉ trực on-call.",
    510, 120, 395, 380
  );
  const rt = tbR.getText();
  rt.getRange(0, 26).getTextStyle().setForegroundColor(ACCENT_AMBER).setFontSize(13).setBold(true);
  rt.getRange(27, rt.getLength()).getTextStyle().setForegroundColor(TEXT_MUTED).setFontSize(9.5);

  Logger.log("Đã cập nhật thành công bộ Slide Bamboo Engine Q4/2026 trên Google Slides!");
}
