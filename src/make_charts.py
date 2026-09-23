import sys
sys.path.insert(0, "src")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import tools

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
NAVY = "#1a3a5c"
TEAL = "#2a9d8f"
ORANGE = "#e76f51"
GREY = "#6c757d"

# --- Chart 1: Top Downtime Equipment ---
top = pd.DataFrame(tools.get_top_downtime_equipment(8)["data"])
fig, ax = plt.subplots(figsize=(7.2, 4))
colors = [ORANGE if v >= 15 else TEAL for v in top["downtime_rate_%"]]
bars = ax.bar(top["equipment_id"], top["downtime_rate_%"], color=colors)
ax.set_ylabel("Downtime Rate (%)")
ax.set_title("Top 8 Equipment by Downtime Rate", fontsize=13, fontweight="bold", color=NAVY)
for b, v in zip(bars, top["downtime_rate_%"]):
    ax.text(b.get_x() + b.get_width()/2, v + 0.3, f"{v}%", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig("reports/chart_top_downtime.png", dpi=160)
plt.close()

# --- Chart 2: Utilization by Project ---
report = tools.generate_fleet_report()
by_proj = pd.DataFrame(report["by_project"]).sort_values("utilization_%")
fig, ax = plt.subplots(figsize=(7.2, 4))
bars = ax.barh(by_proj["project"], by_proj["utilization_%"], color=NAVY)
ax.set_xlabel("Utilization Rate (%)")
ax.set_title("Fleet Utilization Rate by Project", fontsize=13, fontweight="bold", color=NAVY)
ax.set_xlim(0, 100)
for b, v in zip(bars, by_proj["utilization_%"]):
    ax.text(v + 1, b.get_y() + b.get_height()/2, f"{v}%", va="center", fontsize=9)
plt.tight_layout()
plt.savefig("reports/chart_utilization_by_project.png", dpi=160)
plt.close()

# --- Chart 3: Fuel Anomaly ---
fuel = tools.analyze_fuel_consumption()["data"]
if fuel:
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    for i, r in enumerate(fuel):
        ax.plot([0, 1], [r["baseline_l_per_hr"], r["recent_l_per_hr"]], marker="o",
                color=ORANGE, linewidth=2.5, markersize=8)
        ax.annotate(f"{r['equipment_id']}\n+{r['change_%']}%",
                    (1, r["recent_l_per_hr"]), textcoords="offset points", xytext=(10, 0), fontsize=9)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Baseline (first half)", "Recent (last 14 days)"])
    ax.set_ylabel("Fuel Consumption (L/hr)")
    ax.set_title("Fuel Consumption Anomaly Detection", fontsize=13, fontweight="bold", color=NAVY)
    ax.set_xlim(-0.2, 1.4)
    plt.tight_layout()
    plt.savefig("reports/chart_fuel_anomaly.png", dpi=160)
    plt.close()

print("✅ تم توليد الرسومات في مجلد reports/")
