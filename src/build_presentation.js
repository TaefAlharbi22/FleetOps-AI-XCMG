const pptxgen = require("pptxgenjs");

const NAVY = "1A3A5C";
const NAVY_DARK = "10263D";
const TEAL = "2A9D8F";
const ORANGE = "E76F51";
const LIGHT_BG = "F7F8FA";
const LIGHT_GREY = "E9ECEF";
const WHITE = "FFFFFF";
const TEXT_DARK = "27303A";
const TEXT_MUTED = "6B7280";

const HEAD_FONT = "Cambria";
const BODY_FONT = "Calibri";

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5

function circleIcon(slide, x, y, size, label, color) {
  slide.addShape("ellipse", { x, y, w: size, h: size, fill: { color }, line: { type: "none" } });
  slide.addText(label, {
    x, y, w: size, h: size, align: "center", valign: "middle",
    fontFace: HEAD_FONT, fontSize: size * 28, bold: true, color: WHITE, margin: 0,
  });
}

function footer(slide, pageNum) {
  slide.addText("FleetOps AI — AI Operations Agent for Construction Equipment", {
    x: 0.5, y: 7.15, w: 9, h: 0.3, fontFace: BODY_FONT, fontSize: 9, color: TEXT_MUTED,
  });
  slide.addText(String(pageNum), {
    x: 12.6, y: 7.15, w: 0.5, h: 0.3, fontFace: BODY_FONT, fontSize: 9, color: TEXT_MUTED, align: "right",
  });
}

// ============================================================= SLIDE 1: TITLE
{
  const s = pres.addSlide();
  s.background = { color: NAVY_DARK };
  s.addShape("rect", { x: 0, y: 0, w: 13.33, h: 7.5, fill: { color: NAVY_DARK }, line: { type: "none" } });
  circleIcon(s, 5.9, 1.35, 0.55, "F", TEAL);
  s.addText("FleetOps AI", {
    x: 0, y: 2.1, w: 13.33, h: 1.1, align: "center", isTextBox: true,
    fontFace: HEAD_FONT, fontSize: 54, bold: true, color: WHITE, margin: 0,
  });
  s.addText("An AI Operations Agent for Construction Equipment", {
    x: 0, y: 3.15, w: 13.33, h: 0.6, align: "center", isTextBox: true,
    fontFace: BODY_FONT, fontSize: 20, color: "CADCFC", margin: 0,
  });
  s.addShape("line", { x: 5.66, y: 4.05, w: 2, h: 0, line: { color: TEAL, width: 2 } });
  s.addText("Track: AI + Construction Machinery  →  AI + Operation", {
    x: 0, y: 4.35, w: 13.33, h: 0.4, align: "center", isTextBox: true,
    fontFace: BODY_FONT, fontSize: 14, color: "9FB3C8", margin: 0,
  });
  s.addText("15th China International College Students' Innovation & Entrepreneurship Competition", {
    x: 0, y: 4.75, w: 13.33, h: 0.4, align: "center", isTextBox: true,
    fontFace: BODY_FONT, fontSize: 12, color: "7C90A5", margin: 0, italic: true,
  });
}

