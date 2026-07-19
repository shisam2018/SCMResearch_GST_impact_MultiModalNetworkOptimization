import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(13.0, 7.6))
ax.set_xlim(0, 13.0)
ax.set_ylim(0, 7.6)
ax.axis("off")

SPINE_Y = 3.8
ax.annotate("", xy=(12.0, SPINE_Y), xytext=(1.6, SPINE_Y),
            arrowprops=dict(arrowstyle="-|>", lw=2.4, color="#2b2b2b"))
ax.add_patch(FancyBboxPatch((12.05, SPINE_Y - 0.42), 0.85, 0.84, boxstyle="round,pad=0.02,rounding_size=0.06",
                             linewidth=1.3, edgecolor=MAROON, facecolor=MAROON, zorder=4))
ax.text(12.475, SPINE_Y, "High\nlogistics\ncost per\nton", ha="center", va="center", fontsize=8.2, color="white",
        weight="bold", zorder=5, linespacing=1.15)

# Each zone appears exactly once. North & East above the spine; West & South below.
UPPER = [
    ("North zone", ["Rake availability, Delhi\u2013NCR corridor",
                     "Multiple wagon types (mixed idle-freight impact)",
                     "Diesel-price variation clause on road legs"], 4.0),
    ("East zone", ["Dominant customer concentration in one catchment",
                    "Production-plan variability at source",
                    "High inter-stockyard transfer volume"], 8.4),
]
LOWER = [
    ("West zone", ["Long average lead distance to plant",
                    "High special road-volume premium",
                    "Multiple handling legs (quality risk)"], 4.0),
    ("South zone", ["Rake availability, far-south corridor",
                     "Coastal / sea-mode under-utilisation",
                     "Customer single-sourcing from one stockyard"], 8.4),
]

BRANCH_LEN = 2.35
BOX_W, BOX_H = 1.9, 0.55


def draw_branch(label, items, x_tip, side):
    """side = +1 (above spine) or -1 (below spine)"""
    x0 = x_tip - BRANCH_LEN
    y0 = SPINE_Y + side * 2.55
    ax.plot([x0, x_tip], [y0, SPINE_Y], color=SLATE, linewidth=2.2, zorder=2)
    box_y = y0 + side * (BOX_H / 2 + 0.06)
    fc = DEEPBLUE if side == 1 else TEAL
    ax.add_patch(FancyBboxPatch((x0 - BOX_W / 2, box_y - BOX_H / 2), BOX_W, BOX_H,
                                 boxstyle="round,pad=0.02,rounding_size=0.06",
                                 linewidth=1.1, edgecolor=fc, facecolor=fc, zorder=4))
    ax.text(x0, box_y, label, ha="center", va="center", fontsize=9.2, color="white", weight="bold", zorder=5)

    n = len(items)
    for i, item in enumerate(items):
        t = 0.22 + i * (0.62 / max(n - 1, 1))
        px = x0 + t * (x_tip - x0)
        py = y0 + t * (SPINE_Y - y0)
        leaf_dx, leaf_dy = -0.85, side * 0.55
        ax.plot([px, px + leaf_dx], [py, py + leaf_dy], color="#B9B4A6", linewidth=1.0, zorder=1)
        ax.text(px + leaf_dx - 0.08, py + leaf_dy, item, ha="right", va="center",
                fontsize=7.9, color="#2b2b2b", linespacing=1.15)


for label, items, x in UPPER:
    draw_branch(label, items, x, +1)
for label, items, x in LOWER:
    draw_branch(label, items, x, -1)

ax.set_title("Root-cause (Ishikawa) analysis of regional logistics-cost drivers motivating the network re-optimisation",
              fontsize=12.2, pad=10)

plt.tight_layout()
plt.savefig("figures/fig_ishikawa.png", bbox_inches="tight", dpi=300)
print("saved")
