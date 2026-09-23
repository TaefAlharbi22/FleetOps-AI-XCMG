"""
FleetOps AI - Analytics Tool Library
====================================
Deterministic fleet analytics used by both the built-in agent and the optional LLM mode.
"""

import pandas as pd
import numpy as np

DAILY_PATH = "data/fleet_daily_logs.csv"
EQUIP_PATH = "data/equipment_master.csv"

_OVERRIDE = {"daily": None, "equip": None}


def set_data_source(equipment_df: pd.DataFrame, daily_df: pd.DataFrame):
    _OVERRIDE["equip"] = equipment_df
    _OVERRIDE["daily"] = daily_df


def reset_data_source():
    _OVERRIDE["equip"] = None
    _OVERRIDE["daily"] = None


def using_custom_data() -> bool:
    return _OVERRIDE["daily"] is not None


def _load_data():
    if _OVERRIDE["daily"] is not None:
        daily = _OVERRIDE["daily"].copy()
        equip = _OVERRIDE["equip"].copy()
    else:
        daily = pd.read_csv(DAILY_PATH, parse_dates=["date"])
        equip = pd.read_csv(EQUIP_PATH)
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.merge(equip, on=["equipment_id", "equipment_type", "project"])


def get_project_names() -> list[str]:
    return sorted(_load_data()["project"].dropna().astype(str).unique().tolist())


def get_equipment_ids() -> list[str]:
    return sorted(_load_data()["equipment_id"].dropna().astype(str).unique().tolist())


def _safe_top_n(top_n, default=5, maximum=50) -> int:
    try:
        value = int(top_n)
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, maximum))


def _attention_action(row, downtime_threshold_pct=15.0):
    actions_en = []
    actions_ar = []
    if row["downtime_rate_%"] >= downtime_threshold_pct:
        actions_en.append("perform an immediate diagnostic inspection and schedule corrective maintenance to reduce downtime")
        actions_ar.append("إجراء فحص تشخيصي فوري وجدولة صيانة تصحيحية لتقليل التوقف")
    if row["fuel_vs_type_avg_%"] >= 20:
        actions_en.append("inspect the fuel system, filters, and engine for abnormal consumption")
        actions_ar.append("فحص نظام الوقود والفلاتر والمحرك بسبب الاستهلاك غير الطبيعي")
    if row["maintenance_flag_high"]:
        actions_en.append("run a root-cause review for recurring faults before the next shift")
        actions_ar.append("إجراء تحليل سبب جذري للأعطال المتكررة قبل الوردية القادمة")
    if not actions_en:
        actions_en.append("review the unit during the next planned maintenance window")
        actions_ar.append("مراجعة المعدة في أقرب نافذة صيانة مخططة")
    return "; ".join(actions_en), "؛ ".join(actions_ar)


def get_top_downtime_equipment(top_n: int = 5) -> dict:
    """Return equipment with the highest downtime rate, respecting the requested count."""
    top_n = _safe_top_n(top_n, default=5)
    df = _load_data()
    agg = df.groupby(["equipment_id", "equipment_type", "project"]).agg(
        operating_hours=("operating_hours", "sum"),
        downtime_hours=("downtime_hours", "sum"),
        maintenance_events=("maintenance_flag", "sum"),
    ).reset_index()
    denom = agg["operating_hours"] + agg["downtime_hours"]
    agg["downtime_rate_%"] = np.where(denom > 0, agg["downtime_hours"] / denom * 100, 0).round(1)
    top = agg.sort_values(["downtime_rate_%", "downtime_hours"], ascending=[False, False]).head(top_n)
    return {
        "tool": "get_top_downtime_equipment",
        "requested_top_n": top_n,
        "data": top.to_dict(orient="records"),
        "narrative_hint": f"Return exactly the top {top_n} units unless fewer units exist.",
    }


