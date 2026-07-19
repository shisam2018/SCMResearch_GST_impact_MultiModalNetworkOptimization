import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
import pandas as pd
import geopandas as gpd
import json
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch

kpi = pd.read_csv("outputs/kpi_comparison.csv")
with open("outputs/savings_summary.json") as f:
    sav = json.load(f)
post = kpi[kpi["scenario"] == "post_gst"].iloc[0]
pre = kpi[kpi["scenario"] == "pre_gst"].iloc[0]

gdf = gpd.read_file("geo/india_states_simplified.geojson")
plants = pd.read_csv("outputs/data_plants.csv")
stockyards = pd.read_csv("outputs/data_stockyards.csv")
status = pd.read_csv("outputs/stockyard_status_comparison.csv")

fig = plt.figure(figsize=(13.5, 8.6))
fig.patch.set_facecolor("#EEF1F4")

gs = gridspec.GridSpec(4, 4, figure=fig, height_ratios=[0.55, 0.85, 1.9, 0.15], hspace=0.55, wspace=0.35)

# ---- Title bar ----
ax_title = fig.add_subplot(gs[0, :])
ax_title.axis("off")
ax_title.add_patch(FancyBboxPatch((0, 0), 1, 1, transform=ax_title.transAxes, boxstyle="round,pad=0.0,rounding_size=0.0",
                                    facecolor=NAVY, edgecolor="none", zorder=1))
ax_title.text(0.018, 0.5, "\u2699  Multimodal Steel Distribution Network Optimiser", transform=ax_title.transAxes,
              fontsize=15, color="white", weight="bold", va="center")
ax_title.text(0.982, 0.5, "Scenario:  \u25CF Post-GST", transform=ax_title.transAxes,
              fontsize=10.5, color="#CFE3EA", va="center", ha="right", style="italic")

# ---- KPI cards ----
kpi_defs = [
    ("Total annual cost", f"${post['total_cost_usd']/1e6:.1f} M", f"\u2193 {sav['total_cost_saving_pct']:.1f}% vs pre-GST", TEAL),
    ("Cost per ton", f"${post['cost_per_ton_usd']:.2f}", f"vs ${pre['cost_per_ton_usd']:.2f} pre-GST", DEEPBLUE),
    ("Stockyards open", f"{int(post['n_stockyards_open'])}", f"vs {int(pre['n_stockyards_open'])} pre-GST", AMBER),
    ("Direct-dispatch share", f"{post['direct_shipment_pct']:.0f}%", f"vs {pre['direct_shipment_pct']:.0f}% pre-GST", RUST),
]
for i, (label, val, sub, c) in enumerate(kpi_defs):
    ax = fig.add_subplot(gs[1, i])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.03, 0.05), 0.94, 0.9, transform=ax.transAxes,
                                  boxstyle="round,pad=0.02,rounding_size=0.10",
                                  facecolor="white", edgecolor="#D8DCE1", linewidth=1.0, zorder=1))
    ax.add_patch(FancyBboxPatch((0.03, 0.05), 0.05, 0.9, transform=ax.transAxes,
                                  boxstyle="round,pad=0.0,rounding_size=0.0",
                                  facecolor=c, edgecolor="none", zorder=2))
    ax.text(0.18, 0.72, label, transform=ax.transAxes, fontsize=9.3, color="#555555", va="center")
    ax.text(0.18, 0.42, val, transform=ax.transAxes, fontsize=19, color="#1a1a1a", weight="bold", va="center")
    ax.text(0.18, 0.18, sub, transform=ax.transAxes, fontsize=8.3, color=TEAL if "\u2193" in sub else "#777777", va="center")

# ---- Map panel ----
ax_map = fig.add_subplot(gs[2, 0:2])
gdf.plot(ax=ax_map, color=MAPFILL, edgecolor=MAPLINE, linewidth=0.4, zorder=1)
ax_map.scatter(stockyards["lon"], stockyards["lat"], s=20, color="#CCCCCC", zorder=2, marker="s")
open_sy = status[status["open_post_gst"]].merge(stockyards, on="stockyard")
ax_map.scatter(open_sy["lon"], open_sy["lat"], s=70, color=TEAL, edgecolor="#2b2b2b", linewidth=0.6, zorder=3, marker="s")
ax_map.scatter(plants["lon"], plants["lat"], s=140, color=MAROON, edgecolor="#2b2b2b", linewidth=0.7, zorder=4, marker="*")
ax_map.set_xlim(67, 98); ax_map.set_ylim(6, 36)
ax_map.axis("off")
ax_map.set_title("Optimised network map", fontsize=10.5, loc="left", color="#333333")

