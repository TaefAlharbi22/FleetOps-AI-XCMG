"""
FleetOps AI - Automated Test Suite
====================================
يشغّل مجموعة اختبارات فعلية على النظام كامل ويسجّل النتائج (Expected vs Actual)
في ملف JSON يُستخدم بعدين لبناء Test Report الرسمي.
"""

import sys, json, traceback
sys.path.insert(0, "src")
import pandas as pd
import tools
import agent
import ml_anomaly

results = []


def record(tc_id, name, expected, actual, passed, notes=""):
    results.append({
        "id": tc_id, "name": name, "expected": expected, "actual": actual,
        "passed": bool(passed), "notes": notes,
    })


# --------------------------------------------------------------------------
# TC-01: سلامة البيانات المولّدة
# --------------------------------------------------------------------------
try:
    daily = pd.read_csv("data/fleet_daily_logs.csv")
    equip = pd.read_csv("data/equipment_master.csv")
    ok = (len(daily) == 2700) and (equip["equipment_id"].nunique() == 30) and (daily.isnull().sum().sum() == 0)
    record("TC-01", "Data integrity (row count, no nulls, 30 units)",
           "2700 rows, 30 units, 0 null values",
           f"{len(daily)} rows, {equip['equipment_id'].nunique()} units, {daily.isnull().sum().sum()} nulls",
           ok)
