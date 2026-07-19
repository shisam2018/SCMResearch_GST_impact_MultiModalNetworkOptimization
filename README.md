# Multimodal Steel Distribution Network Optimiser

A reproducible, open-source (PuLP/CBC) Mixed-Integer Linear Programming
reference implementation accompanying the research paper *"[paper title -
see manuscript]"*. It reproduces, on a synthetic-but-realistic dataset, the
pre-GST / post-GST outbound-logistics network re-optimisation problem for
an Indian steel-sector original equipment manufacturer (OEM).

## What is included

| File | Purpose |
|---|---|
| `data_generator.py` | Generates the synthetic-but-realistic master dataset (plants, ports, 20 candidate stockyards, 32 customer zones, distances, freight-rate structure, tax assumptions). Seeded for full reproducibility. |
| `milp_model.py` | The MILP formulation (sets, parameters, decision variables, objective, constraints) and solve routine, built with PuLP and solved by the open-source COIN-OR CBC solver. Supports both the pre-GST and post-GST scenario and an optional forced-open/forced-closed sensitivity override. |
| `run_analysis.py` | Runs both scenarios end-to-end and writes all KPI, flow and comparison tables to `outputs/`. |
| `app.py` | The Streamlit dashboard (interactive scenario toggle, what-if sensitivity controls, network map, cost-breakdown views, and a side-by-side scenario comparison tab). |
| `fig_*.py` | Stand-alone scripts that regenerate every figure used in the manuscript directly from the model output. |
| `geo/india_states_simplified.geojson` | Simplified state-boundary basemap used for the network maps (derived from public boundary data). |
| `requirements.txt` | Python package dependencies. |

## Quick start

```bash
pip install -r requirements.txt

# 1. Run both scenarios and populate outputs/
python run_analysis.py

# 2. Regenerate all manuscript figures into figures/
python fig_network_map.py
python fig_cost_comparison.py
python fig_stockyard_status.py
python fig_pre_post_gst_concept.py
python fig_network_structure.py
python fig_ishikawa.py
python fig_process_flow.py
python fig_sensitivity.py
python fig_dashboard_mockup.py

# 3. Launch the interactive dashboard
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. Use the sidebar to switch
between the Pre-GST and Post-GST regulatory regimes, force specific
candidate stockyards open or closed, and re-solve the model interactively.

## Model summary

Two-echelon, multi-modal (Rail / Road / Sea), capacitated facility-location
and transportation MILP with a fixed-charge stockyard-opening decision.
The pre-GST and post-GST scenarios differ only in one respect: the
pre-GST objective adds a non-creditable cross-state "sale-leg" tax penalty
(representing central sales tax / entry-tax friction) that is absent,
by construction, from the post-GST objective (destination-based, fully
input-tax-credited GST). Full indices, parameters, decision variables and
constraints are documented in the manuscript's Methodology section and in
the docstring of `milp_model.py`.

## Reproducibility and data note

All demand, capacity, cost and tax-rate figures are **synthetically
generated** (fixed random seed = 42) around industry-plausible ranges for
academic demonstration purposes. They do not represent, and should not be
attributed to, the confidential commercial data of any real company.
City coordinates are public geographic facts used only to compute
illustrative great-circle route distances.

## Solver

Solved with **COIN-OR CBC** via the **PuLP** Python interface - a fully
open-source, licence-free alternative to commercial MILP solvers, chosen
so that any reader can reproduce every result in this paper without a
commercial software licence.