def get_equipment_needing_attention(downtime_threshold_pct: float = 15.0, top_n: int | None = None) -> dict:
    """Identify units needing attention and include an explainable reason + next action."""
    df = _load_data()
    agg = df.groupby(["equipment_id", "equipment_type", "project"]).agg(
        operating_hours=("operating_hours", "sum"),
        downtime_hours=("downtime_hours", "sum"),
        fuel_l=("fuel_consumption_l", "sum"),
        maintenance_events=("maintenance_flag", "sum"),
    ).reset_index()

    denom = agg["operating_hours"] + agg["downtime_hours"]
    agg["downtime_rate_%"] = np.where(denom > 0, agg["downtime_hours"] / denom * 100, 0).round(1)
    agg["fuel_eff_l_per_hr"] = np.where(
        agg["operating_hours"] > 0, agg["fuel_l"] / agg["operating_hours"], np.nan
    ).round(2)

    type_avg = agg.groupby("equipment_type")["fuel_eff_l_per_hr"].transform("mean")
    agg["fuel_vs_type_avg_%"] = np.where(
        type_avg > 0, (agg["fuel_eff_l_per_hr"] / type_avg - 1) * 100, 0
    ).round(1)

    maint_mean = agg["maintenance_events"].mean()
    maint_std = agg["maintenance_events"].std(ddof=1)
    if pd.isna(maint_std):
        maint_std = 0.0
    maint_threshold = maint_mean + 1.5 * maint_std
    agg["maintenance_flag_high"] = agg["maintenance_events"] >= maint_threshold

    flagged = agg[
        (agg["downtime_rate_%"] >= downtime_threshold_pct)
        | (agg["maintenance_flag_high"])
        | (agg["fuel_vs_type_avg_%"] >= 20)
    ].copy()

    reasons_en, reasons_ar, actions_en, actions_ar = [], [], [], []
    for _, row in flagged.iterrows():
        en = []
        ar = []
        if row["downtime_rate_%"] >= downtime_threshold_pct:
            en.append(f"High downtime ({row['downtime_rate_%']}%)")
            ar.append(f"ارتفاع نسبة التوقف ({row['downtime_rate_%']}%)")
        if row["fuel_vs_type_avg_%"] >= 20:
            en.append(f"Fuel use {row['fuel_vs_type_avg_%']}% above its {row['equipment_type']} type average")
            ar.append(f"استهلاك الوقود أعلى من متوسط نوع {row['equipment_type']} بنسبة {row['fuel_vs_type_avg_%']}%")
        if row["maintenance_flag_high"]:
            en.append(f"Abnormally frequent maintenance ({int(row['maintenance_events'])} events vs fleet avg {maint_mean:.1f})")
            ar.append(f"تكرار صيانة غير طبيعي ({int(row['maintenance_events'])} مرات مقابل متوسط أسطول {maint_mean:.1f})")
        reasons_en.append(" + ".join(en))
        reasons_ar.append(" + ".join(ar))
        a_en, a_ar = _attention_action(row, downtime_threshold_pct)
        actions_en.append(a_en)
        actions_ar.append(a_ar)

    flagged["reason"] = reasons_en
    flagged["reason_ar"] = reasons_ar
    flagged["recommended_action"] = actions_en
    flagged["recommended_action_ar"] = actions_ar

    # A deterministic severity score used only to order flagged units.
    flagged["priority_index"] = (
        flagged["downtime_rate_%"] * 1.0
        + flagged["fuel_vs_type_avg_%"].clip(lower=0) * 0.35
        + flagged["maintenance_events"] * 2.5
    )
    flagged = flagged.sort_values(["priority_index", "downtime_rate_%"], ascending=False)

    if top_n is not None:
        top_n = _safe_top_n(top_n, default=5)
        flagged = flagged.head(top_n)

    cols = [
        "equipment_id", "equipment_type", "project", "downtime_rate_%",
        "fuel_eff_l_per_hr", "fuel_vs_type_avg_%", "maintenance_events",
        "reason", "reason_ar", "recommended_action", "recommended_action_ar",
    ]
    return {
        "tool": "get_equipment_needing_attention",
        "requested_top_n": top_n,
        "data": flagged[cols].to_dict(orient="records"),
        "narrative_hint": "Ranked equipment requiring intervention, each with reason and a practical next action.",
    }