except Exception as e:
    record("TC-01", "Data integrity", "No exceptions", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-02: صحة حساب KPI (Utilization) - مقارنة يدوية
# --------------------------------------------------------------------------
try:
    df = tools._load_data()
    sample_eq = df["equipment_id"].iloc[0]
    sub = df[df["equipment_id"] == sample_eq]
    manual_util = round(sub["operating_hours"].sum() / (sub["operating_hours"].sum() + sub["downtime_hours"].sum()) * 100, 1)
    tool_result = tools.get_top_downtime_equipment(30)["data"]
    tool_row = next(r for r in tool_result if r["equipment_id"] == sample_eq)
    tool_util = round(100 - tool_row["downtime_rate_%"], 1)
    ok = abs(manual_util - tool_util) < 0.5
    record("TC-02", f"KPI calculation accuracy (manual vs tool, {sample_eq})",
           f"Utilization match within 0.5% (manual={manual_util}%)",
           f"Tool output={tool_util}%", ok)
except Exception as e:
    record("TC-02", "KPI calculation accuracy", "No exceptions", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-03: عدالة مقارنة استهلاك الوقود (إصلاح الـ bug: مقارنة بالنوع مش بالكل)
# --------------------------------------------------------------------------
try:
    attention = tools.get_equipment_needing_attention()["data"]
    dump_truck_flags = [r for r in attention if r["equipment_type"] == "Dump Truck" and "استهلاك وقود" in r["reason"]]
    # المتوقع: مفيش Dump Truck اتعلّم غلط بس لأن نوعه بيستهلك وقود أكتر بطبيعته
    all_dump_trucks = tools._load_data()
    total_dump_trucks = all_dump_trucks[all_dump_trucks["equipment_type"] == "Dump Truck"]["equipment_id"].nunique()
    ok = len(dump_truck_flags) < total_dump_trucks  # مش كل الدامب تركس اتعلّموا غلط
    record("TC-03", "Fair fuel comparison (within-type, not fleet-wide)",
           "Not all Dump Trucks flagged just for being naturally fuel-heavy",
           f"{len(dump_truck_flags)}/{total_dump_trucks} Dump Trucks flagged for fuel", ok,
           "Bug found & fixed during development: initial version compared fleet-wide average, "
           "causing false positives on naturally fuel-heavy equipment types.")
except Exception as e:
    record("TC-03", "Fair fuel comparison", "No exceptions", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-04: اكتشاف anomaly الوقود الحقيقي (EQ-008 مزروعة في البيانات)
# --------------------------------------------------------------------------
try:
    fuel_result = tools.analyze_fuel_consumption()["data"]
    detected_ids = [r["equipment_id"] for r in fuel_result]
    ok = "EQ-008" in detected_ids
    record("TC-04", "Fuel anomaly detection (ground truth: EQ-008 was injected with a fuel spike)",
           "EQ-008 appears in anomalies list",
           f"Detected units: {detected_ids}", ok)
except Exception as e:
    record("TC-04", "Fuel anomaly detection", "No exceptions", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-05: تطابق ML (Isolation Forest) مع النتائج اليدوية
# --------------------------------------------------------------------------
try:
    ml_result = ml_anomaly.detect_ml_anomalies()["data"]
    ml_ids = set(r["equipment_id"] for r in ml_result)
    manual_top3 = set(r["equipment_id"] for r in tools.get_top_downtime_equipment(3)["data"])
    overlap = ml_ids & manual_top3
    ok = len(overlap) >= 2  # على الأقل 2 من أعلى 3 لازم يظهروا في الـ ML كمان
    record("TC-05", "ML anomaly detection cross-validates manual downtime ranking",
           "At least 2 of top-3 manual downtime units also flagged by Isolation Forest",
           f"Overlap: {overlap} ({len(overlap)}/3)", ok)
except Exception as e:
    record("TC-05", "ML cross-validation", "No exceptions", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-06: التوجيه الصحيح للأسئلة الخمسة الأساسية (Agent Routing)
# --------------------------------------------------------------------------
question_tool_map = [
    ("ما المعدات التي لديها أعلى Downtime؟", "get_top_downtime_equipment", "\"Which equipment has the highest downtime?\""),
    ("أي المعدات تحتاج إلى تدخل فوري؟", "get_equipment_needing_attention", "\"Which equipment needs urgent attention?\""),
    ("لماذا انخفض معدل استخدام المعدات؟", "explain_utilization_trend", "\"Why did utilization drop?\""),
    ("ما أسباب ارتفاع استهلاك الوقود؟", "analyze_fuel_consumption", "\"What's causing the fuel increase?\""),
    ("أنشئ لي تقريرًا عن أداء الأسطول", "generate_fleet_report", "\"Generate a fleet performance report\""),
]
for q, expected_tool, label in question_tool_map:
    try:
        actual_tool, _ = agent._route_question(q)
        ok = actual_tool == expected_tool
        record("TC-06", f"Agent routing: {label}", f"Routes to {expected_tool}", f"Routed to {actual_tool}", ok)
    except Exception as e:
        record("TC-06", f"Agent routing: {label}", f"Routes to {expected_tool}", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-07: التعامل الآمن مع الحالات الحدية (Edge Cases)
# --------------------------------------------------------------------------
edge_cases = [
    ("", "(empty input)"),
    ("ما هذا؟", "(vague question, Arabic)"),
    ("asdkjaslkdj", "(random gibberish)"),
    ("1234", "(numeric-only input)"),
]
for q, label in edge_cases:
    try:
        answer = agent.ask_agent(q)
        ok = isinstance(answer, str) and len(answer) > 0
        record("TC-07", f"Edge case handling: {label}",
               "No crash, returns a safe fallback answer", "Returned valid response, no exception", ok)
    except Exception as e:
        record("TC-07", f"Edge case handling: {label}",
               "No crash", f"Exception raised: {e}", False)

# --------------------------------------------------------------------------
# TC-08: بناء الملفات (تقرير PDF + عرض PPTX) بدون أخطاء
# --------------------------------------------------------------------------
import os
ok_pdf = os.path.exists("reports/FleetOps_AI_Project_Report.pdf") and os.path.getsize("reports/FleetOps_AI_Project_Report.pdf") > 1000
ok_pptx = os.path.exists("presentation/FleetOps_AI_Presentation.pptx") and os.path.getsize("presentation/FleetOps_AI_Presentation.pptx") > 1000
record("TC-08a", "Project report PDF generated successfully", "File exists, size > 1KB",
       f"Exists={os.path.exists('reports/FleetOps_AI_Project_Report.pdf')}", ok_pdf)
record("TC-08b", "Presentation PPTX generated successfully", "File exists, size > 1KB",
       f"Exists={os.path.exists('presentation/FleetOps_AI_Presentation.pptx')}", ok_pptx)


# --------------------------------------------------------------------------
# TC-09: Regression - explicit Top-N is respected across agent routes
# --------------------------------------------------------------------------
try:
    tool_name, args = agent._route_question("Show ONLY the top 3 equipment units with the highest downtime.")
    result = agent.TOOL_FUNCTIONS[tool_name](**args)
    ok = tool_name == "get_top_downtime_equipment" and len(result["data"]) == 3
    record("TC-09a", "Top-N respected for downtime", "Exactly 3 units", f"{len(result['data'])} units", ok)
except Exception as e:
    record("TC-09a", "Top-N respected for downtime", "Exactly 3 units", f"Exception: {e}", False)

try:
    tool_name, args = agent._route_question("Rank the top 3 equipment units that need maintenance attention today.")
    result = agent.TOOL_FUNCTIONS[tool_name](**args)
    ok = (tool_name == "get_equipment_needing_attention" and len(result["data"]) == 3
          and all(r.get("recommended_action") for r in result["data"]))
    record("TC-09b", "Top-N + actions for maintenance attention",
           "Exactly 3 units with recommended actions", f"{len(result['data'])} units", ok)
except Exception as e:
    record("TC-09b", "Top-N + actions for maintenance attention", "Exactly 3 units with actions", f"Exception: {e}", False)

try:
    tool_name, args = agent._route_question("Give me ONLY the top 3 equipment units by Attention Score and explain why each one is high priority.")
    result = agent.TOOL_FUNCTIONS[tool_name](**args)
    ok = (tool_name == "compute_attention_scores" and len(result["data"]) == 3
          and all(r.get("reason") and r.get("recommended_action") for r in result["data"]))
    record("TC-09c", "Top-N + explanations for Attention Score",
           "Exactly 3 units with reason/action", f"{len(result['data'])} units", ok)
except Exception as e:
    record("TC-09c", "Top-N + explanations for Attention Score", "Exactly 3 units with reason/action", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-10: Regression - project-specific utilization is preserved
# --------------------------------------------------------------------------
try:
    tool_name, args = agent._route_question("Why did utilization change in Makkah Housing?")
    result = agent.TOOL_FUNCTIONS[tool_name](**args)
    ok = tool_name == "explain_utilization_trend" and result.get("scope") == "Makkah Housing"
    record("TC-10", "Project-specific utilization filtering", "Scope=Makkah Housing", f"Scope={result.get('scope')}", ok)
except Exception as e:
    record("TC-10", "Project-specific utilization filtering", "Scope=Makkah Housing", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-11: Regression - invalid equipment IDs fail safely
# --------------------------------------------------------------------------
try:
    tool_name, args = agent._route_question("Analyze fuel consumption for EQ-999.")
    result = agent.TOOL_FUNCTIONS[tool_name](**args)
    ok = result.get("error_code") == "equipment_not_found" and result.get("equipment_id") == "EQ-999"
    record("TC-11", "Invalid equipment ID validation", "Clear equipment_not_found response", str(result.get("error_code")), ok)
except Exception as e:
    record("TC-11", "Invalid equipment ID validation", "Clear equipment_not_found response", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-12: Regression - report contains 3 manager actions
# --------------------------------------------------------------------------
try:
    report = tools.generate_fleet_report()
    ok = len(report.get("manager_actions", [])) == 3
    record("TC-12", "Fleet report management actions", "Exactly 3 management actions", f"{len(report.get('manager_actions', []))} actions", ok)
except Exception as e:
    record("TC-12", "Fleet report management actions", "Exactly 3 management actions", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-13: Regression - Arabic request routes correctly and answers in Arabic
# --------------------------------------------------------------------------
try:
    q = "رتب لي أعلى 3 معدات تحتاج تدخل اليوم، واذكر السبب والإجراء المقترح لكل معدة."
    tool_name, args = agent._route_question(q)
    answer = agent.ask_agent_test(q)
    result = agent.TOOL_FUNCTIONS[tool_name](**args)
    ok = (tool_name == "get_equipment_needing_attention" and len(result["data"]) == 3
          and "السبب" in answer and "الإجراء المقترح" in answer)
    record("TC-13", "Arabic routing + Arabic actionable answer",
           "3 units, Arabic reason/action", f"Tool={tool_name}, units={len(result['data'])}", ok)
except Exception as e:
    record("TC-13", "Arabic routing + Arabic actionable answer", "3 units, Arabic reason/action", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-14: Maintenance Planner returns a valid 7-day prioritized schedule
# --------------------------------------------------------------------------
try:
    plan = tools.build_maintenance_plan(top_n=6, horizon_days=7)
    required = {"day", "priority", "equipment_id", "attention_score", "reason", "recommended_action", "estimated_service_hours"}
    ok = (len(plan.get("data", [])) == 6
          and all(required.issubset(r.keys()) for r in plan["data"])
          and all(1 <= int(r["day_number"]) <= 7 for r in plan["data"])
          and plan.get("summary", {}).get("estimated_service_hours", 0) > 0)
    record("TC-14", "7-day Maintenance Planner",
           "6 prioritized units with valid schedule/action/service estimate",
           f"units={len(plan.get('data', []))}, service_h={plan.get('summary', {}).get('estimated_service_hours')}", ok)
except Exception as e:
    record("TC-14", "7-day Maintenance Planner", "Valid plan", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-15: What-If Simulator returns transparent delay-impact metrics
# --------------------------------------------------------------------------
try:
    sim = tools.simulate_maintenance_delay("EQ-024", delay_days=7)
    ok = (sim.get("equipment_id") == "EQ-024"
          and sim.get("delay_days") == 7
          and sim.get("projected_delay_downtime_hours", -1) >= sim.get("baseline_expected_downtime_hours", 0)
          and "projected_utilization_%" in sim
          and sim.get("recommended_action"))
    record("TC-15", "What-If maintenance delay simulator",
           "Valid 7-day scenario with impact + recommendation",
           f"extra_down={sim.get('additional_downtime_hours')}, impact={sim.get('impact_band')}", ok)
except Exception as e:
    record("TC-15", "What-If maintenance delay simulator", "Valid scenario", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-16: What-If invalid equipment ID fails safely
# --------------------------------------------------------------------------
try:
    sim = tools.simulate_maintenance_delay("EQ-999", delay_days=7)
    ok = sim.get("error_code") == "equipment_not_found"
    record("TC-16", "What-If invalid equipment validation",
           "equipment_not_found response", str(sim.get("error_code")), ok)
except Exception as e:
    record("TC-16", "What-If invalid equipment validation", "Safe error", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-17: Agent routes new features correctly
# --------------------------------------------------------------------------
try:
    tool_name, args = agent._route_question("Build a 7-day maintenance plan for the top 5 equipment units.")
    ok1 = tool_name == "build_maintenance_plan" and args.get("top_n") == 5 and args.get("horizon_days") == 7
    record("TC-17a", "Agent routing: Maintenance Planner",
           "build_maintenance_plan top_n=5 horizon=7", f"{tool_name} {args}", ok1)
except Exception as e:
    record("TC-17a", "Agent routing: Maintenance Planner", "Correct route", f"Exception: {e}", False)

try:
    tool_name, args = agent._route_question("What if I delay maintenance for EQ-024 by 7 days?")
    ok2 = tool_name == "simulate_maintenance_delay" and args.get("equipment_id") == "EQ-024" and args.get("delay_days") == 7
    record("TC-17b", "Agent routing: What-If Simulator",
           "simulate_maintenance_delay EQ-024 delay=7", f"{tool_name} {args}", ok2)
except Exception as e:
    record("TC-17b", "Agent routing: What-If Simulator", "Correct route", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# TC-18: Structured context is available for card-based Agent UI
# --------------------------------------------------------------------------
try:
    ctx = agent.ask_agent_with_context("Give me ONLY the top 3 equipment units by Attention Score.")
    ok = (ctx.get("tool_name") == "compute_attention_scores"
          and len(ctx.get("result", {}).get("data", [])) == 3
          and isinstance(ctx.get("answer"), str) and len(ctx.get("answer")) > 0)
    record("TC-18", "Agent structured response for cards",
           "tool + structured result + answer", f"tool={ctx.get('tool_name')}", ok)
except Exception as e:
    record("TC-18", "Agent structured response for cards", "Valid context", f"Exception: {e}", False)

# --------------------------------------------------------------------------
# النتيجة النهائية
# --------------------------------------------------------------------------
with open("reports/test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

total = len(results)
passed = sum(1 for r in results if r["passed"])
print(f"\n{'='*60}\nإجمالي الاختبارات: {total} | ناجحة: {passed} | فاشلة: {total - passed}\n{'='*60}")
for r in results:
    status = "✅" if r["passed"] else "❌"
    print(f"{status} [{r['id']}] {r['name']}")
