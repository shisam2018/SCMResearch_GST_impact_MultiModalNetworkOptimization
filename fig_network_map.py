import sys
sys.path.insert(0, "/home/claude/steel_model")
from style import *
import geopandas as gpd
import pandas as pd
import json

gdf = gpd.read_file("geo/india_states_simplified.geojson")

plants = pd.read_csv("outputs/data_plants.csv")
stockyards = pd.read_csv("outputs/data_stockyards.csv")
customers = pd.read_csv("outputs/data_customers.csv")

with open("outputs/savings_summary.json") as f:
    savings = json.load(f)

status_df = pd.read_csv("outputs/stockyard_status_comparison.csv")


def draw_panel(ax, scenario_col, title, open_color):
    gdf.plot(ax=ax, color=MAPFILL, edgecolor=MAPLINE, linewidth=0.5, zorder=1)
    # customers (small grey dots)
    ax.scatter(customers["lon"], customers["lat"], s=10, color="#BFBFBF", zorder=2,
               label="Customer zone", edgecolor="none")
    # stockyards: open vs closed
    open_mask = status_df[scenario_col]
    open_sy = status_df[open_mask].merge(stockyards, on="stockyard")
    closed_sy = status_df[~open_mask].merge(stockyards, on="stockyard")
    ax.scatter(closed_sy["lon"], closed_sy["lat"], s=34, color="white",
               edgecolor="#999999", linewidth=1.0, zorder=3, marker="s")
    ax.scatter(open_sy["lon"], open_sy["lat"], s=95, color=open_color,
               edgecolor="#2b2b2b", linewidth=0.8, zorder=4, marker="s", label="Open stockyard")
    # plants
    ax.scatter(plants["lon"], plants["lat"], s=170, color=MAROON, edgecolor="#2b2b2b",
               linewidth=0.9, zorder=5, marker="*", label="Manufacturing plant")

    # flow lines: plant -> open stockyard
    flows = pd.read_csv(f"outputs/flows_plant_stockyard_{'pre_gst' if 'pre' in scenario_col else 'post_gst'}.csv")
    flow_agg = flows.groupby(["plant", "stockyard"])["qty_kt"].sum().reset_index()
    pmap = plants.set_index("plant")
    smap = stockyards.set_index("stockyard")
    for _, r in flow_agg.iterrows():
        lw = 0.3 + 2.6 * (r["qty_kt"] / flow_agg["qty_kt"].max())
        ax.plot([pmap.loc[r["plant"], "lon"], smap.loc[r["stockyard"], "lon"]],
                [pmap.loc[r["plant"], "lat"], smap.loc[r["stockyard"], "lat"]],
                color=DEEPBLUE, alpha=0.45, linewidth=lw, zorder=2.5)

    # direct plant->customer flows
    dflows = pd.read_csv(f"outputs/flows_direct_{'pre_gst' if 'pre' in scenario_col else 'post_gst'}.csv")
    if len(dflows):
        dflow_agg = dflows.groupby(["plant", "customer"])["qty_kt"].sum().reset_index()
        cmap = customers.set_index("customer")
        for _, r in dflow_agg.iterrows():
            lw = 0.25 + 1.8 * (r["qty_kt"] / dflow_agg["qty_kt"].max())
            ax.plot([pmap.loc[r["plant"], "lon"], cmap.loc[r["customer"], "lon"]],
                    [pmap.loc[r["plant"], "lat"], cmap.loc[r["customer"], "lat"]],
                    color=RUST, alpha=0.5, linewidth=lw, zorder=2.6, linestyle="--")

    ax.set_xlim(67, 98)
    ax.set_ylim(6, 36)
    ax.axis("off")
    ax.set_title(title, fontsize=12.5, pad=8)


fig, axes = plt.subplots(1, 2, figsize=(13.5, 8.3))
draw_panel(axes[0], "open_pre_gst", f"(a) Pre-GST network  \u2013  {savings['stockyards_pre']} stockyards open, "
                                     f"{savings['direct_pct_pre']:.0f}% direct dispatch", RUST)
draw_panel(axes[1], "open_post_gst", f"(b) Post-GST network  \u2013  {savings['stockyards_post']} stockyards open, "
                                      f"{savings['direct_pct_post']:.0f}% direct dispatch", TEAL)

from matplotlib.lines import Line2D
legend_elems = [
    Line2D([0], [0], marker="*", color="w", markerfacecolor=MAROON, markeredgecolor="#2b2b2b", markersize=15, label="Manufacturing plant"),
    Line2D([0], [0], marker="s", color="w", markerfacecolor=TEAL, markeredgecolor="#2b2b2b", markersize=10, label="Open stockyard"),
    Line2D([0], [0], marker="s", color="w", markerfacecolor="white", markeredgecolor="#999999", markersize=8, label="Candidate stockyard (closed)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#BFBFBF", markersize=6, label="Customer zone"),
    Line2D([0], [0], color=DEEPBLUE, alpha=0.6, linewidth=2, label="1st-leg flow (plant\u2192stockyard)"),
    Line2D([0], [0], color=RUST, alpha=0.6, linewidth=1.6, linestyle="--", label="Direct flow (plant\u2192customer)"),
]
fig.legend(handles=legend_elems, loc="lower center", ncol=3, fontsize=9.3, frameon=False, bbox_to_anchor=(0.5, -0.02))
plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig("figures/fig_network_map.png", bbox_inches="tight", dpi=300)
print("saved fig_network_map.png")
