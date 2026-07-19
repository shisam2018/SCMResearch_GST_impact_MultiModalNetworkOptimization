"""
app.py
-------
Streamlit dashboard for the Multimodal Steel Distribution Network Optimiser.

Run locally with:
    pip install -r requirements.txt
    streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from data_generator import build_dataset, TAX_ASSUMPTIONS
from milp_model import build_and_solve

st.set_page_config(page_title="Steel Distribution Network Optimiser",
                    page_icon="\U0001F4C8", layout="wide", initial_sidebar_state="expanded")

# ----------------------------------------------------------------------
# ACADEMIC / PROFESSIONAL STYLING
# ----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Source Serif 4', serif !important; color: #1F4E79; }
.main-header {
    background: linear-gradient(90deg, #1F4E79 0%, #2E6B5E 100%);
    padding: 1.6rem 2rem; border-radius: 10px; color: white; margin-bottom: 1.4rem;
}
.main-header h1 { color: white !important; margin: 0; font-size: 1.65rem; }
.main-header p { color: #DCE8EC; margin: 0.25rem 0 0 0; font-size: 0.92rem; font-style: italic;}
div[data-testid="stMetric"] {
    background-color: #FFFFFF; border: 1px solid #E3E6EA; border-radius: 10px;
    padding: 0.9rem 1rem; border-left: 5px solid #1F4E79;
}
.footnote { color: #6b6b6b; font-size: 0.78rem; font-style: italic; margin-top: 2rem; border-top: 1px solid #ddd; padding-top: 0.6rem;}
.section-card { background-color: #FAFBFC; border: 1px solid #E7E9EC; border-radius: 10px; padding: 1.1rem 1.3rem; margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
<h1>Multimodal Steel Distribution Network Optimiser</h1>
<p>A Mixed-Integer Linear Programming decision-support tool for pre-GST vs. post-GST outbound
logistics network design &mdash; academic reference implementation (PuLP / CBC, open-source solver)</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# DATA (cached)
# ----------------------------------------------------------------------
@st.cache_data
def get_data():
    return build_dataset()

data = get_data()
all_stockyards = sorted(data["stockyards"]["stockyard"].tolist())

# ----------------------------------------------------------------------
# SIDEBAR CONTROLS
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Scenario configuration")
    scenario_label = st.radio("Regulatory regime", ["Post-GST (current law)", "Pre-GST (historical)"], index=0)
    scenario = "post_gst" if "Post" in scenario_label else "pre_gst"

    st.markdown("---")
    st.markdown("### What-if sensitivity")
    st.caption("Override the model's own open/close decision for specific candidate locations, "
               "then re-solve to see the cost impact (mirrors a classical inclusion/exclusion "
               "sensitivity study).")
    forced_open = st.multiselect("Force OPEN these candidate stockyards", all_stockyards)
    forced_closed = st.multiselect("Force CLOSED these candidate stockyards",
                                    [s for s in all_stockyards if s not in forced_open])

    st.markdown("---")
    solve_clicked = st.button("\u25B6  Solve / re-solve model", width='stretch', type="primary")

    st.markdown("---")
    with st.expander("About the dataset"):
        st.write(
            "The network comprises **2 manufacturing plants**, **3 ports**, **20 candidate "
            "stockyard locations**, and **32 aggregated customer zones** across India, moving "
            "**2 product families** (Flat, Long) by **3 transport modes** (Rail, Road, Sea). "
            "All figures are synthetically generated at run time around industry-plausible "
            "ranges for illustrative, reproducible academic use; they do not represent the "
            "confidential data of any real organisation."
        )

# ----------------------------------------------------------------------
# SOLVE
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def solve_cached(scenario, forced_open_t, forced_closed_t):
    res = build_and_solve(data, scenario=scenario, forced_open=list(forced_open_t),
                           forced_closed=list(forced_closed_t))
    return res

with st.spinner("Solving mixed-integer program (CBC branch-and-bound)..."):
    result = solve_cached(scenario, tuple(sorted(forced_open)), tuple(sorted(forced_closed)))

kpi = result["kpi"]

# ----------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total annual cost", f"${kpi['total_cost_usd']/1e6:,.2f} M")
c2.metric("Cost per ton", f"${kpi['cost_per_ton_usd']:.2f}")
c3.metric("Stockyards open", f"{kpi['n_stockyards_open']} / {len(all_stockyards)}")
c4.metric("Direct-dispatch share", f"{kpi['direct_shipment_pct']:.1f}%")
c5.metric("Solver status", kpi["status"])

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["\U0001F5FA Network map", "\U0001F4CA Cost breakdown",
                                    "\U0001F4CB Stockyard decisions", "\U0001F4C8 Scenario comparison"])

# ----------------------------------------------------------------------
# TAB 1: MAP
# ----------------------------------------------------------------------
with tab1:
    stockyards = data["stockyards"].copy()
    stockyards["status"] = np.where(stockyards["stockyard"].isin(result["opened"]), "Open", "Closed")
    customers = data["customers"]
    plants = data["plants"]

    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lon=customers["lon"], lat=customers["lat"], mode="markers",
                                 marker=dict(size=5, color="#BFBFBF"), name="Customer zone"))
    closed = stockyards[stockyards["status"] == "Closed"]
    openv = stockyards[stockyards["status"] == "Open"]
    fig.add_trace(go.Scattergeo(lon=closed["lon"], lat=closed["lat"], mode="markers",
                                 marker=dict(size=9, color="white", line=dict(color="#888", width=1.5), symbol="square"),
                                 name="Candidate (closed)"))
    fig.add_trace(go.Scattergeo(lon=openv["lon"], lat=openv["lat"], mode="markers",
                                 marker=dict(size=13, color="#2E6B5E", line=dict(color="#1a1a1a", width=1), symbol="square"),
                                 name="Open stockyard", text=openv["stockyard"]))
    fig.add_trace(go.Scattergeo(lon=plants["lon"], lat=plants["lat"], mode="markers",
                                 marker=dict(size=18, color="#8C3B3B", symbol="star", line=dict(color="#1a1a1a", width=1)),
                                 name="Manufacturing plant", text=plants["plant"]))

    fig.update_geos(scope="asia", center=dict(lat=22, lon=82), projection_scale=5.2,
                     showland=True, landcolor="#F2F0EA", showcountries=True, countrycolor="#AAAAAA",
                     showcoastlines=True, coastlinecolor="#AAAAAA")
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0),
                       legend=dict(orientation="h", yanchor="bottom", y=-0.05))
    st.plotly_chart(fig, width='stretch')
    st.caption("Marker size for open stockyards is constant; use the **Stockyard decisions** tab for exact throughput figures.")

# ----------------------------------------------------------------------
# TAB 2: COST BREAKDOWN
# ----------------------------------------------------------------------
with tab2:
    col1, col2 = st.columns([1, 1])
    with col1:
        comp = pd.DataFrame({
            "Component": ["Freight", "Handling", "Fixed (stockyard)", "Tax friction"],
            "USD": [kpi["freight_cost_usd"], kpi["handling_cost_usd"], kpi["fixed_cost_usd"], kpi["tax_cost_usd"]],
        })
        fig2 = px.pie(comp, names="Component", values="USD", hole=0.45,
                       color_discrete_sequence=["#1F4E79", "#3E8E7E", "#D9A441", "#B5591C"])
        fig2.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), title="Annual cost composition")
        st.plotly_chart(fig2, width='stretch')
    with col2:
        st.markdown("#### Cost summary")
        st.dataframe(comp.assign(**{"USD million": (comp["USD"]/1e6).round(2)})[["Component", "USD million"]],
                     hide_index=True, width='stretch')
        st.markdown(f"""
        <div class="section-card">
        <b>Total annual network cost:</b> ${kpi['total_cost_usd']/1e6:,.2f} million<br>
        <b>Total volume served:</b> {kpi['total_volume_kt']:,.0f} kt/year<br>
        <b>Effective cost per ton:</b> ${kpi['cost_per_ton_usd']:.2f}
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# TAB 3: STOCKYARD DECISIONS
# ----------------------------------------------------------------------
with tab3:
    sy_view = data["stockyards"].copy()
    sy_view["Decision"] = np.where(sy_view["stockyard"].isin(result["opened"]), "OPEN", "closed")
    inflow = result["x"].groupby("stockyard")["qty_kt"].sum().reindex(sy_view["stockyard"]).fillna(0).round(1)
    sy_view["Throughput (kt/yr)"] = inflow.values
    sy_view = sy_view.sort_values("Decision", ascending=False)
    st.dataframe(
        sy_view[["stockyard", "state", "tier", "Decision", "Throughput (kt/yr)", "throughput_cap_kt", "fixed_cost_usd"]]
        .rename(columns={"stockyard": "Stockyard", "state": "State", "tier": "Ownership tier",
                          "throughput_cap_kt": "Capacity (kt/yr)", "fixed_cost_usd": "Fixed cost (USD/yr)"}),
        hide_index=True, width='stretch', height=460,
    )

