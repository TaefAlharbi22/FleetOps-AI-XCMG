"""
FleetOps AI - ML-based Anomaly Detection
=========================================
Isolation Forest + explainable unified Attention Score.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

import tools


def detect_ml_anomalies(contamination: float = 0.15) -> dict:
    df = tools._load_data()
    agg = df.groupby(["equipment_id", "equipment_type", "project"]).agg(
        operating_hours=("operating_hours", "sum"),
        downtime_hours=("downtime_hours", "sum"),
        fuel_l=("fuel_consumption_l", "sum"),
        maintenance_events=("maintenance_flag", "sum"),
    ).reset_index()

    denom = agg["operating_hours"] + agg["downtime_hours"]
    agg["downtime_rate_%"] = np.where(denom > 0, agg["downtime_hours"] / denom * 100, 0)
    agg["fuel_eff"] = np.where(agg["operating_hours"] > 0, agg["fuel_l"] / agg["operating_hours"], 0)
    type_avg_fuel = agg.groupby("equipment_type")["fuel_eff"].transform("mean")
    agg["fuel_vs_type_%"] = np.where(type_avg_fuel > 0, (agg["fuel_eff"] / type_avg_fuel - 1) * 100, 0)

    features = agg[["downtime_rate_%", "fuel_vs_type_%", "maintenance_events", "operating_hours"]].fillna(0).copy()
    X = StandardScaler().fit_transform(features)

    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
    agg["anomaly_flag"] = model.fit_predict(X)
    agg["anomaly_score"] = -model.score_samples(X)

    anomalies = agg[agg["anomaly_flag"] == -1].sort_values("anomaly_score", ascending=False)
    return {
        "tool": "detect_ml_anomalies",
        "method": "Isolation Forest (scikit-learn)",
        "features_used": ["downtime_rate_%", "fuel_vs_type_avg_%", "maintenance_events", "operating_hours"],
        "anomalies_found": len(anomalies),
        "data": anomalies[["equipment_id", "equipment_type", "project", "downtime_rate_%",
                            "fuel_vs_type_%", "maintenance_events", "anomaly_score"]].round(2).to_dict(orient="records"),
        "narrative_hint": "Statistical outliers based on the combined operating signals.",
    }


def _norm(s: pd.Series) -> pd.Series:
    rng = s.max() - s.min()
    if rng > 0:
        return (s - s.min()) / rng * 100
    return pd.Series(np.zeros(len(s)), index=s.index)


def _score_reason_action(row):
    contribs = {
        "downtime": row["downtime_component"],
        "fuel": row["fuel_component"],
        "maintenance": row["maintenance_component"],
        "ml": row["ml_component"],
    }
    driver = max(contribs, key=contribs.get)

    if driver == "downtime":
        return (
            f"Downtime is the strongest risk signal ({row['downtime_rate_%']:.1f}%).",
            f"نسبة التوقف هي أقوى إشارة خطر ({row['downtime_rate_%']:.1f}%).",
            "Run an immediate diagnostic inspection and schedule corrective maintenance.",
            "إجراء فحص تشخيصي فوري وجدولة صيانة تصحيحية.",
        )
    if driver == "fuel":
        return (
            f"Fuel consumption is {row['fuel_dev_%']:.1f}% above the average for its equipment type.",
            f"استهلاك الوقود أعلى من متوسط نوع المعدة بنسبة {row['fuel_dev_%']:.1f}%.",
            "Inspect the fuel system, filters, and engine before continued operation.",
            "فحص نظام الوقود والفلاتر والمحرك قبل مواصلة التشغيل.",
        )
    if driver == "maintenance":
        return (
            f"Maintenance frequency is elevated ({int(row['maintenance_events'])} events).",
            f"تكرار الصيانة مرتفع ({int(row['maintenance_events'])} مرات).",
            "Perform a recurring-fault root-cause analysis and review component replacement history.",
            "إجراء تحليل سبب جذري للأعطال المتكررة ومراجعة سجل استبدال المكونات.",
        )
    return (
        "The combined operating pattern is statistically unusual according to Isolation Forest.",
        "النمط التشغيلي المجمع غير طبيعي إحصائيًا وفق نموذج Isolation Forest.",
        "Perform a targeted inspection of the unit's downtime, fuel, and maintenance history.",
        "إجراء فحص مستهدف لسجل التوقف والوقود والصيانة للمعدة.",
    )


def compute_attention_scores(top_n: int = 10) -> dict:
    """Return top-N units by explainable Attention Score (0-100)."""
    top_n = max(1, min(int(top_n or 10), 50))
    df = tools._load_data()
    agg = df.groupby(["equipment_id", "equipment_type", "project"]).agg(
        operating_hours=("operating_hours", "sum"),
        downtime_hours=("downtime_hours", "sum"),
        fuel_l=("fuel_consumption_l", "sum"),
        maintenance_events=("maintenance_flag", "sum"),
    ).reset_index()

    denom = agg["operating_hours"] + agg["downtime_hours"]
    agg["downtime_rate_%"] = np.where(denom > 0, agg["downtime_hours"] / denom * 100, 0)
    agg["fuel_eff"] = np.where(agg["operating_hours"] > 0, agg["fuel_l"] / agg["operating_hours"], 0)
    type_avg_fuel = agg.groupby("equipment_type")["fuel_eff"].transform("mean")
    agg["fuel_dev_%"] = np.where(type_avg_fuel > 0, (agg["fuel_eff"] / type_avg_fuel - 1) * 100, 0)

    ml_result = detect_ml_anomalies()
    if ml_result["data"]:
        ml_scores = pd.DataFrame(ml_result["data"])[["equipment_id", "anomaly_score"]]
    else:
        ml_scores = pd.DataFrame(columns=["equipment_id", "anomaly_score"])
    agg = agg.merge(ml_scores, on="equipment_id", how="left").fillna({"anomaly_score": 0})

    agg["downtime_component"] = _norm(agg["downtime_rate_%"]) * 0.40
    agg["fuel_component"] = _norm(agg["fuel_dev_%"].clip(lower=0)) * 0.25
    agg["maintenance_component"] = _norm(agg["maintenance_events"]) * 0.20
    agg["ml_component"] = _norm(agg["anomaly_score"]) * 0.15
    agg["attention_score"] = (
        agg["downtime_component"] + agg["fuel_component"] +
        agg["maintenance_component"] + agg["ml_component"]
    ).round(1)

    reason, reason_ar, action, action_ar = [], [], [], []
    for _, row in agg.iterrows():
        r, ra, a, aa = _score_reason_action(row)
        reason.append(r)
        reason_ar.append(ra)
        action.append(a)
        action_ar.append(aa)
    agg["reason"] = reason
    agg["reason_ar"] = reason_ar
    agg["recommended_action"] = action
    agg["recommended_action_ar"] = action_ar

    result = agg.sort_values("attention_score", ascending=False).head(top_n)
    cols = [
        "equipment_id", "equipment_type", "project", "attention_score",
        "downtime_rate_%", "fuel_dev_%", "maintenance_events",
        "reason", "reason_ar", "recommended_action", "recommended_action_ar",
    ]
    return {
        "tool": "compute_attention_scores",
        "requested_top_n": top_n,
        "data": result[cols].round({"attention_score": 1, "downtime_rate_%": 1, "fuel_dev_%": 1}).to_dict(orient="records"),
        "narrative_hint": f"Return exactly the top {top_n} ranked units unless fewer units exist, with reason and action.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(compute_attention_scores(3), ensure_ascii=False, indent=2))