// ============================================================= SLIDE 2: PROBLEM
{
  const s = pres.addSlide();
  s.background = { color: LIGHT_BG };
  s.addText("The Problem", {
    x: 0.6, y: 0.45, w: 8, h: 0.7, fontFace: HEAD_FONT, fontSize: 32, bold: true, color: NAVY, isTextBox: true, margin: 0,
  });
  s.addText("Fleet managers still fight spreadsheets instead of managing equipment", {
    x: 0.6, y: 1.05, w: 10.5, h: 0.5, fontFace: BODY_FONT, fontSize: 15, color: TEXT_MUTED, isTextBox: true, margin: 0,
  });

  const rows = [
    ["1", "Manual & slow", "Managers manually cross-reference hours, downtime, and fuel logs to answer basic operational questions."],
    ["2", "Issues found too late", "Downtime spikes and fuel waste are often discovered only after they've already cost money."],
    ["3", "No natural access", "There is no simple way to just ask \u201cwhich equipment needs attention?\u201d and get an instant, data-grounded answer."],
  ];
  let y = 1.85;
  rows.forEach(([num, title, desc]) => {
    circleIcon(s, 0.7, y, 0.6, num, ORANGE);
    s.addText(title, {
      x: 1.55, y: y - 0.05, w: 10.5, h: 0.4, fontFace: HEAD_FONT, fontSize: 17, bold: true, color: NAVY, isTextBox: true, margin: 0,
    });
    s.addText(desc, {
      x: 1.55, y: y + 0.38, w: 10.7, h: 0.6, fontFace: BODY_FONT, fontSize: 12.5, color: TEXT_DARK, isTextBox: true, margin: 0, lineSpacingMultiple: 1.15,
    });
    y += 1.35;
  });
  footer(s, 2);
}

// ============================================================= SLIDE 3: SOLUTION
{
  const s = pres.addSlide();
  s.background = { color: LIGHT_BG };
  s.addText("The Solution", {
    x: 0.6, y: 0.45, w: 8, h: 0.7, fontFace: HEAD_FONT, fontSize: 32, bold: true, color: NAVY, isTextBox: true, margin: 0,
  });
  s.addText("Ask your fleet a question in plain language — get an instant, actionable answer", {
    x: 0.6, y: 1.05, w: 11.5, h: 0.5, fontFace: BODY_FONT, fontSize: 15, color: TEXT_MUTED, isTextBox: true, margin: 0,
  });

  // Chat mockup
  const chatX = 0.7, chatW = 7.6;
  s.addShape("roundRect", { x: chatX, y: 1.85, w: chatW, h: 4.7, rectRadius: 0.12, fill: { color: WHITE }, line: { color: LIGHT_GREY, width: 1 }, shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 8, offset: 3, angle: 90 } });

  const bubbles = [
    { who: "user", text: "Which equipment has the highest downtime?" },
    { who: "ai", text: "EQ-024, EQ-013, and EQ-026 show 17-21% downtime — more than double the fleet average. Recommend priority inspection." },
    { who: "user", text: "What's causing the fuel spike on EQ-008?" },
    { who: "ai", text: "Fuel use jumped 47% over the last 14 days vs. its own baseline — consistent with a leak or clogged filter." },
  ];
  let by = 2.1;
  bubbles.forEach(b => {
    const isUser = b.who === "user";
    const bw = 5.6;
    const bx = isUser ? chatX + chatW - bw - 0.3 : chatX + 0.3;
    const bh = 0.85;
    s.addShape("roundRect", {
      x: bx, y: by, w: bw, h: bh, rectRadius: 0.1,
      fill: { color: isUser ? NAVY : LIGHT_GREY }, line: { type: "none" },
    });
    s.addText(b.text, {
      x: bx + 0.2, y: by, w: bw - 0.4, h: bh, valign: "middle",
      fontFace: BODY_FONT, fontSize: 11, color: isUser ? WHITE : TEXT_DARK, isTextBox: true, margin: 0, lineSpacingMultiple: 1.1,
    });
    by += bh + 0.22;
  });

  // Right column: value props
  const vx = 8.65;
  s.addText("What you get", {
    x: vx, y: 1.85, w: 4, h: 0.4, fontFace: HEAD_FONT, fontSize: 16, bold: true, color: TEAL, isTextBox: true, margin: 0,
  });
  const values = [
    "Instant natural-language answers",
    "Automatic priority flagging",
    "Root-cause explanations, not just numbers",
    "One-click fleet performance reports",
  ];
  let vy = 2.4;
  values.forEach(v => {
    s.addShape("ellipse", { x: vx, y: vy + 0.05, w: 0.12, h: 0.12, fill: { color: ORANGE }, line: { type: "none" } });
    s.addText(v, {
      x: vx + 0.3, y: vy - 0.08, w: 3.8, h: 0.5, fontFace: BODY_FONT, fontSize: 12.5, color: TEXT_DARK, isTextBox: true, margin: 0, valign: "top",
    });
    vy += 0.7;
  });
  footer(s, 3);
}

