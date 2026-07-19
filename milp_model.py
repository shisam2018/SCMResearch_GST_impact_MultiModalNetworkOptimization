"""
milp_model.py
--------------
Mixed-Integer Linear Programming (MILP) model for a two-echelon,
multi-modal steel finished-goods distribution network, solved for two
regulatory scenarios:

    * PRE-GST  : inter-state "sale" legs (stockyard->customer and any
                 direct plant->customer shipment that crosses a state
                 boundary) carry a non-creditable central-sales-tax-type
                 cost penalty, creating a structural incentive to hold a
                 stockyard in (or very near) every demand state.
    * POST-GST : the destination-based, fully input-tax-credited GST
                 regime removes that penalty, so the network is free to
                 re-optimise purely on logistics economics (freight +
                 handling + fixed cost).

Solved with the open-source CBC solver via PuLP (COIN-OR), an accessible
substitute for commercial MILP solvers, fully reproducible without a
commercial licence.
"""

import pulp
import pandas as pd
import numpy as np
from data_generator import build_dataset, freight_rate_usd, TAX_ASSUMPTIONS, PRODUCTS, MODES


def _mode_allowed(mode, coastal_src, coastal_dst):
    if mode == "Sea":
        return bool(coastal_src) and bool(coastal_dst)
    return True


