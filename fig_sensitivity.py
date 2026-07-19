import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
import json
import numpy as np

with open("outputs/sensitivity_scenarios.json") as f:
    sens = json.load(f)

names = list(sens.keys())[1:]  # exclude baseline
deltas_pct = [sens[n]["delta_pct"] for n in names]
deltas_usd = [sens[n]["delta"] / 1e6 for n in names]

order = np.argsort(deltas_pct)
names = [names[i] for i in order]
deltas_pct = [deltas_pct[i] for i in order]
deltas_usd = [deltas_usd[i] for i in order]

fig, ax = plt.subplots(figsize=(10.2, 5.6))
colors = [RUST if "close" in n.lower() else AMBER for n in names]
bars = ax.barh(names, deltas_pct, color=colors, height=0.58, zorder=3)
for b, usd in zip(bars, deltas_usd):
    w = b.get_width()
    ax.annotate(f"+{w:.2f}%  (+${usd:.2f}M/yr)", (w + 0.06, b.get_y() + b.get_height()/2),
                va="center", fontsize=9, color="#2b2b2b")

ax.set_xlabel("Increase in total annual network cost relative to the model-optimised post-GST baseline (%)", fontsize=10)
ax.set_title("What-if sensitivity: cost impact of overriding the model's stockyard open/close decision", fontsize=12, pad=12)
ax.set_xlim(0, max(deltas_pct) * 1.35)
ax.grid(axis="x", color=LIGHTGRID, linewidth=0.6, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=RUST, label="Force-close a model-selected stockyard"),
                    Patch(color=AMBER, label="Force-open a model-excluded stockyard")],
          fontsize=9, loc="lower right", frameon=False)

plt.tight_layout()
plt.savefig("figures/fig_sensitivity.png", bbox_inches="tight", dpi=300)
print("saved")
