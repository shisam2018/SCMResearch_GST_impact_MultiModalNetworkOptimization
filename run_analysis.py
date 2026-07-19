"""
run_analysis.py
-----------------
Runs the pre-GST and post-GST network-optimisation scenarios end to end,
saves all KPI tables, flow tables, and the underlying master dataset to
/outputs, for use in both the manuscript and the Streamlit application.
"""
import json
import pandas as pd
from data_generator import build_dataset, TAX_ASSUMPTIONS
from milp_model import build_and_solve

OUT = "outputs"


def main():
    data = build_dataset()

    for name, df in data.items():
        df.to_csv(f"{OUT}/data_{name}.csv", index=False)

    results = {}
    for scenario in ["pre_gst", "post_gst"]:
        res = build_and_solve(data, scenario=scenario, time_limit=120)
        results[scenario] = res
        res["x"].to_csv(f"{OUT}/flows_plant_stockyard_{scenario}.csv", index=False)
        res["z"].to_csv(f"{OUT}/flows_stockyard_customer_{scenario}.csv", index=False)
        res["q"].to_csv(f"{OUT}/flows_direct_{scenario}.csv", index=False)

    kpi_rows = []
    for scenario in ["pre_gst", "post_gst"]:
        k = results[scenario]["kpi"]
        kpi_rows.append({kk: vv for kk, vv in k.items() if kk != "stockyards_open"})
    kpi_df = pd.DataFrame(kpi_rows)
    kpi_df.to_csv(f"{OUT}/kpi_comparison.csv", index=False)
    print(kpi_df.T)

    # opened stockyard lists + tiers
    sy = data["stockyards"].set_index("stockyard")
    open_compare = []
    all_sy = list(sy.index)
    pre_open = set(results["pre_gst"]["opened"])
    post_open = set(results["post_gst"]["opened"])
    for k in all_sy:
        open_compare.append(dict(
            stockyard=k, state=sy.loc[k, "state"], tier=sy.loc[k, "tier"],
            open_pre_gst=k in pre_open, open_post_gst=k in post_open,
            status=("Retained" if (k in pre_open and k in post_open) else
                     "Closed post-GST" if (k in pre_open and k not in post_open) else
                     "Newly opened post-GST" if (k not in pre_open and k in post_open) else
                     "Never opened"),
        ))
    open_df = pd.DataFrame(open_compare)
    open_df.to_csv(f"{OUT}/stockyard_status_comparison.csv", index=False)
    print(open_df["status"].value_counts())

    with open(f"{OUT}/tax_assumptions.json", "w") as f:
        json.dump(TAX_ASSUMPTIONS, f, indent=2)

    savings = {
        "total_cost_saving_usd": results["pre_gst"]["kpi"]["total_cost_usd"] - results["post_gst"]["kpi"]["total_cost_usd"],
        "total_cost_saving_pct": 100 * (results["pre_gst"]["kpi"]["total_cost_usd"] - results["post_gst"]["kpi"]["total_cost_usd"]) / results["pre_gst"]["kpi"]["total_cost_usd"],
        "cost_per_ton_pre": results["pre_gst"]["kpi"]["cost_per_ton_usd"],
        "cost_per_ton_post": results["post_gst"]["kpi"]["cost_per_ton_usd"],
        "stockyards_pre": results["pre_gst"]["kpi"]["n_stockyards_open"],
        "stockyards_post": results["post_gst"]["kpi"]["n_stockyards_open"],
        "direct_pct_pre": results["pre_gst"]["kpi"]["direct_shipment_pct"],
        "direct_pct_post": results["post_gst"]["kpi"]["direct_shipment_pct"],
    }
    with open(f"{OUT}/savings_summary.json", "w") as f:
        json.dump(savings, f, indent=2, default=float)
    print("\nSAVINGS SUMMARY:")
    for k, v in savings.items():
        print(f"  {k}: {v:,.2f}" if isinstance(v, float) else f"  {k}: {v}")

    return data, results


if __name__ == "__main__":
    main()
