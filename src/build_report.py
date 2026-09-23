import sys
sys.path.insert(0, "src")
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, HRFlowable
)
import tools

NAVY = colors.HexColor("#1a3a5c")
TEAL = colors.HexColor("#2a9d8f")
ORANGE = colors.HexColor("#e76f51")
LIGHT_GREY = colors.HexColor("#f4f6f8")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("CoverTitle", fontSize=28, leading=34, alignment=TA_CENTER,
                          textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=6))
styles.add(ParagraphStyle("CoverSubtitle", fontSize=15, leading=20, alignment=TA_CENTER,
                          textColor=colors.HexColor("#444444"), fontName="Helvetica", spaceAfter=4))
styles.add(ParagraphStyle("SectionHeading", fontSize=16, leading=20, textColor=NAVY,
                          fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8))
styles.add(ParagraphStyle("SubHeading", fontSize=12.5, leading=16, textColor=TEAL,
                          fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle("BodyText2", fontSize=10.3, leading=15, alignment=TA_LEFT,
                          textColor=colors.HexColor("#222222"), spaceAfter=6))
styles.add(ParagraphStyle("BulletText", fontSize=10.3, leading=15, leftIndent=14,
                          bulletIndent=2, spaceAfter=4))
styles.add(ParagraphStyle("Caption", fontSize=8.5, leading=11, alignment=TA_CENTER,
                          textColor=colors.HexColor("#777777"), fontName="Helvetica-Oblique", spaceAfter=14))

story = []

# =============================================================================
# COVER PAGE
# =============================================================================
story.append(Spacer(1, 1.6 * inch))
story.append(Paragraph("FleetOps AI", styles["CoverTitle"]))
story.append(Paragraph("An AI Operations Agent for Construction Equipment", styles["CoverSubtitle"]))
story.append(Spacer(1, 0.35 * inch))
story.append(HRFlowable(width="40%", thickness=1.2, color=TEAL, hAlign="CENTER"))
story.append(Spacer(1, 0.35 * inch))
story.append(Paragraph("Project Report", ParagraphStyle("covermeta", fontSize=13, alignment=TA_CENTER,
                                                          textColor=colors.HexColor("#555555"), spaceAfter=4)))
story.append(Paragraph("Track: AI + Construction Machinery &rarr; AI + Operation",
                        ParagraphStyle("covermeta2", fontSize=11, alignment=TA_CENTER,
                                       textColor=colors.HexColor("#777777"), spaceAfter=2)))
story.append(Paragraph("15th China International College Students' Innovation &amp; Entrepreneurship Competition",
                        ParagraphStyle("covermeta3", fontSize=10.5, alignment=TA_CENTER,
                                       textColor=colors.HexColor("#999999"), spaceAfter=15)))
story.append(HRFlowable(width="25%", thickness=0.8, color=ORANGE, hAlign="CENTER"))
story.append(Spacer(1, 0.2 * inch))
story.append(Paragraph("<b>Prepared by: FleetOps AI Team</b>",
                        ParagraphStyle("teamtitle", fontSize=11, alignment=TA_CENTER,
                                       textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=6)))
story.append(Paragraph("<b>Project Leader:</b> Raghad Altrisy<br/><b>Core Members:</b> Taif Alharbi &bull; Jood Alwajeeh",
                        ParagraphStyle("teamnames", fontSize=10, alignment=TA_CENTER,
                                       textColor=colors.HexColor("#444444"), spaceAfter=0)))
story.append(PageBreak())

# =============================================================================
# 1. EXECUTIVE SUMMARY
# =============================================================================
story.append(Paragraph("1. Executive Summary", styles["SectionHeading"]))
story.append(Paragraph(
    "Construction fleet managers currently rely on manual review of spreadsheets and periodic reports to "
    "track equipment performance &mdash; a slow process that delays the detection of downtime spikes, fuel "
    "waste, and maintenance issues. <b>FleetOps AI</b> is an AI Operations Agent that lets managers ask "
    "natural-language questions about their fleet (e.g. <i>\u201cWhich equipment has the highest downtime?\u201d</i>) "
    "and receive instant, data-grounded answers, insights, and actionable recommendations.",
    styles["BodyText2"]))
story.append(Paragraph(
    "Within a 10-day sprint, the team built a working prototype covering the full pipeline: data ingestion, "
    "KPI computation, an AI agent with tool-calling, an interactive dashboard, and cloud deployment &mdash; "
    "demonstrating the core value proposition end-to-end rather than a partial concept.",
    styles["BodyText2"]))

report = tools.generate_fleet_report()
kpi_table_data = [
    ["Metric", "Value"],
    ["Fleet size", f"{report['fleet_size']} units"],
    ["Monitoring period", report["period"]],
    ["Overall utilization rate", f"{report['overall_utilization_%']}%"],
    ["Total operating hours", f"{report['total_operating_hours']:,.0f} hrs"],
    ["Total downtime hours", f"{report['total_downtime_hours']:,.0f} hrs"],
    ["Total fuel consumption", f"{report['total_fuel_l']:,.0f} L"],
]
t = Table(kpi_table_data, colWidths=[2.6 * inch, 2.6 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 6))
story.append(t)

# =============================================================================
# 2. PROBLEM & OBJECTIVES
# =============================================================================
story.append(Paragraph("2. Problem Statement &amp; Objectives", styles["SectionHeading"]))
story.append(Paragraph("<b>The Problem</b>", styles["SubHeading"]))
story.append(Paragraph(
    "Construction fleets generate large volumes of operational data (hours, downtime, fuel, maintenance) "
    "that is rarely analyzed in real time. Managers spend hours manually cross-referencing spreadsheets to "
    "answer basic operational questions, and often discover equipment issues only after they become costly.",
    styles["BodyText2"]))
story.append(Paragraph("<b>Objectives</b>", styles["SubHeading"]))
for b in [
    "Let managers query fleet data using natural language instead of manual spreadsheet analysis.",
    "Automatically surface equipment needing urgent attention (high downtime, abnormal maintenance frequency).",
    "Detect abnormal patterns such as sudden fuel-consumption spikes that may indicate mechanical issues.",
    "Generate ready-to-use monthly fleet performance reports.",
    "Deliver all of the above through a simple, accessible web dashboard.",
]:
    story.append(Paragraph(f"&bull; {b}", styles["BulletText"]))

# =============================================================================
# 3. METHODOLOGY & ARCHITECTURE
# =============================================================================
story.append(Paragraph("3. Methodology &amp; System Architecture", styles["SectionHeading"]))
story.append(Paragraph(
    "The system follows a five-stage pipeline, moving from raw fleet data to actionable operational decisions:",
    styles["BodyText2"]))

arch_data = [
    ["Stage", "Function"],
    ["Data Input", "Daily equipment logs: operating hours, downtime, fuel consumption, maintenance events, project, location"],
    ["Data Processing", "Cleaning, feature engineering, and KPI calculation (Pandas)"],
    ["AI Agent", "LLM + tool-calling layer that interprets natural-language questions and selects the right analysis function"],
    ["Visualization & UI", "Streamlit dashboard: interactive charts, KPI cards, and a natural-language chat interface"],
    ["Output", "Answers to user questions, visual analysis, recommendations, and performance reports"],
]
t2 = Table(arch_data, colWidths=[1.4 * inch, 4.5 * inch])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), TEAL),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 6))
story.append(t2)

