import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
import pandas as pd
import numpy as np

status = pd.read_csv("outputs/stockyard_status_comparison.csv")

# ---------------- Figure: stockyard status by region ----------------
region_map = {
    "Delhi": "North", "Chandigarh": "North", "Jaipur": "North", "Lucknow": "North",
    "Mumbai": "West", "Ahmedabad": "West", "Pune": "West", "Indore": "West",
    "Kolkata": "East", "Patna": "East", "Bhubaneswar": "East", "Guwahati": "East",
    "Chennai": "South", "Bangalore": "South", "Hyderabad": "South", "Coimbatore": "South", "Vijayawada": "South",
    "Nagpur": "Central", "Bhopal": "Central", "Raipur": "Central",
}
status["region"] = status["stockyard"].map(region_map)

order = ["Retained", "Closed post-GST", "Never opened"]
colors = {"Retained": TEAL, "Closed post-GST": RUST, "Never opened": "#C9C4B8"}

fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.4), gridspec_kw={"width_ratios": [1.05, 1]})

ax = axes[0]
tab = pd.crosstab(status["region"], status["status"])
for s in order:
    if s not in tab.columns:
        tab[s] = 0
tab = tab[order]
tab = tab.loc[["North", "West", "Central", "East", "South"]]
bottom = np.zeros(len(tab))
for s in order:
    ax.bar(tab.index, tab[s], bottom=bottom, color=colors[s], label=s, width=0.58, zorder=3)
    bottom += tab[s].values
ax.set_ylabel("Number of candidate stockyard locations", fontsize=10.5)
ax.set_title("(a) Stockyard status by macro-region", fontsize=11.8)
ax.legend(fontsize=9, frameon=False, loc="upper right")
ax.grid(axis="y", color=LIGHTGRID, linewidth=0.6, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

ax = axes[1]
counts = status["status"].value_counts().reindex(order)
wedges, texts, autotexts = ax.pie(
    counts.values, labels=None, colors=[colors[s] for s in order], startangle=90,
    autopct=lambda p: f"{p:.0f}%\n({int(round(p*sum(counts.values)/100))})",
    pctdistance=0.72, wedgeprops=dict(edgecolor="white", linewidth=1.5),
    textprops=dict(fontsize=9.5, color="white", weight="bold"))
ax.legend(wedges, order, fontsize=9.3, frameon=False, loc="center left", bbox_to_anchor=(0.95, 0.5))
ax.set_title("(b) Overall disposition of the 20\ncandidate stockyard locations", fontsize=11.8)

plt.tight_layout()
plt.savefig("figures/fig_stockyard_status.png", bbox_inches="tight", dpi=300)
print("saved fig_stockyard_status.png")
