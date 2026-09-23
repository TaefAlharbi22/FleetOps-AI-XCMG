"""
FleetOps AI - KPI Calculation
=============================
يحسب مؤشرات الأداء الرئيسية لكل معدة ومشروع:
  - Utilization Rate = operating_hours / (operating_hours + downtime_hours)
  - Downtime Rate
  - Fuel Efficiency = fuel_consumption_l / operating_hours (لتر/ساعة)
  - Maintenance Frequency
"""

import pandas as pd

daily = pd.read_csv("data/fleet_daily_logs.csv")
equip = pd.read_csv("data/equipment_master.csv")

df = daily.merge(equip, on=["equipment_id", "equipment_type", "project"])

# --- KPIs لكل معدة (كامل الفترة) ---
kpi = df.groupby(["equipment_id", "equipment_type", "project"]).agg(
    total_operating_hours=("operating_hours", "sum"),
    total_downtime_hours=("downtime_hours", "sum"),
    total_fuel_l=("fuel_consumption_l", "sum"),
    maintenance_events=("maintenance_flag", "sum"),
    days_logged=("date", "count"),
).reset_index()

kpi["utilization_rate_%"] = (
    kpi["total_operating_hours"] / (kpi["total_operating_hours"] + kpi["total_downtime_hours"]) * 100
).round(1)
kpi["downtime_rate_%"] = (100 - kpi["utilization_rate_%"]).round(1)
kpi["fuel_efficiency_l_per_hr"] = (kpi["total_fuel_l"] / kpi["total_operating_hours"]).round(2)

kpi = kpi.sort_values("downtime_rate_%", ascending=False)
kpi.to_csv("data/equipment_kpis.csv", index=False)

print("=== أعلى 5 معدات من حيث Downtime ===")
print(kpi[["equipment_id", "equipment_type", "project", "downtime_rate_%", "utilization_rate_%"]].head(5).to_string(index=False))

print("\n=== أعلى 5 معدات من حيث استهلاك الوقود لكل ساعة (Fuel Efficiency) ===")
print(kpi.sort_values("fuel_efficiency_l_per_hr", ascending=False)[
    ["equipment_id", "equipment_type", "fuel_efficiency_l_per_hr"]
].head(5).to_string(index=False))

# --- اتجاه الاستخدام الأسبوعي لكل مشروع (لاكتشاف التراجع التدريجي) ---
df["date"] = pd.to_datetime(df["date"])
df["week"] = df["date"].dt.isocalendar().week
weekly_util = df.groupby(["project", "week"]).apply(
    lambda x: x["operating_hours"].sum() / (x["operating_hours"].sum() + x["downtime_hours"].sum()) * 100
).reset_index(name="utilization_%")
weekly_util.to_csv("data/weekly_utilization_by_project.csv", index=False)

print("\n=== متوسط الاستخدام الأسبوعي حسب المشروع (أول وآخر 3 أسابيع) ===")
for proj in weekly_util["project"].unique():
    sub = weekly_util[weekly_util["project"] == proj].sort_values("week")
    first3 = sub["utilization_%"].head(3).mean()
    last3 = sub["utilization_%"].tail(3).mean()
    trend = "⬇️ تراجع" if last3 < first3 - 5 else "➡️ مستقر"
    print(f"{proj:20s} | أول 3 أسابيع: {first3:5.1f}% | آخر 3 أسابيع: {last3:5.1f}% | {trend}")
