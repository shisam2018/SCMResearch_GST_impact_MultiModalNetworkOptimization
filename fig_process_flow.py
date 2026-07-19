import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(12.6, 4.6))
ax.set_xlim(0, 12.8)
ax.set_ylim(0, 4.6)
ax.axis("off")

steps_top = ["Data generation\n& validation", "Network &\ncost modelling", "MILP formulation\n(PuLP / CBC)",
             "Scenario solve\n(pre- vs post-GST)", "Sensitivity\n(what-if) analysis", "Managerial\ninterpretation"]

n = len(steps_top)
xs = [0.9 + i * 2.2 for i in range(n)]
y = 2.9

for i, (x, s) in enumerate(zip(xs, steps_top)):
    fc = DEEPBLUE if i < 3 else TEAL
    b = FancyBboxPatch((x - 0.95, y - 0.55), 1.9, 1.1, boxstyle="round,pad=0.02,rounding_size=0.08",
                        linewidth=1.2, edgecolor=fc, facecolor=fc, zorder=3)
    ax.add_patch(b)
    ax.text(x, y, s, ha="center", va="center", fontsize=8.7, color="white", weight="bold", zorder=4, linespacing=1.25)
    ax.text(x - 0.95, y + 0.85, f"Step {i+1}", fontsize=8.3, color=SLATE, style="italic")
    if i < n - 1:
        a = FancyArrowPatch((x + 0.98, y), (xs[i+1] - 0.98, y), arrowstyle="-|>",
                             mutation_scale=14, linewidth=1.6, color="#2b2b2b", zorder=2)
        ax.add_patch(a)

# Streamlit app annotation loop-back
ax.annotate("", xy=(xs[4], y - 0.85), xytext=(xs[2], y - 0.85),
            arrowprops=dict(arrowstyle="-|>", lw=1.3, color=RUST, connectionstyle="arc3,rad=0.25", linestyle="--"))
ax.text((xs[2]+xs[4])/2, y - 1.25, "interactive re-solve via the Streamlit dashboard\n(forced-open / forced-closed candidate locations)",
        ha="center", fontsize=8.2, color=RUST, style="italic")

ax.text(6.4, 0.5, "Reproducibility: all steps are implemented in open, citable, non-proprietary Python\n"
                   "(pandas, PuLP/CBC, Streamlit) so that any reader can re-run or re-parameterise the model.",
        ha="center", fontsize=9.0, style="italic", color="#333333")

plt.tight_layout()
plt.savefig("figures/fig_process_flow.png", bbox_inches="tight", dpi=300)
print("saved")
