"""
FleetOps AI - Agent Logic
==========================
Two execution modes share the same analytics tools:

1) LLM MODE: optional OpenAI function calling when OPENAI_API_KEY is configured.
2) BUILT-IN MODE: deterministic local routing + analytics/ML, with no external key required.

The built-in mode is intentionally capable on its own: it extracts explicit constraints
such as top-N, equipment IDs, and project names, then calls the same production tools.
"""

import json
import os
import re
from dotenv import load_dotenv

import tools
import ml_anomaly

load_dotenv()


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_top_downtime_equipment",
            "description": "Return the equipment with the highest downtime rate, ranked descending.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "Exact number of units requested", "default": 5}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_equipment_needing_attention",
            "description": "Identify equipment needing maintenance/operational attention and return reasons plus recommended actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "downtime_threshold_pct": {"type": "number", "default": 15.0},
                    "top_n": {"type": "integer", "description": "Exact number of units requested (optional)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_utilization_trend",
            "description": "Analyze utilization trend for the whole fleet or a specifically named project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Exact project name if the user names one"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_fuel_consumption",
            "description": "Detect abnormal fuel-consumption changes for a specific equipment ID or the whole fleet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "string", "description": "Exact equipment ID if the user names one"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_fleet_report",
            "description": "Generate a fleet performance report including key management actions.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_attention_scores",
            "description": "Rank equipment by unified Attention Score (0-100), with reasons and recommended actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "Exact number of units requested", "default": 10}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_maintenance_plan",
            "description": "Build a prioritized maintenance plan for the highest-risk equipment over a planning horizon.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "Number of units to include", "default": 8},
                    "horizon_days": {"type": "integer", "description": "Planning horizon in days", "default": 7}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_maintenance_delay",
            "description": "Run a transparent what-if scenario for delaying maintenance on one equipment unit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "string", "description": "Equipment ID, for example EQ-024"},
                    "delay_days": {"type": "integer", "description": "How many days maintenance is delayed", "default": 7}
                },
                "required": ["equipment_id"]
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "get_top_downtime_equipment": tools.get_top_downtime_equipment,
    "get_equipment_needing_attention": tools.get_equipment_needing_attention,
    "explain_utilization_trend": tools.explain_utilization_trend,
    "analyze_fuel_consumption": tools.analyze_fuel_consumption,
    "generate_fleet_report": tools.generate_fleet_report,
    "compute_attention_scores": ml_anomaly.compute_attention_scores,
    "build_maintenance_plan": tools.build_maintenance_plan,
    "simulate_maintenance_delay": tools.simulate_maintenance_delay,
}

SYSTEM_PROMPT = """You are FleetOps AI, an intelligent assistant for construction fleet operations.
Understand the user's question, select the right tool, and turn the tool result into a clear,
actionable answer. Obey explicit constraints exactly: if the user asks for top 3, return exactly
3 (unless fewer valid results exist); if an equipment ID or project is named, analyze only that
entity. When the user asks why, explain the reason from returned data. When the user asks for an
action or recommendation, include a practical next action. Respond in the same language as the
user. Never invent numbers or facts; use only data returned by the tools."""


def _is_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def _extract_top_n(question: str, default: int | None = None) -> int | None:
    q = question or ""
    patterns = [
        r"\btop\s*(\d{1,2})\b",
        r"\b(?:only\s+)?(?:the\s+)?(?:highest|best|worst)\s*(\d{1,2})\b",
        r"(?:أعلى|اعلى|أفضل|افضل|أول|اول)\s*(\d{1,2})",
        r"(?:رتب|رتّب).*?(\d{1,2})\s*(?:معدات|معدة)",
        r"(\d{1,2})\s*(?:معدات|معدة)",
    ]
    for p in patterns:
        m = re.search(p, q, flags=re.IGNORECASE)
        if m:
            return max(1, min(int(m.group(1)), 20))
    return default


def _extract_days(question: str, default: int | None = None) -> int | None:
    q = question or ""
    patterns = [
        r"(\d{1,2})\s*[- ]?day(?:s)?\b",
        r"(?:delay|postpone|defer).*?(\d{1,2})\s*day",
        r"(\d{1,2})\s*(?:يوم|أيام|ايام)",
        r"(?:أجل|اجل|تأجيل|نأجل|نوجل).*?(\d{1,2})\s*(?:يوم|أيام|ايام)",
    ]
    for p in patterns:
        m = re.search(p, q, flags=re.IGNORECASE)
        if m:
            return max(1, min(int(m.group(1)), 30))
    return default