// ============================================================= SLIDE 4: ARCHITECTURE
{
  const s = pres.addSlide();
  s.background = { color: LIGHT_BG };
  s.addText("System Architecture", {
    x: 0.6, y: 0.45, w: 8, h: 0.7, fontFace: HEAD_FONT, fontSize: 32, bold: true, color: NAVY, isTextBox: true, margin: 0,
  });
  s.addText("A five-stage pipeline from raw fleet data to an operational decision", {
    x: 0.6, y: 1.05, w: 11, h: 0.5, fontFace: BODY_FONT, fontSize: 15, color: TEXT_MUTED, isTextBox: true, margin: 0,
  });

  const stages = [
    ["Data Input", "Daily equipment logs"],
    ["Processing", "Cleaning & KPI calc"],
    ["AI Agent", "LLM + tool calling"],
    ["Dashboard", "Streamlit UI"],
    ["Output", "Insights & actions"],
  ];
  const boxW = 2.05, gap = 0.35, startX = 0.75, boxY = 3.0, boxH = 1.5;
  stages.forEach((st, i) => {
    const x = startX + i * (boxW + gap);
    const color = i === 2 ? ORANGE : NAVY;
    s.addShape("roundRect", { x, y: boxY, w: boxW, h: boxH, rectRadius: 0.08, fill: { color }, line: { type: "none" } });
    s.addText(st[0], {
      x, y: boxY + 0.18, w: boxW, h: 0.5, align: "center", fontFace: HEAD_FONT, fontSize: 14, bold: true, color: WHITE, isTextBox: true, margin: 0,
    });
    s.addText(st[1], {
      x: x + 0.1, y: boxY + 0.68, w: boxW - 0.2, h: 0.7, align: "center", fontFace: BODY_FONT, fontSize: 10, color: "E8EEF3", isTextBox: true, margin: 0,
    });
    if (i < stages.length - 1) {
      s.addText("\u2192", {
        x: x + boxW, y: boxY, w: gap, h: boxH, align: "center", valign: "middle",
        fontFace: BODY_FONT, fontSize: 22, bold: true, color: TEXT_MUTED, isTextBox: true, margin: 0,
      });
    }
  });

  s.addText("Tool Library (AI Agent Functions)", {
    x: 0.6, y: 5.0, w: 6, h: 0.4, fontFace: HEAD_FONT, fontSize: 15, bold: true, color: TEAL, isTextBox: true, margin: 0,
  });
  const tools = [
    "get_top_downtime_equipment", "get_equipment_needing_attention", "explain_utilization_trend",
    "analyze_fuel_consumption", "generate_fleet_report", "compute_attention_scores (ML)",
  ];
  let tx = 0.6, ty = 5.5;
  tools.forEach((t, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const px = 0.6 + col * 4.1, py = 5.5 + row * 0.55;
    s.addShape("roundRect", { x: px, y: py, w: 3.85, h: 0.42, rectRadius: 0.06, fill: { color: WHITE }, line: { color: LIGHT_GREY, width: 1 } });
    s.addText(t, {
      x: px + 0.15, y: py, w: 3.6, h: 0.42, valign: "middle", fontFace: BODY_FONT, fontSize: 9.5, color: TEXT_DARK, isTextBox: true, margin: 0,
    });
  });
  footer(s, 4);
}