story.append(Paragraph("<b>Tool Library (AI Agent Functions)</b>", styles["SubHeading"]))
for b in [
    "<b>get_top_downtime_equipment</b> &mdash; ranks equipment by downtime rate.",
    "<b>get_equipment_needing_attention</b> &mdash; flags equipment with abnormal downtime, maintenance "
    "frequency, or fuel use (compared fairly within its own equipment type).",
    "<b>explain_utilization_trend</b> &mdash; analyzes weekly utilization trends and identifies the likely driver of change.",
    "<b>analyze_fuel_consumption</b> &mdash; detects recent abnormal fuel-consumption spikes per unit.",
    "<b>generate_fleet_report</b> &mdash; compiles a full fleet performance summary.",
]:
    story.append(Paragraph(f"&bull; {b}", styles["BulletText"]))

story.append(Paragraph("<b>Tech Stack</b>", styles["SubHeading"]))
tech_data = [
    ["Layer", "Tools"],
    ["Core development", "Python"],
    ["Data analysis", "Pandas, NumPy"],
    ["AI / LLM", "OpenAI API (Chat Completions with Function Calling)"],
    ["Visualization", "Plotly, Matplotlib"],
    ["Web interface", "Streamlit"],
    ["Version control & deployment", "GitHub, Streamlit Community Cloud"],
]
t3 = Table(tech_data, colWidths=[2.0 * inch, 3.9 * inch])
t3.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 6))
story.append(t3)
story.append(PageBreak())

# =============================================================================
# 4. DATA
# =============================================================================
story.append(Paragraph("4. Data", styles["SectionHeading"]))
story.append(Paragraph(
    "Given the 10-day sprint, the team generated a realistic synthetic operations dataset "
    "(30 units, 6 equipment types, 5 active projects, 90 days of daily logs &mdash; 2,700 records) with "
    "deliberately embedded operational issues, so the AI agent's insight-detection could be validated "
    "against known ground truth before being pointed at real fleet data. The schema (equipment ID, type, "
    "project, operating hours, downtime hours, fuel consumption, maintenance flag) matches what a real "
    "telematics or ERP export would provide, so the pipeline can be pointed at live data with no code changes.",
    styles["BodyText2"]))

# =============================================================================
# 5. RESULTS & INSIGHTS
# =============================================================================
story.append(Paragraph("5. Results &amp; Insights", styles["SectionHeading"]))
story.append(Paragraph(
    "Running the AI agent against the dataset surfaced the following validated insights, confirming the "
    "detection logic works correctly before deployment on real data:",
    styles["BodyText2"]))

