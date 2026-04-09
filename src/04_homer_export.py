"""
04_homer_export.py
==================
Exports processed data to HOMER Grid input format.

HOMER load CSV format requirements:
- 8760 rows, one per hour
- Single column of load values in kW
- No header row
- Values represent average power during that hour

HOMER wind resource format:
- 8760 rows
- Column: wind speed in m/s at hub height
- No header

Author: Felix Okumo
Date: April 2026
"""

import pandas as pd
import numpy as np
import os

os.makedirs("homer", exist_ok=True)

# ── 1. Load profile export ────────────────────────────────────
load = pd.read_csv("data/processed/load_profile_8760.csv")

# HOMER requires: one column, kW, 8760 rows, no header
homer_load = load["total_load_kw"].values

# Validate
assert len(homer_load) == 8760, "Must be exactly 8760 rows"
assert homer_load.min() >= 0,   "No negative loads"
assert homer_load.max() <= 200, f"Peak {homer_load.max():.1f} kW seems high — check"

np.savetxt("homer/load_profile_homer.csv", homer_load, fmt="%.4f")
print(f"Load export:")
print(f"  Rows:        {len(homer_load)}")
print(f"  Peak:        {homer_load.max():.2f} kW")
print(f"  Mean:        {homer_load.mean():.2f} kW")
print(f"  Annual sum:  {homer_load.sum():.0f} kWh")
print(f"  Saved: homer/load_profile_homer.csv")

# ── 2. Solar resource export (GHI for HOMER) ─────────────────
solar = pd.read_csv("data/processed/solar_resource.csv",
                    index_col="timestamp", parse_dates=True)

# HOMER solar: hourly GHI in kWh/m² (not W/m²)
# Convert: W/m² × 1h = Wh/m² ÷ 1000 = kWh/m²
ghi_kwh = solar["GHI_Wm2"].values / 1000.0

np.savetxt("homer/solar_ghi_homer.csv", ghi_kwh, fmt="%.6f")
print(f"\nSolar export:")
print(f"  Annual GHI:  {ghi_kwh.sum():.1f} kWh/m²/yr")
print(f"  Daily avg:   {ghi_kwh.sum()/365:.3f} kWh/m²/day  (PSH)")
print(f"  Saved: homer/solar_ghi_homer.csv")

# ── 3. Wind resource export ───────────────────────────────────
# HOMER wind: hourly wind speed in m/s at hub height
ws_50m = solar["WS50m_ERA5_ms"].values

np.savetxt("homer/wind_speed_homer.csv", ws_50m, fmt="%.4f")
print(f"\nWind export (ERA5, 50m):")
print(f"  Mean WS:     {ws_50m.mean():.3f} m/s")
print(f"  Max WS:      {ws_50m.max():.3f} m/s")
print(f"  Saved: homer/wind_speed_homer.csv")

# ── 4. Summary table for HOMER manual entry ──────────────────
print(f"\n{'='*55}")
print(f"HOMER MANUAL ENTRY REFERENCE")
print(f"{'='*55}")
print(f"\nLOCATION:")
print(f"  Latitude:       5.7833°N")
print(f"  Longitude:      0.6333°E")
print(f"  Elevation:      2 m asl")
print(f"  Time zone:      GMT+0")

print(f"\nLOAD:")
print(f"  Peak demand:    {homer_load.max():.1f} kW")
print(f"  Annual energy:  {homer_load.sum():.0f} kWh/yr")
print(f"  Load type:      AC primary load")
print(f"  Scaled annual:  {homer_load.sum():.0f} kWh/yr (no scaling)")

print(f"\nSOLAR PV (enter per kWp, HOMER scales):")
print(f"  Derating:       68.7%  (PR = η_inv × f_temp × f_soil)")
print(f"  Lifetime:       25 years")
print(f"  Cost:           EUR 250/kWp capital, EUR 5/kWp/yr O&M")
print(f"  Search space:   20, 40, 60, 80, 100, 120, 150 kWp")

print(f"\nWIND TURBINE (IEC Class III, 50 kW):")
print(f"  Hub height:     50 m")
print(f"  Cut-in:         2.5 m/s")
print(f"  Rated speed:    11.0 m/s")
print(f"  Cut-out:        25.0 m/s")
print(f"  Cost:           EUR 75,000 capital (EUR 1,500/kW)")
print(f"               EUR 3,000/yr O&M (4% of capital)")
print(f"  Search space:   0, 1, 2, 3 units")

print(f"\nBATTERY (LFP, 1C, 100 kWh modules):")
print(f"  Capacity:       100 kWh per unit")
print(f"  Min SOC:        20% (80% DoD)")
print(f"  Round-trip η:   94%")
print(f"  Lifetime:       15 years")
print(f"  Cost:           EUR 40,000/unit capital (EUR 400/kWh)")
print(f"               EUR 800/unit/yr O&M (2% of capital)")
print(f"  Search space:   2, 4, 6, 8, 10 units (200–1000 kWh)")

print(f"\nDIESEL GENERATOR:")
print(f"  Sizes to test:  40, 60, 80 kW")
print(f"  Cost:           EUR 300/kW capital, EUR 9/kW/yr O&M (3%)")
print(f"  Fuel price:     EUR 1.44/L (USD 1.56 ÷ 1.08)")
print(f"  Fuel curve a:   0.0811 L/kWh")
print(f"  Fuel curve b:   0.2450 L/kWh")
print(f"  Min load ratio: 30%")
print(f"  Lifetime:       15,000 hours")

print(f"\nSYSTEM:")
print(f"  Project life:   20 years")
print(f"  Discount rate:  8% (base), 12% (sensitivity)")
print(f"  Annual capacity shortage: ≤ 5% (LPSP constraint)")
print(f"  Operating reserve: 10% of hourly load")
print(f"               + 25% of PV output (cloud ramp)")
print(f"               + 50% of wind output (variability)")