def _extract_equipment_id(question: str) -> str | None:
    m = re.search(r"\bEQ\s*-\s*(\d{1,4})\b", question or "", flags=re.IGNORECASE)
    if not m:
        return None
    return f"EQ-{int(m.group(1)):03d}"


def _extract_project(question: str) -> str | None:
    q = (question or "").casefold()
    try:
        projects = tools.get_project_names()
    except Exception:
        projects = []
    for project in sorted(projects, key=len, reverse=True):
        if project.casefold() in q:
            return project
    return None


def _question_constraints(question: str) -> dict:
    return {
        "top_n": _extract_top_n(question),
        "equipment_id": _extract_equipment_id(question),
        "project": _extract_project(question),
        "days": _extract_days(question),
    }


def _route_question(question: str) -> tuple[str, dict]:
    q = (question or "").lower()
    c = _question_constraints(question)

    if any(k in q for k in [
        "what if", "what-if", "delay maintenance", "postpone maintenance", "defer maintenance",
        "delay service", "لو أجل", "لو اجل", "تأجيل الصيانة", "أجل الصيانة", "اجل الصيانة",
    ]):
        args = {"delay_days": c["days"] or 7}
        if c["equipment_id"]:
            args["equipment_id"] = c["equipment_id"]
        else:
            args["equipment_id"] = ""
        return "simulate_maintenance_delay", args

    if any(k in q for k in [
        "maintenance plan", "maintenance planner", "7-day maintenance", "7 day maintenance",
        "maintenance schedule", "خطة صيانة", "خطة الصيانة", "جدول الصيانة", "جدول صيانة",
    ]):
        return "build_maintenance_plan", {
            "top_n": c["top_n"] or 8,
            "horizon_days": c["days"] or 7,
        }

    if any(k in q for k in [
        "attention score", "priority score", "priority ranking", "unified priority", "attention rank",
        "أولوية موحد", "درجة الأولوية", "ترتيب شامل", "درجة الاهتمام", "سكور الأولوية",
    ]):
        return "compute_attention_scores", {"top_n": c["top_n"] or 10}

    if any(k in q for k in [
        "تدخل فوري", "تحتاج تدخل", "تحتاج إلى تدخل", "تحتاج صيانة", "صيانة اليوم",
        "maintenance attention", "needs maintenance", "need maintenance", "urgent attention",
        "attention", "urgent", "priority", "high priority", "أولوية",
    ]):
        args = {}
        if c["top_n"]:
            args["top_n"] = c["top_n"]
        return "get_equipment_needing_attention", args

    if any(k in q for k in ["وقود", "fuel", "استهلاك"]):
        args = {}
        if c["equipment_id"]:
            args["equipment_id"] = c["equipment_id"]
        return "analyze_fuel_consumption", args

    if any(k in q for k in ["انخفض", "تغير", "تغيّر", "استخدام", "utilization", "قلّ", "قل معدل", "ارتفع"]):
        args = {}
        if c["project"]:
            args["project"] = c["project"]
        return "explain_utilization_trend", args

    if any(k in q for k in ["تقرير", "report", "أداء الأسطول", "fleet performance"]):
        return "generate_fleet_report", {}

    if any(k in q for k in ["downtime", "توقف", "أعلى المعدات", "اعلى المعدات"]):
        return "get_top_downtime_equipment", {"top_n": c["top_n"] or 5}

    return "generate_fleet_report", {}


def _apply_explicit_constraints(tool_name: str, fn_args: dict, question: str) -> dict:
    """Explicit user constraints win over inferred LLM tool arguments."""
    args = dict(fn_args or {})
    c = _question_constraints(question)
    if tool_name in {"get_top_downtime_equipment", "get_equipment_needing_attention", "compute_attention_scores", "build_maintenance_plan"}:
        if c["top_n"] is not None:
            args["top_n"] = c["top_n"]
    if tool_name == "build_maintenance_plan" and c["days"] is not None:
        args["horizon_days"] = c["days"]
    if tool_name == "simulate_maintenance_delay":
        if c["equipment_id"]:
            args["equipment_id"] = c["equipment_id"]
        if c["days"] is not None:
            args["delay_days"] = c["days"]
    if tool_name == "analyze_fuel_consumption" and c["equipment_id"]:
        args["equipment_id"] = c["equipment_id"]
    if tool_name == "explain_utilization_trend" and c["project"]:
        args["project"] = c["project"]
    return args