# ---- Cost breakdown donut ----
ax_donut = fig.add_subplot(gs[2, 2])
vals = [post["freight_cost_usd"], post["handling_cost_usd"], post["fixed_cost_usd"]]
labels = ["Freight", "Handling", "Fixed"]
ax_donut.pie(vals, labels=None, colors=[DEEPBLUE, TEAL, AMBER], startangle=90,
             wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
ax_donut.legend(labels, fontsize=8, frameon=False, loc="center", bbox_to_anchor=(0.5, -0.08), ncol=3)
ax_donut.set_title("Cost composition", fontsize=10.5, loc="left", color="#333333")

# ---- Scenario toggle + sensitivity mock control panel ----
ax_ctrl = fig.add_subplot(gs[2, 3])
ax_ctrl.axis("off")
ax_ctrl.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96, transform=ax_ctrl.transAxes,
                                   boxstyle="round,pad=0.02,rounding_size=0.08",
                                   facecolor="white", edgecolor="#D8DCE1", linewidth=1.0, zorder=1))
ax_ctrl.text(0.5, 0.90, "Scenario controls", transform=ax_ctrl.transAxes, fontsize=9.6, weight="bold", ha="center")
ax_ctrl.text(0.12, 0.76, "Regulatory regime", transform=ax_ctrl.transAxes, fontsize=8.2, color="#555555")
for i, (lab, sel) in enumerate([("Pre-GST", False), ("Post-GST", True)]):
    yy = 0.66 - i*0.08
    ax_ctrl.add_patch(plt.Circle((0.14, yy), 0.018, transform=ax_ctrl.transAxes, color=TEAL if sel else "#BBBBBB", zorder=2))
    ax_ctrl.text(0.20, yy, lab, transform=ax_ctrl.transAxes, fontsize=8.3, va="center")
ax_ctrl.text(0.12, 0.45, "Force-open location", transform=ax_ctrl.transAxes, fontsize=8.2, color="#555555")
ax_ctrl.add_patch(FancyBboxPatch((0.10, 0.36), 0.8, 0.07, transform=ax_ctrl.transAxes,
                                  boxstyle="round,pad=0.01,rounding_size=0.05", facecolor="#F3F4F6", edgecolor="#CCCCCC"))
ax_ctrl.text(0.14, 0.395, "Select city\u2026", transform=ax_ctrl.transAxes, fontsize=7.8, color="#999999", va="center")
ax_ctrl.text(0.12, 0.24, "Force-close location", transform=ax_ctrl.transAxes, fontsize=8.2, color="#555555")
ax_ctrl.add_patch(FancyBboxPatch((0.10, 0.15), 0.8, 0.07, transform=ax_ctrl.transAxes,
                                  boxstyle="round,pad=0.01,rounding_size=0.05", facecolor="#F3F4F6", edgecolor="#CCCCCC"))
ax_ctrl.text(0.14, 0.185, "Select city\u2026", transform=ax_ctrl.transAxes, fontsize=7.8, color="#999999", va="center")
ax_ctrl.add_patch(FancyBboxPatch((0.10, 0.02), 0.8, 0.09, transform=ax_ctrl.transAxes,
                                  boxstyle="round,pad=0.01,rounding_size=0.06", facecolor=DEEPBLUE, edgecolor="none"))
ax_ctrl.text(0.5, 0.065, "\u25B6 Re-solve model", transform=ax_ctrl.transAxes, fontsize=8.6, color="white",
             weight="bold", ha="center", va="center")

ax_foot = fig.add_subplot(gs[3, :])
ax_foot.axis("off")
ax_foot.text(0.5, 0.5, "Representative view of the interactive Streamlit application described in Section 4 "
                       "(built with pandas, PuLP/CBC and Streamlit; live values shown are illustrative of a single run)",
             transform=ax_foot.transAxes, ha="center", fontsize=8.3, style="italic", color="#666666")

plt.savefig("figures/fig_dashboard_mockup.png", bbox_inches="tight", dpi=300, facecolor=fig.get_facecolor())
print("saved")
