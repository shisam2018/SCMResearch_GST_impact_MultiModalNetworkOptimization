"""
data_generator.py
------------------
Generates a realistic, reproducible synthetic dataset for a multi-echelon,
multi-modal steel finished-goods distribution network in India, used to
demonstrate the pre-GST / post-GST network optimisation model.

All figures are illustrative (randomly generated with a fixed seed around
plausible industry ranges) and do NOT represent the actual data of any
named company. Distances are computed from public great-circle coordinates
of Indian cities.

Author: Generated for academic research-paper reproduction.
"""

import math
import random
import pandas as pd
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ----------------------------------------------------------------------
# 1. GEOGRAPHY  (public, approximate city-centre coordinates; degrees)
# ----------------------------------------------------------------------
CITY_COORDS = {
    "Delhi":         (28.70, 77.10, "Delhi"),
    "Mumbai":        (19.08, 72.88, "Maharashtra"),
    "Kolkata":       (22.57, 88.36, "West Bengal"),
    "Chennai":       (13.08, 80.27, "Tamil Nadu"),
    "Bangalore":     (12.97, 77.59, "Karnataka"),
    "Hyderabad":     (17.39, 78.49, "Telangana"),
    "Ahmedabad":     (23.02, 72.57, "Gujarat"),
    "Pune":          (18.52, 73.86, "Maharashtra"),
    "Jaipur":        (26.91, 75.79, "Rajasthan"),
    "Lucknow":       (26.85, 80.95, "Uttar Pradesh"),
    "Nagpur":        (21.15, 79.09, "Maharashtra"),
    "Patna":         (25.59, 85.14, "Bihar"),
    "Bhopal":        (23.26, 77.41, "Madhya Pradesh"),
    "Indore":        (22.72, 75.86, "Madhya Pradesh"),
    "Chandigarh":    (30.73, 76.78, "Chandigarh"),
    "Guwahati":      (26.14, 91.74, "Assam"),
    "Bhubaneswar":   (20.30, 85.82, "Odisha"),
    "Raipur":        (21.25, 81.63, "Chhattisgarh"),
    "Coimbatore":    (11.02, 76.97, "Tamil Nadu"),
    "Vijayawada":    (16.51, 80.65, "Andhra Pradesh"),
    "Kanpur":        (26.45, 80.33, "Uttar Pradesh"),
    "Ludhiana":      (30.90, 75.86, "Punjab"),
    "Surat":         (21.17, 72.83, "Gujarat"),
    "Visakhapatnam": (17.69, 83.22, "Andhra Pradesh"),
    "Kochi":         (9.93, 76.26, "Kerala"),
    "Varanasi":      (25.32, 82.97, "Uttar Pradesh"),
    "Dehradun":      (30.32, 78.03, "Uttarakhand"),
    "Siliguri":      (26.73, 88.43, "West Bengal"),
    "Rajkot":        (22.30, 70.80, "Gujarat"),
    "Madurai":       (9.93, 78.12, "Tamil Nadu"),
    "Amritsar":      (31.63, 74.87, "Punjab"),
    "Ranchi":        (23.34, 85.31, "Jharkhand"),
}

# Fictitious, non-identifying plant locations (representative eastern-India
# integrated-steel-plant belt; NOT the coordinates of any specific real plant)
PLANTS = {
    "Plant-1": dict(lat=22.95, lon=86.35, state="Jharkhand", capacity_kt=1900),
    "Plant-2": dict(lat=21.05, lon=86.30, state="Odisha",    capacity_kt=1100),
}

PORTS = {
    "Port-A": dict(lat=22.06, lon=88.06, state="West Bengal", linked_plant="Plant-1"),
    "Port-B": dict(lat=20.32, lon=86.61, state="Odisha",      linked_plant="Plant-2"),
    "Port-C": dict(lat=17.69, lon=83.22, state="Andhra Pradesh", linked_plant="Plant-2"),
}

CANDIDATE_STOCKYARDS = [
    "Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad",
    "Ahmedabad", "Pune", "Jaipur", "Lucknow", "Nagpur", "Patna", "Bhopal",
    "Indore", "Chandigarh", "Guwahati", "Bhubaneswar", "Raipur",
    "Coimbatore", "Vijayawada",
]

CUSTOMER_ZONES = CANDIDATE_STOCKYARDS + [
    "Kanpur", "Ludhiana", "Surat", "Visakhapatnam", "Kochi", "Varanasi",
    "Dehradun", "Siliguri", "Rajkot", "Madurai", "Amritsar", "Ranchi",
]

COASTAL_CUSTOMERS = {"Mumbai", "Chennai", "Kolkata", "Visakhapatnam", "Kochi", "Surat"}
COASTAL_STOCKYARDS = {"Mumbai", "Chennai", "Kolkata"}

PRODUCTS = ["Flat", "Long"]
MODES = ["Rail", "Road", "Sea"]

# ----------------------------------------------------------------------
# 2. DISTANCE  (great-circle x circuity factor to approximate route km)
# ----------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def route_km(lat1, lon1, lat2, lon2, circuity=1.30):
    return haversine_km(lat1, lon1, lat2, lon2) * circuity


def _coord(name):
    if name in PLANTS:
        return PLANTS[name]["lat"], PLANTS[name]["lon"]
    if name in PORTS:
        return PORTS[name]["lat"], PORTS[name]["lon"]
    return CITY_COORDS[name][0], CITY_COORDS[name][1]


def _state(name):
    if name in PLANTS:
        return PLANTS[name]["state"]
    if name in PORTS:
        return PORTS[name]["state"]
    return CITY_COORDS[name][2]