def ask_agent_real(user_question: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto",
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        for call in msg.tool_calls:
            fn_name = call.function.name
            fn_args = json.loads(call.function.arguments or "{}")
            fn_args = _apply_explicit_constraints(fn_name, fn_args, user_question)
            result = TOOL_FUNCTIONS[fn_name](**fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
        final = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return final.choices[0].message.content

    return msg.content


def _summarize(tool_name: str, result: dict, question: str = "") -> str:
    """Deterministic natural-language summary for built-in mode."""
    ar = _is_arabic(question)

    if "error" in result:
        if result.get("error_code") == "equipment_not_found":
            eq_id = result.get("equipment_id", "")
            return f"⚠️ المعدة {eq_id} غير موجودة في بيانات الأسطول الحالية. تأكد من رقم المعدة وحاول مرة أخرى." if ar else \
                f"⚠️ Equipment {eq_id} was not found in the current fleet dataset. Please check the equipment ID and try again."
        if result.get("error_code") == "project_not_found":
            project = result.get("project", "")
            return f"⚠️ المشروع '{project}' غير موجود في البيانات الحالية." if ar else \
                f"⚠️ Project '{project}' was not found in the current dataset."
        if result.get("error_code") == "equipment_id_required":
            return "⚠️ حدد رقم المعدة أولًا لتشغيل سيناريو What-If، مثل EQ-024." if ar else \
                "⚠️ Please specify an equipment ID to run a What-If scenario, for example EQ-024."
        return f"⚠️ {result['error']}"

    if tool_name == "get_top_downtime_equipment":
        lines = ["🔧 المعدات الأعلى في التوقف:" if ar else "🔧 Equipment ranked by downtime:"]
        for i, r in enumerate(result["data"], 1):
            if ar:
                lines.append(
                    f"{i}. {r['equipment_id']} ({r['equipment_type']}، {r['project']}) — "
                    f"نسبة التوقف {r['downtime_rate_%']}% | مرات الصيانة {r['maintenance_events']}"
                )
            else:
                lines.append(
                    f"{i}. {r['equipment_id']} ({r['equipment_type']}, {r['project']}) — "
                    f"downtime {r['downtime_rate_%']}% | maintenance {r['maintenance_events']}x"
                )
        return "\n".join(lines)

    if tool_name == "get_equipment_needing_attention":
        if not result["data"]:
            return "✅ لا توجد معدات تحتاج تدخلًا فوريًا حاليًا." if ar else "✅ No equipment currently needs immediate attention."
        lines = ["🚨 المعدات الأعلى أولوية للتدخل:" if ar else "🚨 Equipment needing immediate attention:"]
        for i, r in enumerate(result["data"], 1):
            if ar:
                lines.append(
                    f"{i}. **{r['equipment_id']}** ({r['equipment_type']}، {r['project']})  \n"
                    f"   السبب: {r['reason_ar']}  \n"
                    f"   الإجراء المقترح: {r['recommended_action_ar']}"
                )
            else:
                lines.append(
                    f"{i}. **{r['equipment_id']}** ({r['equipment_type']}, {r['project']})  \n"
                    f"   Reason: {r['reason']}  \n"
                    f"   Recommended action: {r['recommended_action']}"
                )
        return "\n".join(lines)

    if tool_name == "explain_utilization_trend":
        declining = result["change_%"] < 0
        if ar:
            direction = "انخفاض 📉" if declining else "ارتفاع/استقرار 📈"
            return (
                f"📊 معدل الاستخدام في **{result['scope']}** تغيّر من {result['first_3_weeks_avg_%']}% "
                f"إلى {result['last_3_weeks_avg_%']}% ({direction}، التغير {result['change_%']}%).\n"
                f"السبب المرجح: ارتفاع ساعات التوقف مؤخرًا في معدات **{result['likely_driver_equipment_type']}** داخل نفس النطاق."
            )
        direction = "declining 📉" if declining else "rising/stable 📈"
        return (
            f"📊 Utilization rate in **{result['scope']}** changed from {result['first_3_weeks_avg_%']}% "
            f"to {result['last_3_weeks_avg_%']}% ({direction}, change {result['change_%']}%).\n"
            f"Likely driver: elevated recent downtime in **{result['likely_driver_equipment_type']}** units within that scope."
        )

    if tool_name == "analyze_fuel_consumption":
        if result["anomalies_found"] == 0:
            if result.get("equipment_id"):
                return f"✅ لم يتم اكتشاف تغير غير طبيعي في استهلاك الوقود للمعدة {result['equipment_id']}." if ar else \
                    f"✅ No abnormal fuel-consumption change was detected for {result['equipment_id']}."
            return "✅ لم يتم اكتشاف ارتفاعات غير طبيعية في استهلاك الوقود حاليًا." if ar else \
                "✅ No abnormal fuel-consumption spikes detected currently."
        lines = [
            f"⛽ تم اكتشاف {result['anomalies_found']} حالة غير طبيعية في استهلاك الوقود:" if ar
            else f"⛽ {result['anomalies_found']} fuel-consumption anomaly(ies) detected:"
        ]
        for r in result["data"]:
            if ar:
                kind = "ارتفاع مشبوه" if r["change_%"] > 0 else "انخفاض ملحوظ"
                lines.append(
                    f"• {r['equipment_id']} ({r['equipment_type']}) — {kind} بنسبة {abs(r['change_%'])}% "
                    f"({r['baseline_l_per_hr']} → {r['recent_l_per_hr']} لتر/ساعة)"
                )
            else:
                lines.append(
                    f"• {r['equipment_id']} ({r['equipment_type']}) — {r['flag']} of {abs(r['change_%'])}% "
                    f"({r['baseline_l_per_hr']} → {r['recent_l_per_hr']} L/hr)"
                )
        lines.append(
            "💡 الإجراء المقترح: فحص ميكانيكي سريع لنظام الوقود/الفلتر/المحرك للمعدات أعلاه." if ar
            else "💡 Recommendation: schedule a prompt mechanical inspection (fuel system/filter/engine) for the units above."
        )
        return "\n".join(lines)

    if tool_name == "generate_fleet_report":
        if ar:
            lines = [
                f"📋 تقرير أداء الأسطول ({result['period']})",
                f"• حجم الأسطول: {result['fleet_size']}",
                f"• معدل الاستخدام العام: {result['overall_utilization_%']}%",
                f"• إجمالي ساعات التشغيل: {result['total_operating_hours']} | التوقف: {result['total_downtime_hours']}",
                f"• إجمالي استهلاك الوقود: {result['total_fuel_l']} لتر",
                "• أعلى 3 مشاكل توقف: " + ", ".join(d["equipment_id"] for d in result["top_downtime_equipment"]),
                "\n**أهم 3 إجراءات للمدير:**",
            ]
            for i, action in enumerate(result.get("manager_actions_ar", []), 1):
                lines.append(f"{i}. {action}")
        else:
            lines = [
                f"📋 Fleet Performance Report ({result['period']})",
                f"• Fleet size: {result['fleet_size']}",
                f"• Overall utilization rate: {result['overall_utilization_%']}%",
                f"• Total operating hours: {result['total_operating_hours']} | Downtime: {result['total_downtime_hours']}",
                f"• Total fuel consumption: {result['total_fuel_l']} L",
                "• Top 3 downtime issues: " + ", ".join(d["equipment_id"] for d in result["top_downtime_equipment"]),
                "\n**Top 3 management actions:**",
            ]
            for i, action in enumerate(result.get("manager_actions", []), 1):
                lines.append(f"{i}. {action}")
        return "\n".join(lines)

    if tool_name == "build_maintenance_plan":
        summary = result.get("summary", {})
        if ar:
            lines = [
                f"🗓️ **خطة صيانة لمدة {result['horizon_days']} أيام** — {len(result['data'])} معدات",
                f"حرجة: {summary.get('critical', 0)} | عالية: {summary.get('high', 0)} | متوسطة: {summary.get('medium', 0)} | منخفضة: {summary.get('low', 0)}",
            ]
            for r in result["data"]:
                lines.append(
                    f"**{r['day']} — {r['equipment_id']}** ({r['priority']})  \n"
                    f"السبب: {r['reason_ar']}  \n"
                    f"الإجراء المقترح: {r['recommended_action_ar']}"
                )
        else:
            lines = [
                f"🗓️ **{result['horizon_days']}-Day Maintenance Plan** — {len(result['data'])} units",
                f"Critical: {summary.get('critical', 0)} | High: {summary.get('high', 0)} | Medium: {summary.get('medium', 0)} | Low: {summary.get('low', 0)}",
            ]
            for r in result["data"]:
                lines.append(
                    f"**{r['day']} — {r['equipment_id']}** ({r['priority']})  \n"
                    f"Reason: {r['reason']}  \n"
                    f"Recommended action: {r['recommended_action']}"
                )
        return "\n".join(lines)

    if tool_name == "simulate_maintenance_delay":
        if ar:
            return (
                f"🧪 **سيناريو What-If للمعدة {result['equipment_id']}** — تأجيل الصيانة {result['delay_days']} أيام\n"
                f"• درجة الأولوية: {result['attention_score']}/100 ({result['impact_band']})\n"
                f"• التوقف المتوقع في خط الأساس: {result['baseline_expected_downtime_hours']} ساعة\n"
                f"• التوقف في سيناريو التأجيل: {result['projected_delay_downtime_hours']} ساعة\n"
                f"• ساعات توقف إضافية تقديرية: {result['additional_downtime_hours']} ساعة\n"
                f"• الاستخدام: {result['baseline_utilization_%']}% → {result['projected_utilization_%']}%\n"
                f"• الإجراء المقترح: {result['recommended_action_ar']}\n\n"
                f"_ملاحظة: هذا تقدير سيناريو تشغيلي وليس توقعًا لاحتمال العطل._"
            )
        return (
            f"🧪 **What-If scenario for {result['equipment_id']}** — delay maintenance by {result['delay_days']} days\n"
            f"• Attention Score: {result['attention_score']}/100 ({result['impact_band']} impact)\n"
            f"• Baseline expected downtime: {result['baseline_expected_downtime_hours']} h\n"
            f"• Delay-scenario downtime: {result['projected_delay_downtime_hours']} h\n"
            f"• Estimated additional downtime: {result['additional_downtime_hours']} h\n"
            f"• Utilization: {result['baseline_utilization_%']}% → {result['projected_utilization_%']}%\n"
            f"• Recommended action: {result['recommended_action']}\n\n"
            f"_Note: this is an operational scenario estimate, not a failure-probability forecast._"
        )

    if tool_name == "compute_attention_scores":
        lines = ["🎯 ترتيب المعدات حسب درجة الأولوية (0-100):" if ar else "🎯 Equipment ranked by unified Attention Score (0-100):"]
        for i, r in enumerate(result["data"], 1):
            if ar:
                lines.append(
                    f"{i}. **{r['equipment_id']}** ({r['equipment_type']}، {r['project']}) — الدرجة **{r['attention_score']}/100**  \n"
                    f"   السبب: {r['reason_ar']}  \n"
                    f"   الإجراء المقترح: {r['recommended_action_ar']}"
                )
            else:
                lines.append(
                    f"{i}. **{r['equipment_id']}** ({r['equipment_type']}, {r['project']}) — Attention Score **{r['attention_score']}/100**  \n"
                    f"   Reason: {r['reason']}  \n"
                    f"   Recommended action: {r['recommended_action']}"
                )
        return "\n".join(lines)

    return json.dumps(result, ensure_ascii=False, default=str)


def get_structured_result(user_question: str) -> tuple[str, dict]:
    """Return the deterministic analytics result used to build UI cards for a question."""
    tool_name, args = _route_question(user_question)
    return tool_name, TOOL_FUNCTIONS[tool_name](**args)


def ask_agent_with_context(user_question: str) -> dict:
    """Return answer text plus structured analytics for card-based presentation."""
    tool_name, result = get_structured_result(user_question)
    if os.getenv("OPENAI_API_KEY"):
        answer = ask_agent_real(user_question)
    else:
        answer = _summarize(tool_name, result, user_question)
    return {"answer": answer, "tool_name": tool_name, "result": result}


def ask_agent_test(user_question: str) -> str:
    tool_name, args = _route_question(user_question)
    result = TOOL_FUNCTIONS[tool_name](**args)
    return _summarize(tool_name, result, user_question)


def ask_agent(user_question: str) -> str:
    if os.getenv("OPENAI_API_KEY"):
        return ask_agent_real(user_question)
    return ask_agent_test(user_question)


if __name__ == "__main__":
    questions = [
        "Show ONLY the top 3 equipment units with the highest downtime.",
        "Rank the top 3 equipment units that need maintenance attention today. For each one, explain the reason and recommend the next action.",
        "Why did utilization change in Makkah Housing?",
        "Analyze fuel consumption for EQ-999.",
        "رتب لي أعلى 3 معدات تحتاج تدخل اليوم، واذكر السبب والإجراء المقترح لكل معدة.",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print(ask_agent_test(q))
        print("-" * 60)
