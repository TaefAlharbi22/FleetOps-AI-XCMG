"""
FleetOps AI - Synthetic Fleet Data Generator
=============================================
يولّد بيانات تشغيل واقعية لأسطول معدات إنشاء (حفارات، لوادر، شاحنات قلابة، جرافات...)
على مدى 90 يومًا، مع أنماط ومشاكل مقصودة حتى يستطيع الـ AI Agent اكتشافها لاحقًا:
  - معدات معيّنة عندها Downtime مرتفع بسبب أعطال متكررة
  - معدة واحدة عندها ارتفاع مفاجئ في استهلاك الوقود (anomaly) في آخر الفترة
  - مشروع واحد يعاني من انخفاض تدريجي في معدل الاستخدام (Utilization)
  - علاقة منطقية بين نوع المعدة واستهلاك الوقود وساعات الصيانة
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ---------------------------------------------------------------
# 1) تعريف الأسطول (Equipment Master Data)
# ---------------------------------------------------------------
EQUIPMENT_TYPES = {
    "Excavator": {"fuel_base": 18, "hours_base": 8.5, "maint_interval": 250},
    "Wheel Loader": {"fuel_base": 14, "hours_base": 8.0, "maint_interval": 250},
    "Dump Truck": {"fuel_base": 22, "hours_base": 9.0, "maint_interval": 300},
    "Bulldozer": {"fuel_base": 20, "hours_base": 7.5, "maint_interval": 200},
    "Crane": {"fuel_base": 16, "hours_base": 6.5, "maint_interval": 300},
    "Grader": {"fuel_base": 15, "hours_base": 7.0, "maint_interval": 250},
}

PROJECTS = ["Riyadh Metro Ext.", "Jeddah Corniche", "NEOM Site A", "Dammam Port Rd", "Makkah Housing"]

N_EQUIPMENT = 30
START_DATE = datetime(2026, 6, 1)
N_DAYS = 90

equipment_list = []
rng = np.random.default_rng(42)

for i in range(1, N_EQUIPMENT + 1):
    eq_type = rng.choice(list(EQUIPMENT_TYPES.keys()))
    equipment_list.append({
        "equipment_id": f"EQ-{i:03d}",
        "equipment_type": eq_type,
        "project": rng.choice(PROJECTS),
        "purchase_year": int(rng.integers(2016, 2024)),
    })

equipment_df = pd.DataFrame(equipment_list)

# اختيار بعض المعدات لتكون "مشكلة" بشكل مقصود (لأغراض الديمو والـ Insights)
high_downtime_units = rng.choice(equipment_df["equipment_id"], size=3, replace=False)
fuel_anomaly_unit = rng.choice(
    [e for e in equipment_df["equipment_id"] if e not in high_downtime_units], size=1
)[0]
underused_project = "Dammam Port Rd"  # مشروع يعاني من تراجع تدريجي في الاستخدام

# ---------------------------------------------------------------
# 2) توليد السجلات اليومية (Daily Operations Log)
# ---------------------------------------------------------------
records = []
dates = [START_DATE + timedelta(days=d) for d in range(N_DAYS)]

for _, eq in equipment_df.iterrows():
    specs = EQUIPMENT_TYPES[eq["equipment_type"]]
    is_high_downtime = eq["equipment_id"] in high_downtime_units
    is_fuel_anomaly = eq["equipment_id"] == fuel_anomaly_unit
    hours_since_maint = int(rng.integers(0, 100))

    for day_idx, date in enumerate(dates):
        # عطلة أسبوعية (جمعة) تقلل الاستخدام
        is_friday = date.weekday() == 4
        weekend_factor = 0.15 if is_friday else 1.0

        # اتجاه تراجع تدريجي للاستخدام في مشروع معيّن (مشكلة يكتشفها الـAI)
        project_trend = 1.0
        if eq["project"] == underused_project:
            project_trend = max(0.4, 1.0 - (day_idx / N_DAYS) * 0.6)

        # ساعات التشغيل
        operating_hours = max(
            0,
            rng.normal(specs["hours_base"], 1.2) * weekend_factor * project_trend
        )

        # التوقف (Downtime) - أعلى للمعدات المحددة كـ "مشكلة"
        base_downtime_prob = 0.35 if is_high_downtime else 0.08
        breakdown_today = rng.random() < base_downtime_prob
        downtime_hours = 0.0
        if breakdown_today:
            downtime_hours = rng.uniform(1.5, 6.0) if is_high_downtime else rng.uniform(0.5, 2.5)
            operating_hours = max(0, operating_hours - downtime_hours)

        # استهلاك الوقود (يرتبط بساعات التشغيل + نوع المعدة)
        fuel_consumption = operating_hours * specs["fuel_base"] * rng.normal(1.0, 0.07)
        # anomaly: ارتفاع مفاجئ في الوقود بآخر 20 يوم لمعدة واحدة (مؤشر على مشكلة ميكانيكية/تسريب)
        if is_fuel_anomaly and day_idx > (N_DAYS - 20):
            fuel_consumption *= rng.uniform(1.35, 1.6)

        hours_since_maint += operating_hours
        maintenance_flag = 0
        if hours_since_maint >= specs["maint_interval"]:
            maintenance_flag = 1
            hours_since_maint = 0
            downtime_hours += rng.uniform(2, 5)  # وقت توقف إضافي بسبب الصيانة

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "equipment_id": eq["equipment_id"],
            "equipment_type": eq["equipment_type"],
            "project": eq["project"],
            "operating_hours": round(operating_hours, 2),
            "downtime_hours": round(downtime_hours, 2),
            "fuel_consumption_l": round(max(fuel_consumption, 0), 2),
            "maintenance_flag": maintenance_flag,
        })

daily_df = pd.DataFrame(records)

# ---------------------------------------------------------------
# 3) الحفظ
# ---------------------------------------------------------------
equipment_df.to_csv("data/equipment_master.csv", index=False)
daily_df.to_csv("data/fleet_daily_logs.csv", index=False)

print("✅ equipment_master.csv:", equipment_df.shape)
print("✅ fleet_daily_logs.csv:", daily_df.shape)
print("\nمعدات ذات Downtime مرتفع (مقصودة للديمو):", list(high_downtime_units))
print("معدة فيها Anomaly في استهلاك الوقود:", fuel_anomaly_unit)
print("مشروع فيه تراجع تدريجي في الاستخدام:", underused_project)
