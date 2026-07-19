import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(11.5, 5.6))
ax.set_xlim(0, 11.5)
ax.set_ylim(0, 5.6)
ax.axis("off")


def box(x, y, w, h, text, fc, tc="white", fs=9.3, weight="bold"):
    b = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.02,rounding_size=0.09",
                        linewidth=1.2, edgecolor=fc, facecolor=fc, zorder=3)
    ax.add_patch(b)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc, weight=weight, zorder=4, linespacing=1.3)


def arrow(p1, p2, label=None, color="#2b2b2b"):
    a = FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=15, linewidth=1.6, color=color, zorder=2)
    ax.add_patch(a)
    if label:
        ax.text((p1[0]+p2[0])/2, (p1[1]+p2[1])/2 + 0.34, label, ha="center", fontsize=8.0, color=color, style="italic")


# ---- Pre-GST row ----
y0 = 4.25
box(1.05, y0, 1.7, 0.85, "Manufacturing\nplant", DEEPBLUE)
box(3.55, y0, 1.7, 0.85, "In-state\nstockyard", DEEPBLUE)
box(6.05, y0, 1.9, 0.85, "Customer\n(same state)", DEEPBLUE)
box(9.35, y0, 2.1, 0.95, "Central sales tax (non-\ncreditable) discourages\ndirect inter-state sale", MAROON, fs=8.6)
arrow((1.9, y0), (2.7, y0), "stock transfer\n(tax-exempt)")
arrow((4.4, y0), (5.1, y0), "intra-state sale\n(VAT only)")
arrow((7.0, y0), (8.25, y0))
ax.text(0.15, y0 + 1.0, "PRE-GST", fontsize=11.5, weight="bold", color=DEEPBLUE)
ax.text(5.5, y0 + 1.0, "\u2192 incentive to hold at least one stockyard per state", fontsize=9.5, style="italic", color=SLATE)

# ---- Post-GST row ----
y1 = 1.55
box(1.05, y1, 1.7, 0.95, "Manufacturing\nplant", TEAL)
box(6.05, y1, 1.9, 0.95, "Customer\n(any state)", TEAL)
box(9.35, y1, 2.1, 0.95, "Uniform, destination-based\nGST, fully input-credited:\nstate boundary is cost-neutral", AMBER, tc="#2b2b2b", fs=8.6)
arrow((1.9, y1), (5.1, y1), "direct dispatch, or via a\nfar-larger consolidated hub")
arrow((7.0, y1), (8.25, y1))
ax.text(0.15, y1 + 0.85, "POST-GST", fontsize=11.5, weight="bold", color=TEAL)
ax.text(5.5, y1 + 0.85, "\u2192 network free to consolidate on logistics cost alone", fontsize=9.5, style="italic", color=SLATE)

plt.tight_layout()
plt.savefig("figures/fig_pre_post_gst_concept.png", bbox_inches="tight", dpi=300)
print("saved")