# ----------------------------------------------------------------------
# TAB 4: SCENARIO COMPARISON
# ----------------------------------------------------------------------
with tab4:
    st.caption("Runs both regulatory scenarios (unconstrained) side-by-side for reference, regardless of the sidebar selection.")
    res_pre = solve_cached("pre_gst", tuple(), tuple())
    res_post = solve_cached("post_gst", tuple(), tuple())
    comp_df = pd.DataFrame([
        {"Metric": "Total annual cost (USD M)", "Pre-GST": res_pre["kpi"]["total_cost_usd"]/1e6, "Post-GST": res_post["kpi"]["total_cost_usd"]/1e6},
        {"Metric": "Cost per ton (USD)", "Pre-GST": res_pre["kpi"]["cost_per_ton_usd"], "Post-GST": res_post["kpi"]["cost_per_ton_usd"]},
        {"Metric": "Stockyards open", "Pre-GST": res_pre["kpi"]["n_stockyards_open"], "Post-GST": res_post["kpi"]["n_stockyards_open"]},
        {"Metric": "Direct-dispatch share (%)", "Pre-GST": res_pre["kpi"]["direct_shipment_pct"], "Post-GST": res_post["kpi"]["direct_shipment_pct"]},
    ])
    st.dataframe(comp_df.round(2), hide_index=True, width='stretch')
    fig3 = px.bar(comp_df, x="Metric", y=["Pre-GST", "Post-GST"], barmode="group",
                  color_discrete_sequence=["#B5591C", "#3E8E7E"])
    fig3.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig3, width='stretch')

st.markdown(
    '<p class="footnote">Reference academic implementation. Solver: COIN-OR CBC via PuLP (open source). '
    'Distances from public city coordinates; all cost, capacity and demand parameters are synthetically '
    'generated (see data_generator.py) and are illustrative only.</p>', unsafe_allow_html=True)