def explain_utilization_trend(project: str | None = None) -> dict:
    """Analyze utilization weekly for the whole fleet or a named project."""
    df = _load_data()
    matched_project = None
    if project:
        lookup = {str(p).casefold(): str(p) for p in df["project"].dropna().unique()}
        matched_project = lookup.get(str(project).casefold())
        if matched_project is None:
            return {
                "tool": "explain_utilization_trend",
                "error_code": "project_not_found",
                "project": project,
                "error": f"Project '{project}' was not found",
                "available_projects": sorted(lookup.values()),
            }
        df = df[df["project"] == matched_project].copy()

    df["week"] = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    weekly = df.groupby("week", as_index=False).agg(
        operating_hours=("operating_hours", "sum"),
        downtime_hours=("downtime_hours", "sum"),
    )
    denom = weekly["operating_hours"] + weekly["downtime_hours"]
    weekly["utilization_%"] = np.where(denom > 0, weekly["operating_hours"] / denom * 100, 0).round(1)
    weekly["week"] = weekly["week"].dt.strftime("%Y-%m-%d")

    first3 = weekly["utilization_%"].head(3).mean()
    last3 = weekly["utilization_%"].tail(3).mean()
    delta = round(float(last3 - first3), 1)

    recent_cutoff = df["date"].max() - pd.Timedelta(days=21)
    recent = df[df["date"] >= recent_cutoff]
    downtime_by_type = recent.groupby("equipment_type")["downtime_hours"].sum().sort_values(ascending=False)
    likely_driver = str(downtime_by_type.index[0]) if not downtime_by_type.empty else "N/A"

    return {
        "tool": "explain_utilization_trend",
        "scope": matched_project or "Entire fleet",
        "weekly_trend": weekly[["week", "utilization_%"]].to_dict(orient="records"),
        "first_3_weeks_avg_%": round(float(first3), 1),
        "last_3_weeks_avg_%": round(float(last3), 1),
        "change_%": delta,
        "likely_driver_equipment_type": likely_driver,
        "narrative_hint": "The driver is calculated from downtime within the same requested scope.",
    }