// ============================================================= SLIDE 5: RESULTS
{
  const s = pres.addSlide();
  s.background = { color: LIGHT_BG };
  s.addText("Validated Insights", {
    x: 0.6, y: 0.4, w: 8, h: 0.65, fontFace: HEAD_FONT, fontSize: 32, bold: true, color: NAVY, isTextBox: true, margin: 0,
  });
  s.addText("Tested against a realistic synthetic dataset with known embedded issues", {
    x: 0.6, y: 0.98, w: 11, h: 0.4, fontFace: BODY_FONT, fontSize: 14, color: TEXT_MUTED, isTextBox: true, margin: 0,
  });

  s.addImage({ path: "reports/chart_top_downtime.png", x: 0.5, y: 1.55, w: 7.3, h: 4.1 });

  const notes = [
    ["21.2%", "Highest downtime rate found (EQ-024) — more than double the fleet average."],
    ["47%", "Fuel-consumption spike detected on EQ-008 vs. its own baseline."],
    ["3", "Units flagged with statistically abnormal maintenance frequency."],
  ];
  let ny = 1.75;
  notes.forEach(([stat, desc]) => {
    s.addText(stat, {
      x: 8.1, y: ny, w: 2, h: 0.7, fontFace: HEAD_FONT, fontSize: 32, bold: true, color: ORANGE, isTextBox: true, margin: 0,
    });
    s.addText(desc, {
      x: 8.1, y: ny + 0.68, w: 4.6, h: 0.7, fontFace: BODY_FONT, fontSize: 11.5, color: TEXT_DARK, isTextBox: true, margin: 0, lineSpacingMultiple: 1.15,
    });
    ny += 1.55;
  });
  footer(s, 5);
}

// ============================================================= SLIDE 6: ATTENTION SCORE (native chart)
{
  const s = pres.addSlide();
  s.background = { color: LIGHT_BG };
  s.addText("One Score to Prioritize the Fleet", {
    x: 0.6, y: 0.45, w: 10, h: 0.7, fontFace: HEAD_FONT, fontSize: 30, bold: true, color: NAVY, isTextBox: true, margin: 0,
  });
  s.addText("Attention Score (0-100) combines downtime, fuel deviation, maintenance frequency, and ML anomaly detection (Isolation Forest)", {
    x: 0.6, y: 1.1, w: 11.8, h: 0.6, fontFace: BODY_FONT, fontSize: 13, color: TEXT_MUTED, isTextBox: true, margin: 0,
  });

  const chartData = [{
    name: "Attention Score",
    labels: ["EQ-026", "EQ-024", "EQ-008", "EQ-013", "EQ-004"],
    values: [56.1, 53.6, 52.6, 45.7, 35.8],
  }];
  s.addChart(pres.ChartType.bar, chartData, {
    x: 0.7, y: 1.9, w: 8.2, h: 4.6,
    barDir: "col",
    showTitle: false,
    showLegend: false,
    showValue: true,
    dataLabelColor: WHITE,
    dataLabelPosition: "inEnd",
    dataLabelFontSize: 11,
    chartColors: [ORANGE],
    catAxisLabelColor: TEXT_DARK,
    valAxisLabelColor: TEXT_DARK,
    valAxisMaxVal: 70,
    valGridLine: { color: LIGHT_GREY, size: 1 },
    catGridLine: { style: "none" },
  });

  s.addText("Why it matters", {
    x: 9.15, y: 1.9, w: 3.6, h: 0.4, fontFace: HEAD_FONT, fontSize: 15, bold: true, color: TEAL, isTextBox: true, margin: 0,
  });
  s.addText(
    "A manager doesn't need five separate charts — just one ranked list telling them exactly which unit to check first, and why.",
    { x: 9.15, y: 2.4, w: 3.7, h: 1.3, fontFace: BODY_FONT, fontSize: 12, color: TEXT_DARK, isTextBox: true, margin: 0, lineSpacingMultiple: 1.2 }
  );
  footer(s, 6);
}

