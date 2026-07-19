import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
import pandas as pd
import numpy as np
import json

kpi = pd.read_csv("outputs/kpi_comparison.csv")
with open("outputs/savings_summary.json") as f:
    sav = json.load(f)

pre = kpi[kpi["scenario"] == "pre_gst"].iloc[0]
post = kpi[kpi["scenario"] == "post_gst"].iloc[0]

# ---------------- Figure: Cost breakdown grouped bar + total cost drop ----------------
fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.6))

ax = axes[0]
cats = ["Freight", "Handling", "Fixed\n(stockyard)", "Tax\nfriction"]
pre_vals = [pre["freight_cost_usd"], pre["handling_cost_usd"], pre["fixed_cost_usd"], pre["tax_cost_usd"]]
post_vals = [post["freight_cost_usd"], post["handling_cost_usd"], post["fixed_cost_usd"], post["tax_cost_usd"]]
pre_vals = [v / 1e6 for v in pre_vals]
post_vals = [v / 1e6 for v in post_vals]
x = np.arange(len(cats))
w = 0.35
b1 = ax.bar(x - w/2, pre_vals, width=w, color=RUST, label="Pre-GST", zorder=3)
b2 = ax.bar(x + w/2, post_vals, width=w, color=TEAL, label="Post-GST", zorder=3)
for b in list(b1) + list(b2):
    h = b.get_height()
    ax.annotate(f"{h:.1f}", (b.get_x() + b.get_width()/2, h), textcoords="offset points",
                xytext=(0, 3), ha="center", fontsize=8.5)
ax.set_xticks(x)
ax.set_xticklabels(cats, fontsize=9.5)
ax.set_ylabel("Annual cost (USD million)", fontsize=10.5)
ax.set_title("(a) Cost-component comparison", fontsize=11.5)
ax.legend(fontsize=9.5, frameon=False)
ax.grid(axis="y", color=LIGHTGRID, linewidth=0.6, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

ax = axes[1]
labels = ["Pre-GST\ntotal cost", "Freight\n\u0394", "Handling\n\u0394", "Fixed-cost\n\u0394", "Tax\n\u0394", "Post-GST\ntotal cost"]
freight_d = post["freight_cost_usd"] - pre["freight_cost_usd"]
handling_d = post["handling_cost_usd"] - pre["handling_cost_usd"]
fixed_d = post["fixed_cost_usd"] - pre["fixed_cost_usd"]
tax_d = post["tax_cost_usd"] - pre["tax_cost_usd"]
vals = [pre["total_cost_usd"]/1e6, freight_d/1e6, handling_d/1e6, fixed_d/1e6, tax_d/1e6, post["total_cost_usd"]/1e6]
cum = [vals[0]]
for v in vals[1:-1]:
    cum.append(cum[-1] + v)
cum.append(0)

bottoms = [0, min(cum[0], cum[0]+vals[1]), 0, 0, 0, 0]
running = vals[0]
colors_wf = [NAVY]
bar_bottoms = [0]
bar_heights = [vals[0]]
for v in vals[1:-1]:
    if v >= 0:
        bar_bottoms.append(running)
        bar_heights.append(v)
    else:
        bar_bottoms.append(running + v)
        bar_heights.append(-v)
    running += v
    colors_wf.append(TEAL if v < 0 else RUST)
bar_bottoms.append(0)
bar_heights.append(running)
colors_wf.append(DEEPBLUE)

ax.bar(range(6), bar_heights, bottom=bar_bottoms, color=colors_wf, width=0.62, zorder=3,
       edgecolor="#2b2b2b", linewidth=0.5)
delta_labels = [f"{vals[0]:.1f}"] + [f"{v:+.1f}" for v in vals[1:-1]] + [f"{vals[-1]:.1f}"]
for i, (bb, bh, lbl) in enumerate(zip(bar_bottoms, bar_heights, delta_labels)):
    ax.annotate(lbl, (i, bb + bh + 0.5), ha="center", fontsize=8.5)
ax.set_xticks(range(6))
ax.set_xticklabels(labels, fontsize=8.6)
ax.set_ylabel("Annual cost (USD million)", fontsize=10.5)
ax.set_title(f"(b) Bridge from pre- to post-GST total cost ({sav['total_cost_saving_pct']:.1f}% reduction)", fontsize=11.2)
ax.grid(axis="y", color=LIGHTGRID, linewidth=0.6, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig_cost_comparison.png", bbox_inches="tight", dpi=300)
print("saved fig_cost_comparison.png")
