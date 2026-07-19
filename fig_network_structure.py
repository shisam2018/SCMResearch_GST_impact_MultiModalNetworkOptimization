import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(12.2, 5.6))
ax.set_xlim(0, 12.6)
ax.set_ylim(0, 5.8)
ax.axis("off")


def box(x, y, w, h, text, fc, tc="white", fs=9.0, weight="bold", ec=None):
    ec = ec or fc
    b = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.02,rounding_size=0.09",
                        linewidth=1.3, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(b)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, weight=weight, zorder=4, linespacing=1.3)


def arrow(p1, p2, color="#2b2b2b", lw=1.5, ls="-", rad=0.0):
    a = FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13, linewidth=lw, color=color,
                         connectionstyle=f"arc3,rad={rad}", zorder=2, linestyle=ls)
    ax.add_patch(a)


plant = (1.1, 3.6); box(*plant, 1.9, 1.05, "Manufacturing\nplants\n(2)", DEEPBLUE)
port = (4.0, 5.05); box(*port, 1.9, 0.95, "Ports\n(coastal)", DEEPBLUE)
sy = (4.0, 3.6); box(*sy, 1.9, 0.95, "Candidate\nstockyards\n(1st echelon)", DEEPBLUE)
direct = (4.0, 2.1); box(*direct, 1.9, 0.95, "Direct road/sea\nlane (\u2264 700 km or\ncoastal)", DEEPBLUE, fs=8.4)

cust = (7.3, 3.6); box(*cust, 2.0, 1.4, "Customer\nzones\n(2nd echelon)", TEAL)

arrow((2.05, plant[1]+0.35), (3.05, port[1]-0.15), rad=0.05)
arrow((2.05, plant[1]), (3.05, sy[1]))
arrow((2.05, plant[1]-0.35), (3.05, direct[1]+0.15), rad=-0.05)
arrow((port[0]+0.95, port[1]), (cust[0]-0.35, cust[1]+0.62), rad=-0.18)
arrow((sy[0]+0.95, sy[1]), (cust[0]-1.0, cust[1]))
arrow((direct[0]+0.95, direct[1]), (cust[0]-0.35, cust[1]-0.62), rad=0.18)

# annotations of transport modes
ax.text(2.55, plant[1]+0.62, "Rail / Sea", fontsize=8, color=SLATE, style="italic")
ax.text(2.55, plant[1]+0.13, "Rail / Road", fontsize=8, color=SLATE, style="italic")
ax.text(2.55, plant[1]-0.58, "Road / Sea", fontsize=8, color=SLATE, style="italic")
ax.text(5.55, sy[1]+0.28, "Road (last mile)", fontsize=8, color=SLATE, style="italic")

# right-side annotation box: model decisions
box(10.5, 4.3, 3.6, 1.5, "DECISIONS\n\u2022 Open / close each\n  candidate stockyard (y)\n\u2022 Route & mode per lane\n  (x, z, q)", "#2b2b2b", fs=8.7)
box(10.5, 2.35, 3.6, 1.6, "REGULATORY SWITCH\n\u2022 Pre-GST: cross-state\n  sale penalty applied\n\u2022 Post-GST: penalty\n  removed (tax-neutral)", MAROON, fs=8.7)
arrow((8.35, 3.9), (8.7, 4.15), rad=0.15)
arrow((8.35, 3.3), (8.7, 2.9), rad=-0.15)

ax.text(6.3, 0.45, "Objective: minimise total annual cost = freight + handling + fixed stockyard cost + (pre-GST only) tax friction,\nsubject to plant capacity, stockyard throughput, minimum economic volume, demand satisfaction and flow-balance constraints.",
        ha="center", fontsize=9.2, style="italic", color="#333333")

plt.tight_layout()
plt.savefig("figures/fig_network_structure.png", bbox_inches="tight", dpi=300)
print("saved")