// ============================================================= SLIDE 7: TECH STACK & STATUS
{
  const s = pres.addSlide();
  s.background = { color: LIGHT_BG };
  s.addText("Tech Stack & Project Status", {
    x: 0.6, y: 0.45, w: 10, h: 0.65, fontFace: HEAD_FONT, fontSize: 30, bold: true, color: NAVY, isTextBox: true, margin: 0,
  });

  s.addText("Tech Stack", {
    x: 0.6, y: 1.3, w: 4, h: 0.4, fontFace: HEAD_FONT, fontSize: 15, bold: true, color: TEAL, isTextBox: true, margin: 0,
  });
  const stack = [
    ["Core & Data", "Python, Pandas, NumPy"],
    ["AI / LLM", "OpenAI API (Function Calling)"],
    ["ML", "Scikit-learn (Isolation Forest)"],
    ["Visualization", "Plotly, Matplotlib"],
    ["Web Interface", "Streamlit"],
    ["Deployment", "GitHub, Streamlit Community Cloud"],
  ];
  let sy = 1.8;
  stack.forEach(([label, val]) => {
    s.addText(label, { x: 0.6, y: sy, w: 2.1, h: 0.4, fontFace: BODY_FONT, fontSize: 11.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    s.addText(val, { x: 2.75, y: sy, w: 3.4, h: 0.4, fontFace: BODY_FONT, fontSize: 11.5, color: TEXT_DARK, isTextBox: true, margin: 0 });
    sy += 0.5;
  });

  s.addText("10-Day Roadmap", {
    x: 6.9, y: 1.3, w: 4, h: 0.4, fontFace: HEAD_FONT, fontSize: 15, bold: true, color: TEAL, isTextBox: true, margin: 0,
  });
  const roadmap = [
    ["Day 1-2", "Setup & data", true], ["Day 3", "KPI calculation", true],
    ["Day 4-5", "AI agent + LLM", true], ["Day 6", "Streamlit dashboard", true],
    ["Day 7", "ML anomaly detection", true], ["Day 8", "Testing & refinement", true],
    ["Day 9", "Docs & presentation", true], ["Day 10", "Final review & submission", false],
  ];
  let ry = 1.8;
  roadmap.forEach(([label, desc, done]) => {
    const mark = done ? "\u2713" : "\u25CB";
    const color = done ? TEAL : TEXT_MUTED;
    s.addText(mark, { x: 6.9, y: ry, w: 0.35, h: 0.38, fontFace: BODY_FONT, fontSize: 13, bold: true, color, isTextBox: true, margin: 0 });
    s.addText(`${label} — ${desc}`, { x: 7.3, y: ry, w: 5.1, h: 0.38, fontFace: BODY_FONT, fontSize: 11.5, color: TEXT_DARK, isTextBox: true, margin: 0 });
    ry += 0.42;
  });
  footer(s, 7);
}

// ============================================================= SLIDE 8: CLOSING
{
  const s = pres.addSlide();
  s.background = { color: NAVY_DARK };
  s.addText("From Data to Smarter Operations Decisions", {
    x: 0.8, y: 2.4, w: 11.7, h: 1.1, align: "center", fontFace: HEAD_FONT, fontSize: 34, bold: true, color: WHITE, isTextBox: true, margin: 0,
  });
  s.addText(
    "FleetOps AI proves that a small team can build a working AI operations agent in 10 days — one that turns raw construction-fleet data into a decision a manager can act on today.",
    { x: 1.8, y: 3.5, w: 9.7, h: 1.0, align: "center", fontFace: BODY_FONT, fontSize: 14, color: "CADCFC", isTextBox: true, margin: 0, lineSpacingMultiple: 1.3 }
  );
  s.addShape("line", { x: 5.66, y: 4.75, w: 2, h: 0, line: { color: TEAL, width: 2 } });
  s.addText("Thank you", {
    x: 0, y: 5.1, w: 13.33, h: 0.6, align: "center", fontFace: HEAD_FONT, fontSize: 22, bold: true, color: ORANGE, isTextBox: true, margin: 0,
  });
}

pres.writeFile({ fileName: "presentation/FleetOps_AI_Presentation.pptx" }).then(() => {
  console.log("✅ تم إنشاء العرض التقديمي");
});