# ----------------------------------------------------------------------
# 3. FREIGHT-RATE MODEL  (Rs per ton, distance- and mode-dependent)
# ----------------------------------------------------------------------
FX_RATE = 83.0   # Rs per USD, used only to express final KPIs in USD for reporting

RAIL_BASE, RAIL_PER_KM, RAIL_IDLE_FACTOR = 180.0, 1.05, 1.09      # Rs/ton; incl. avg. idle/dead-freight loading
ROAD_BASE, ROAD_PER_KM = 120.0, 1.85                              # Rs/ton
SEA_BASE, SEA_PER_KM = 250.0, 0.55                                # Rs/ton
WIRE_ROD_DISCOUNT = 0.87   # Long-product wire-rod class (FOIS class 130) discount vs class 165


def freight_rate_usd(distance_km, mode, product):
    """Freight rate in USD per ton (converted from an underlying Rs/ton structure)."""
    if mode == "Rail":
        rate = (RAIL_BASE + RAIL_PER_KM * distance_km) * RAIL_IDLE_FACTOR
    elif mode == "Road":
        rate = ROAD_BASE + ROAD_PER_KM * distance_km
    elif mode == "Sea":
        rate = SEA_BASE + SEA_PER_KM * distance_km
    else:
        raise ValueError(mode)
    if product == "Long":
        rate *= WIRE_ROD_DISCOUNT
    return round(rate / FX_RATE, 3)


# backward-compatible alias operating in Rs (kept for transparency / audit)
def freight_rate(distance_km, mode, product):
    return round(freight_rate_usd(distance_km, mode, product) * FX_RATE, 2)


# ----------------------------------------------------------------------
# 4. MASTER DATA TABLES
# ----------------------------------------------------------------------
def build_dataset():
    # ---- Stockyards ----
    tiers = {}
    for i, city in enumerate(CANDIDATE_STOCKYARDS):
        tiers[city] = "Type-1" if i % 3 == 0 else ("Type-2" if i % 3 == 1 else "Type-3")

    stockyard_rows = []
    for city in CANDIDATE_STOCKYARDS:
        lat, lon = _coord(city)
        tier = tiers[city]
        base_cap = random.randint(180, 520)  # kt/yr throughput capacity
        # Annual fixed operating cost (USD): owned land+assets (Type-1) carries the
        # highest amortised capital charge; pure third-party (Type-2) the lowest.
        base_fixed_usd = {"Type-1": 480_000, "Type-2": 260_000, "Type-3": 360_000}[tier]
        fixed_cost_usd = base_fixed_usd * (base_cap / 350) * random.uniform(0.9, 1.1)
        handling = {"Type-1": 285, "Type-2": 245, "Type-3": 265}[tier] + random.randint(-15, 15)  # Rs/ton
        stockyard_rows.append(dict(
            stockyard=city, state=_state(city), lat=lat, lon=lon, tier=tier,
            throughput_cap_kt=float(base_cap),
            fixed_cost_usd=round(fixed_cost_usd, 0),
            handling_cost_usd_per_ton=round(handling / FX_RATE, 3),
            coastal=city in COASTAL_STOCKYARDS,
        ))
    stockyards = pd.DataFrame(stockyard_rows)

    # ---- Customers / demand ----
    cust_rows = []
    for city in CUSTOMER_ZONES:
        lat, lon = _coord(city)
        pop_weight = np.random.gamma(shape=2.2, scale=1.0)
        flat_demand = round(16 + pop_weight * 13 + random.uniform(-3, 3), 1)     # kt/yr
        long_demand = round(13 + pop_weight * 10 + random.uniform(-3, 3), 1)     # kt/yr
        cust_rows.append(dict(
            customer=city, state=_state(city), lat=lat, lon=lon,
            demand_flat_kt=max(flat_demand, 5.0),
            demand_long_kt=max(long_demand, 5.0),
            coastal_linked=city in COASTAL_CUSTOMERS,
        ))
    customers = pd.DataFrame(cust_rows)

    # ---- Plants ----
    plant_rows = []
    for name, info in PLANTS.items():
        plant_rows.append(dict(plant=name, state=info["state"], lat=info["lat"], lon=info["lon"],
                                capacity_kt=info["capacity_kt"]))
    plants = pd.DataFrame(plant_rows)

    # ---- Distances ----
    def dist_table(src_df, src_key, dst_df, dst_key):
        rows = []
        for _, s in src_df.iterrows():
            for _, d in dst_df.iterrows():
                km = route_km(s["lat"], s["lon"], d["lat"], d["lon"])
                rows.append({src_key: s[src_key], dst_key: d[dst_key], "distance_km": round(km, 1)})
        return pd.DataFrame(rows)

    dist_plant_stockyard = dist_table(plants, "plant", stockyards, "stockyard")
    dist_stockyard_customer = dist_table(stockyards, "stockyard", customers, "customer")
    dist_plant_customer = dist_table(plants, "plant", customers, "customer")

    return dict(
        plants=plants, stockyards=stockyards, customers=customers,
        dist_plant_stockyard=dist_plant_stockyard,
        dist_stockyard_customer=dist_stockyard_customer,
        dist_plant_customer=dist_plant_customer,
    )


TAX_ASSUMPTIONS = dict(
    pre_gst_cross_state_rate=0.025,     # CST + entry-tax friction, non-creditable, pre-GST
    post_gst_rate=0.18,                 # GST rate (fully input-tax-credited -> cost-neutral)
    unit_value_flat_usd_per_ton=round(52000 / FX_RATE, 2),
    unit_value_long_usd_per_ton=round(44000 / FX_RATE, 2),
    min_economic_volume_kt=30.0,        # minimum annual volume to justify opening a stockyard
)

if __name__ == "__main__":
    data = build_dataset()
    for k, v in data.items():
        print(k, v.shape)
        print(v.head(3))
        print()