def analyze_fuel_consumption(equipment_id: str | None = None) -> dict:
    """Detect abnormal fuel change against each unit's own historical baseline."""
    df = _load_data()
    matched_equipment = None
    if equipment_id:
        lookup = {str(e).casefold(): str(e) for e in df["equipment_id"].dropna().unique()}
        matched_equipment = lookup.get(str(equipment_id).casefold())
        if matched_equipment is None:
            return {
                "tool": "analyze_fuel_consumption",
                "error_code": "equipment_not_found",
                "equipment_id": equipment_id,
                "error": f"Equipment ID {equipment_id} was not found in the current fleet dataset",
            }
        df = df[df["equipment_id"] == matched_equipment].copy()

    df = df.sort_values("date")
    results = []
    for eq_id, g in df.groupby("equipment_id"):
        g = g.copy()
        g["fuel_per_hr"] = g["fuel_consumption_l"] / g["operating_hours"].replace(0, np.nan)
        baseline = g["fuel_per_hr"].iloc[: max(1, len(g) // 2)].mean()
        recent = g["fuel_per_hr"].tail(14).mean()
        if pd.isna(baseline) or baseline == 0 or pd.isna(recent):
            pct_change = 0.0
        else:
            pct_change = round(float((recent - baseline) / baseline * 100), 1)
        if abs(pct_change) >= 15:
            results.append({
                "equipment_id": eq_id,
                "equipment_type": g["equipment_type"].iloc[0],
                "baseline_l_per_hr": round(float(baseline), 2),
                "recent_l_per_hr": round(float(recent), 2),
                "change_%": pct_change,
                "flag": "Suspicious increase" if pct_change > 0 else "Notable decrease",
            })

    results = sorted(results, key=lambda x: abs(x["change_%"]), reverse=True)
    return {
        "tool": "analyze_fuel_consumption",
        "equipment_id": matched_equipment,
        "anomalies_found": len(results),
        "data": results,
        "narrative_hint": "Abnormal fuel changes are compared with each unit's own historical baseline.",
    }


def generate_fleet_report() -> dict:
    """Generate a complete report plus three concrete management actions."""
    df = _load_data()
    total_hours = float(df["operating_hours"].sum())
    total_downtime = float(df["downtime_hours"].sum())
    total_fuel = float(df["fuel_consumption_l"].sum())

    by_project = df.groupby("project").agg(
        operating_hours=("operating_hours", "sum"),
        downtime_hours=("downtime_hours", "sum"),
        fuel_l=("fuel_consumption_l", "sum"),
    ).reset_index()
    denom = by_project["operating_hours"] + by_project["downtime_hours"]
    by_project["utilization_%"] = np.where(denom > 0, by_project["operating_hours"] / denom * 100, 0).round(1)

    top_issues = get_top_downtime_equipment(3)["data"]
    fuel_anomalies = analyze_fuel_consumption()["data"]
    lowest_project = by_project.sort_values("utilization_%").iloc[0].to_dict() if not by_project.empty else None

    actions = []
    actions_ar = []
    if top_issues:
        first = top_issues[0]
        actions.append(
            f"Prioritize diagnostic inspection and corrective maintenance for {first['equipment_id']} "
            f"({first['downtime_rate_%']}% downtime), the highest downtime unit."
        )
        actions_ar.append(
            f"إعطاء الأولوية لفحص وصيانة {first['equipment_id']} لأنها الأعلى توقفًا بنسبة {first['downtime_rate_%']}%."
        )
    if len(top_issues) > 1:
        ids = ", ".join(x["equipment_id"] for x in top_issues[1:])
        actions.append(f"Schedule follow-up diagnostics for the next high-downtime units: {ids}.")
        actions_ar.append(f"جدولة فحوصات لاحقة للمعدات التالية ذات التوقف المرتفع: {ids}.")
    if fuel_anomalies:
        a = fuel_anomalies[0]
        actions.append(
            f"Inspect the fuel system of {a['equipment_id']} after a {abs(a['change_%'])}% abnormal consumption change."
        )
        actions_ar.append(
            f"فحص نظام الوقود للمعدة {a['equipment_id']} بعد تغير غير طبيعي في الاستهلاك بنسبة {abs(a['change_%'])}%."
        )
    elif lowest_project:
        actions.append(
            f"Review {lowest_project['project']} because it has the lowest project utilization at {lowest_project['utilization_%']}%."
        )
        actions_ar.append(
            f"مراجعة مشروع {lowest_project['project']} لأنه الأقل استخدامًا بنسبة {lowest_project['utilization_%']}%."
        )

    # Keep exactly three management actions when possible.
    if lowest_project and len(actions) < 3:
        actions.append(
            f"Review {lowest_project['project']} because it has the lowest project utilization at {lowest_project['utilization_%']}%."
        )
        actions_ar.append(
            f"مراجعة مشروع {lowest_project['project']} لأنه الأقل استخدامًا بنسبة {lowest_project['utilization_%']}%."
        )

    actions = actions[:3]
    actions_ar = actions_ar[:3]

    total_window = total_hours + total_downtime
    overall_util = round(total_hours / total_window * 100, 1) if total_window > 0 else 0.0

    return {
        "tool": "generate_fleet_report",
        "period": f"{df['date'].min().date()} - {df['date'].max().date()}",
        "fleet_size": int(df["equipment_id"].nunique()),
        "total_operating_hours": round(total_hours, 1),
        "total_downtime_hours": round(total_downtime, 1),
        "overall_utilization_%": overall_util,
        "total_fuel_l": round(total_fuel, 1),
        "by_project": by_project.to_dict(orient="records"),
        "top_downtime_equipment": top_issues,
        "fuel_anomalies": fuel_anomalies,
        "manager_actions": actions,
        "manager_actions_ar": actions_ar,
        "narrative_hint": "Use overview + top issues + exactly three management actions when available.",
    }


def _estimate_service_hours(df: pd.DataFrame, equipment_type: str, equipment_id: str | None = None) -> float:
    """Estimate a service window from observed maintenance-day downtime, without inventing cost data."""
    maintenance = df[(df["maintenance_flag"] > 0) & (df["downtime_hours"] > 0)].copy()
    values = pd.Series(dtype=float)

    if equipment_id:
        values = maintenance.loc[maintenance["equipment_id"] == equipment_id, "downtime_hours"]
    if values.empty:
        values = maintenance.loc[maintenance["equipment_type"] == equipment_type, "downtime_hours"]
    if values.empty:
        values = maintenance["downtime_hours"]

    estimate = float(values.median()) if not values.empty else 2.0
    if pd.isna(estimate) or estimate <= 0:
        estimate = 2.0
    return round(max(1.0, min(estimate, 12.0)), 1)


def build_maintenance_plan(top_n: int = 8, horizon_days: int = 7) -> dict:
    """Build an explainable, data-driven maintenance action plan for the highest-priority units."""
    # Lazy import avoids a circular import because ml_anomaly imports this module.
    import ml_anomaly

    top_n = _safe_top_n(top_n, default=8, maximum=20)
    try:
        horizon_days = max(1, min(int(horizon_days), 30))
    except (TypeError, ValueError):
        horizon_days = 7

    df = _load_data()
    scores = ml_anomaly.compute_attention_scores(top_n=top_n)["data"]
    if not scores:
        return {
            "tool": "build_maintenance_plan",
            "horizon_days": horizon_days,
            "requested_top_n": top_n,
            "data": [],
            "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "estimated_service_hours": 0.0},
        }

    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    schedule_counters = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    rows = []

    for rank, item in enumerate(scores, 1):
        score = float(item["attention_score"])
        if score >= 50:
            priority = "Critical"
            timing = "Today"
            day_number = 1
        elif score >= 35:
            priority = "High"
            timing = "Within 48h"
            schedule_counters[priority] += 1
            day_number = min(horizon_days, 2 + ((schedule_counters[priority] - 1) % max(1, min(2, horizon_days - 1))))
        elif score >= 20:
            priority = "Medium"
            timing = "This week"
            schedule_counters[priority] += 1
            start_day = min(4, horizon_days)
            span = max(1, horizon_days - start_day + 1)
            day_number = start_day + ((schedule_counters[priority] - 1) % span)
        else:
            priority = "Low"
            timing = "Planned review"
            day_number = horizon_days

        priority_counts[priority] += 1
        service_hours = _estimate_service_hours(
            df, item["equipment_type"], item["equipment_id"]
        )
        rows.append({
            "rank": rank,
            "day": f"Day {day_number}",
            "day_number": day_number,
            "timing": timing,
            "priority": priority,
            "equipment_id": item["equipment_id"],
            "equipment_type": item["equipment_type"],
            "project": item["project"],
            "attention_score": item["attention_score"],
            "reason": item["reason"],
            "reason_ar": item["reason_ar"],
            "recommended_action": item["recommended_action"],
            "recommended_action_ar": item["recommended_action_ar"],
            "estimated_service_hours": service_hours,
        })

    rows = sorted(rows, key=lambda x: (x["day_number"], x["rank"]))
    return {
        "tool": "build_maintenance_plan",
        "horizon_days": horizon_days,
        "requested_top_n": top_n,
        "data": rows,
        "summary": {
            "critical": priority_counts["Critical"],
            "high": priority_counts["High"],
            "medium": priority_counts["Medium"],
            "low": priority_counts["Low"],
            "estimated_service_hours": round(sum(r["estimated_service_hours"] for r in rows), 1),
        },
        "method_note": (
            "Priority comes from the existing Attention Score. Service-window hours are estimated "
            "from observed maintenance-day downtime for the same unit/type in the current dataset."
        ),
    }


def simulate_maintenance_delay(equipment_id: str, delay_days: int = 7) -> dict:
    """Estimate operational impact if maintenance is delayed for a specific unit.

    This is a transparent scenario model, not a failure-probability prediction. It uses the unit's
    observed daily operating/downtime pattern plus its current Attention Score to stress the
    downtime assumption as the delay gets longer.
    """
    if not equipment_id:
        return {
            "tool": "simulate_maintenance_delay",
            "error_code": "equipment_id_required",
            "error": "An equipment ID is required for a what-if maintenance scenario",
        }

    try:
        delay_days = max(1, min(int(delay_days), 30))
    except (TypeError, ValueError):
        delay_days = 7

    df = _load_data()
    lookup = {str(e).casefold(): str(e) for e in df["equipment_id"].dropna().unique()}
    matched = lookup.get(str(equipment_id).casefold())
    if matched is None:
        return {
            "tool": "simulate_maintenance_delay",
            "error_code": "equipment_not_found",
            "equipment_id": equipment_id,
            "error": f"Equipment ID {equipment_id} was not found in the current fleet dataset",
        }

    import ml_anomaly
    scores = ml_anomaly.compute_attention_scores(top_n=50)["data"]
    score_row = next((r for r in scores if r["equipment_id"] == matched), None)
    if score_row is None:
        return {
            "tool": "simulate_maintenance_delay",
            "error_code": "score_not_available",
            "equipment_id": matched,
            "error": f"Attention Score is not available for {matched}",
        }

    unit = df[df["equipment_id"] == matched].copy()
    avg_op_day = float(unit["operating_hours"].mean())
    avg_down_day = float(unit["downtime_hours"].mean())
    baseline_op = avg_op_day * delay_days
    baseline_down = avg_down_day * delay_days
    baseline_window = baseline_op + baseline_down
    baseline_util = (baseline_op / baseline_window * 100) if baseline_window > 0 else 0.0

    attention_score = float(score_row["attention_score"])
    # Transparent heuristic: stress observed downtime according to current attention risk and delay length.
    escalation_pct = min(60.0, (attention_score / 100.0) * (delay_days / 7.0) * 25.0)
    projected_down = baseline_down * (1.0 + escalation_pct / 100.0)
    projected_window = baseline_op + projected_down
    projected_util = (baseline_op / projected_window * 100) if projected_window > 0 else 0.0
    extra_down = max(0.0, projected_down - baseline_down)

    if attention_score >= 50 or (attention_score >= 35 and delay_days >= 7):
        impact_band = "High"
        recommendation = "Prioritize maintenance now; delaying increases the operational downtime exposure."
        recommendation_ar = "إعطاء الصيانة أولوية الآن؛ التأجيل يزيد التعرض التشغيلي لساعات التوقف."
    elif attention_score >= 35 or delay_days >= 7:
        impact_band = "Moderate"
        recommendation = "Schedule maintenance within 48 hours and monitor downtime closely until service."
        recommendation_ar = "جدولة الصيانة خلال 48 ساعة ومراقبة التوقف عن قرب حتى موعد الخدمة."
    else:
        impact_band = "Low"
        recommendation = "Keep the unit in the planned maintenance queue and monitor for worsening signals."
        recommendation_ar = "الإبقاء على المعدة ضمن خطة الصيانة ومراقبة أي تدهور في المؤشرات."

    service_hours = _estimate_service_hours(unit, score_row["equipment_type"], matched)
    return {
        "tool": "simulate_maintenance_delay",
        "equipment_id": matched,
        "equipment_type": score_row["equipment_type"],
        "project": score_row["project"],
        "delay_days": delay_days,
        "attention_score": round(attention_score, 1),
        "impact_band": impact_band,
        "baseline_expected_downtime_hours": round(baseline_down, 2),
        "projected_delay_downtime_hours": round(projected_down, 2),
        "additional_downtime_hours": round(extra_down, 2),
        "baseline_utilization_%": round(baseline_util, 1),
        "projected_utilization_%": round(projected_util, 1),
        "utilization_change_pp": round(projected_util - baseline_util, 1),
        "estimated_service_hours": service_hours,
        "reason": score_row["reason"],
        "reason_ar": score_row["reason_ar"],
        "recommended_action": recommendation,
        "recommended_action_ar": recommendation_ar,
        "method_note": (
            "Scenario estimate only: observed daily downtime is stress-tested using the current "
            "Attention Score and the selected delay length. It is not a failure probability forecast."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_top_downtime_equipment(3), ensure_ascii=False, indent=2, default=str))