def build_and_solve(data, scenario="post_gst", forced_open=None, forced_closed=None,
                     time_limit=60, msg=False):
    """
    scenario: 'pre_gst' or 'post_gst'
    forced_open / forced_closed: optional lists of stockyard names to fix y_k = 1 / 0
                                 (used for the what-if sensitivity feature in the UI)
    Returns a dict with solved variables, KPI summary, and flow tables.
    """
    plants = data["plants"].set_index("plant")
    stockyards = data["stockyards"].set_index("stockyard")
    customers = data["customers"].set_index("customer")
    dps = data["dist_plant_stockyard"]
    dsc = data["dist_stockyard_customer"]
    dpc = data["dist_plant_customer"]

    P = list(plants.index)
    K = list(stockyards.index)
    C = list(customers.index)
    L = PRODUCTS
    M = MODES

    dps_map = {(r.plant, r.stockyard): r.distance_km for r in dps.itertuples()}
    dsc_map = {(r.stockyard, r.customer): r.distance_km for r in dsc.itertuples()}
    dpc_map = {(r.plant, r.customer): r.distance_km for r in dpc.itertuples()}

    tax_rate = TAX_ASSUMPTIONS["pre_gst_cross_state_rate"] if scenario == "pre_gst" else 0.0
    unit_value = {"Flat": TAX_ASSUMPTIONS["unit_value_flat_usd_per_ton"],
                  "Long": TAX_ASSUMPTIONS["unit_value_long_usd_per_ton"]}

    # NOTE ON UNITS: flow variables (x, z, q) are denominated in kilotons (kt) for
    # readability, while freight/handling/value parameters are quoted per ton.
    # PER_KT converts a $-per-ton rate into the equivalent $-per-kt rate used
    # consistently throughout the objective function below.
    PER_KT = 1000.0

    prob = pulp.LpProblem(f"SteelNetwork_{scenario}", pulp.LpMinimize)

    # ---------------- Decision variables ----------------
    y = {k: pulp.LpVariable(f"open_{k}", cat="Binary") for k in K}

    x = {}   # plant -> stockyard (1st leg), modes Rail/Road/Sea as applicable
    for p in P:
        for k in K:
            for l in L:
                for m in M:
                    if _mode_allowed(m, True, stockyards.loc[k, "coastal"]):
                        x[p, k, l, m] = pulp.LpVariable(f"x_{p}_{k}_{l}_{m}", lowBound=0)

    z = {}   # stockyard -> customer (2nd leg, road only)
    for k in K:
        for c in C:
            for l in L:
                z[k, c, l] = pulp.LpVariable(f"z_{k}_{c}_{l}", lowBound=0)

    q = {}   # direct plant -> customer (road within an operationally realistic haul
              # distance, or sea for coastal-linked customers; customers do not have
              # their own private rail siding, unlike stockyards/ports)
    DIRECT_ROAD_MAX_KM = 700.0
    for p in P:
        for c in C:
            for l in L:
                for m in M:
                    if m == "Rail":
                        continue
                    if m == "Road" and dpc_map[p, c] > DIRECT_ROAD_MAX_KM:
                        continue
                    if _mode_allowed(m, True, customers.loc[c, "coastal_linked"]):
                        q[p, c, l, m] = pulp.LpVariable(f"q_{p}_{c}_{l}_{m}", lowBound=0)

    # ---------------- Objective ----------------
    freight_cost_terms = []
    for (p, k, l, m), var in x.items():
        rate = freight_rate_usd(dps_map[p, k], m, l) * PER_KT
        freight_cost_terms.append(rate * var)
    for (k, c, l), var in z.items():
        rate = freight_rate_usd(dsc_map[k, c], "Road", l) * PER_KT
        freight_cost_terms.append(rate * var)
    for (p, c, l, m), var in q.items():
        rate = freight_rate_usd(dpc_map[p, c], m, l) * PER_KT
        freight_cost_terms.append(rate * var)

    handling_terms = [stockyards.loc[k, "handling_cost_usd_per_ton"] * PER_KT * var
                       for (p, k, l, m), var in x.items()]

    fixed_terms = [stockyards.loc[k, "fixed_cost_usd"] * y[k] for k in K]

    tax_terms = []
    if tax_rate > 0:
        for (k, c, l), var in z.items():
            if stockyards.loc[k, "state"] != customers.loc[c, "state"]:
                tax_terms.append(tax_rate * unit_value[l] * PER_KT * var)
        for (p, c, l, m), var in q.items():
            if plants.loc[p, "state"] != customers.loc[c, "state"]:
                tax_terms.append(tax_rate * unit_value[l] * PER_KT * var)

    prob += (pulp.lpSum(freight_cost_terms) + pulp.lpSum(handling_terms)
             + pulp.lpSum(fixed_terms) + pulp.lpSum(tax_terms))

    # ---------------- Constraints ----------------
    # 1. Demand satisfaction
    for c in C:
        for l in L:
            supply_terms = [z[k, c, l] for k in K]
            supply_terms += [q[p, c, l, m] for p in P for m in M if (p, c, l, m) in q]
            prob += pulp.lpSum(supply_terms) == customers.loc[c, f"demand_{l.lower()}_kt"], f"Demand_{c}_{l}"

    # 2. Plant capacity
    for p in P:
        out_terms = [x[p, k, l, m] for k in K for l in L for m in M if (p, k, l, m) in x]
        out_terms += [q[p, c, l, m] for c in C for l in L for m in M if (p, c, l, m) in q]
        prob += pulp.lpSum(out_terms) <= plants.loc[p, "capacity_kt"], f"PlantCap_{p}"

    # 3. Stockyard throughput capacity (linked to open/close decision)
    for k in K:
        in_terms = [x[p, k, l, m] for p in P for l in L for m in M if (p, k, l, m) in x]
        prob += pulp.lpSum(in_terms) <= stockyards.loc[k, "throughput_cap_kt"] * y[k], f"ThroughputCap_{k}"

    # 4. Flow balance at each stockyard, per product
    for k in K:
        for l in L:
            inflow = pulp.lpSum(x[p, k, l, m] for p in P for m in M if (p, k, l, m) in x)
            outflow = pulp.lpSum(z[k, c, l] for c in C)
            prob += inflow == outflow, f"Balance_{k}_{l}"

    # 5. Minimum economic throughput to justify keeping a stockyard open
    min_vol = TAX_ASSUMPTIONS["min_economic_volume_kt"]
    for k in K:
        in_terms = [x[p, k, l, m] for p in P for l in L for m in M if (p, k, l, m) in x]
        prob += pulp.lpSum(in_terms) >= min_vol * y[k], f"MinVol_{k}"

    # 6. Optional forced inclusion / exclusion (sensitivity "what-if" feature)
    for k in (forced_open or []):
        if k in y:
            prob += y[k] == 1, f"ForceOpen_{k}"
    for k in (forced_closed or []):
        if k in y:
            prob += y[k] == 0, f"ForceClosed_{k}"

    # ---------------- Solve ----------------
    solver = pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit, gapRel=0.001)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    total_cost = pulp.value(prob.objective)

    opened = [k for k in K if y[k].value() and y[k].value() > 0.5]

    x_rows = [{"plant": p, "stockyard": k, "product": l, "mode": m, "qty_kt": var.value()}
              for (p, k, l, m), var in x.items() if var.value() and var.value() > 1e-6]
    z_rows = [{"stockyard": k, "customer": c, "product": l, "qty_kt": var.value()}
              for (k, c, l), var in z.items() if var.value() and var.value() > 1e-6]
    q_rows = [{"plant": p, "customer": c, "product": l, "mode": m, "qty_kt": var.value()}
              for (p, c, l, m), var in q.items() if var.value() and var.value() > 1e-6]

    freight_cost_val = sum(freight_rate_usd(dps_map[p, k], m, l) * PER_KT * var.value()
                            for (p, k, l, m), var in x.items() if var.value())
    freight_cost_val += sum(freight_rate_usd(dsc_map[k, c], "Road", l) * PER_KT * var.value()
                             for (k, c, l), var in z.items() if var.value())
    freight_cost_val += sum(freight_rate_usd(dpc_map[p, c], m, l) * PER_KT * var.value()
                             for (p, c, l, m), var in q.items() if var.value())
    handling_cost_val = sum(stockyards.loc[k, "handling_cost_usd_per_ton"] * PER_KT * var.value()
                             for (p, k, l, m), var in x.items() if var.value())
    fixed_cost_val = sum(stockyards.loc[k, "fixed_cost_usd"] * y[k].value() for k in K if y[k].value())
    tax_cost_val = total_cost - freight_cost_val - handling_cost_val - fixed_cost_val

    direct_kt = sum(r["qty_kt"] for r in q_rows)
    total_kt = customers["demand_flat_kt"].sum() + customers["demand_long_kt"].sum()

    kpi = dict(
        scenario=scenario, status=status, total_cost_usd=total_cost,
        freight_cost_usd=freight_cost_val, handling_cost_usd=handling_cost_val,
        fixed_cost_usd=fixed_cost_val, tax_cost_usd=tax_cost_val,
        n_stockyards_open=len(opened), stockyards_open=opened,
        direct_shipment_kt=direct_kt, direct_shipment_pct=100 * direct_kt / total_kt,
        total_volume_kt=total_kt,
        cost_per_ton_usd=total_cost / (total_kt * PER_KT),
    )
    return dict(kpi=kpi, x=pd.DataFrame(x_rows), z=pd.DataFrame(z_rows), q=pd.DataFrame(q_rows),
                opened=opened, prob_status=status)


if __name__ == "__main__":
    data = build_dataset()
    for scen in ["pre_gst", "post_gst"]:
        res = build_and_solve(data, scenario=scen)
        print(scen, "->", {k: v for k, v in res["kpi"].items() if k not in ("stockyards_open",)})