story.append(Image("reports/chart_top_downtime.png", width=6.3 * inch, height=3.5 * inch))
story.append(Paragraph("Figure 1 &mdash; Three units (EQ-024, EQ-013, EQ-026) show markedly higher downtime "
                        "than the rest of the fleet, warranting priority inspection.", styles["Caption"]))

story.append(Image("reports/chart_utilization_by_project.png", width=6.3 * inch, height=3.5 * inch))
story.append(Paragraph("Figure 2 &mdash; Utilization rate by project. Makkah Housing shows the lowest "
                        "utilization, correlating with its equipment's higher downtime.", styles["Caption"]))

story.append(Image("reports/chart_fuel_anomaly.png", width=6.3 * inch, height=3.1 * inch))
story.append(Paragraph("Figure 3 &mdash; Unit EQ-008 shows a 47% jump in fuel consumption per hour over the "
                        "last 14 days versus its own baseline &mdash; a strong signal of a developing "
                        "mechanical issue (e.g. leak, clogged filter) rather than simple increased usage.",
                        styles["Caption"]))

story.append(Paragraph("<b>Equipment Needing Immediate Attention</b>", styles["SubHeading"]))
attention = tools.get_equipment_needing_attention()["data"]
att_rows = [["Equipment", "Type", "Project", "Reason"]]
for r in attention:
    att_rows.append([r["equipment_id"], r["equipment_type"], r["project"], r["reason"]])
t4 = Table(att_rows, colWidths=[0.8*inch, 1.0*inch, 1.3*inch, 3.0*inch])
t4.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(Spacer(1, 4))
story.append(t4)
story.append(PageBreak())

# =============================================================================
# 6. RECOMMENDATIONS
# =============================================================================
story.append(Paragraph("6. Actionable Recommendations", styles["SectionHeading"]))
for b in [
    "<b>Inspect EQ-024, EQ-013, and EQ-026 immediately</b> &mdash; downtime rates of 17&ndash;21% are more "
    "than double the fleet average and are the single largest drag on overall utilization.",
    "<b>Schedule a mechanical check for EQ-008</b> &mdash; its sudden fuel-consumption increase is "
    "consistent with a leak or filter issue; addressing it now avoids further fuel waste and potential "
    "breakdown.",
    "<b>Review maintenance scheduling for EQ-012, EQ-014, and EQ-004</b> &mdash; their maintenance "
    "frequency is a statistical outlier versus the rest of the fleet, suggesting either a recurring fault "
    "or a scheduling inefficiency.",
    "<b>Investigate Makkah Housing's utilization decline</b> &mdash; it dropped from ~92% to ~84% over the "
    "monitoring period, likely tied to the downtime issues on its assigned equipment.",
]:
    story.append(Paragraph(f"&bull; {b}", styles["BulletText"]))

# =============================================================================
# 7. PROJECT STATUS & NEXT STEPS
# =============================================================================
story.append(Paragraph("7. Project Status &amp; Next Steps", styles["SectionHeading"]))
status_rows = [
    ["Day", "Milestone", "Status"],
    ["1&ndash;2", "Project setup, data collection & exploration", "Done"],
    ["3", "KPI calculation", "Done"],
    ["4", "AI agent tool library", "Done"],
    ["5", "LLM integration & agent logic", "Done"],
    ["6", "Streamlit dashboard (overview, chat, reports)", "Done"],
    ["7", "Advanced features (deeper anomaly detection)", "Planned"],
    ["8", "Testing & refinement", "Planned"],
    ["9", "Documentation & presentation", "In progress (this report)"],
    ["10", "Final review & submission", "Planned"],
]
t5 = Table(status_rows, colWidths=[0.7*inch, 3.7*inch, 1.7*inch])
t5.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 6))
story.append(t5)

story.append(Paragraph("<b>Future Development</b>", styles["SubHeading"]))
for b in [
    "Connect the agent to real telematics/ERP data sources (schema is already compatible).",
    "Add predictive maintenance (scikit-learn) to forecast failures before they occur, not just detect "
    "downtime after the fact.",
    "Extend the agent with proactive alerts (e.g. automatic Slack/email notification when a unit crosses a risk threshold).",
]:
    story.append(Paragraph(f"&bull; {b}", styles["BulletText"]))

# =============================================================================
# 8. CONCLUSION
# =============================================================================
story.append(Paragraph("8. Conclusion", styles["SectionHeading"]))
story.append(Paragraph(
    "FleetOps AI demonstrates that a small team can, within 10 days, build a working AI operations agent "
    "that turns raw construction-fleet data into natural-language insights and concrete recommendations. "
    "The prototype validates the core value proposition end-to-end &mdash; from data to a decision a "
    "fleet manager can act on today &mdash; and is built on a data schema and architecture ready to scale "
    "to real operational data.",
    styles["BodyText2"]))

doc = SimpleDocTemplate(
    "reports/FleetOps_AI_Project_Report.pdf",
    pagesize=letter,
    topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    leftMargin=0.85 * inch, rightMargin=0.85 * inch,
    title="FleetOps AI - Project Report",
)
doc.build(story)
print("✅ تم إنشاء التقرير: reports/FleetOps_AI_Project_Report.pdf")
