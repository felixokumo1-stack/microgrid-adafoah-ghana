"""
01_load_profile.py
==================
Builds an 8760-hour synthetic load profile for the Ada East microgrid.

Method: Bottom-up demand estimation using IEA Multi-Tier Framework (MTF).
Reference: ESMAP/IEA (2015) Beyond Connections: Energy Access Redefined.

REVISION NOTE (April 2026):
Tier 2/3 consumption revised upward from IEA MTF minimum thresholds
(200/1000 Wh/day) to typical consumption values for coastal Ghana
(500/1500 Wh/day). MTF tiers are access thresholds, not consumption
estimates. Source: GOGLA 2022 Consumer Insights; ESMAP MTF Ghana survey.

Anchor loads revised upward to reflect WHO/UNICEF health facility
standards and productive use loads (fish processing, cold storage).

Author: Felix Okumo
Date: April 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# ── 0. Ensure output directories exist ────────────────────────────────────────
os.makedirs("data/processed", exist_ok=True)
os.makedirs("results/figures", exist_ok=True)

# ── 1. Site and community parameters ──────────────────────────────────────────
N_HOUSEHOLDS   = 500
TIER2_FRACTION = 0.60
TIER3_FRACTION = 0.40

# REVISED: IEA MTF values (200/1000) are minimum thresholds, not typical use.
# Typical coastal Ghana household with fan, lighting, phone, radio, small TV:
# Tier 2: 400–600 Wh/day → 500 Wh/day adopted (GOGLA 2022; ESMAP MTF Ghana)
# Tier 3: 1,200–2,000 Wh/day → 1,500 Wh/day adopted (Ghana Energy Commission 2021)
TIER2_DAILY_WH = 500    # REVISED from 200
TIER3_DAILY_WH = 1500   # REVISED from 1000

# REVISED: Anchor loads updated to reflect realistic facility demands
# and productive use loads for a coastal fishing community
ANCHOR_LOADS = {
    # Health clinic: refrigeration (vaccines), lighting, medical equipment
    # Reference: WHO/UNICEF Health Facility Energy Needs 2023: 8–15 kW rural clinic
    "health_clinic": {"peak_kw": 10.0, "hours_per_day": 16, "on_hour": 6},

    # Schools: lighting, fans, projector/computers
    # Reference: Ghana Education Service rural school load: 3–5 kW
    "school_1":      {"peak_kw": 4.0,  "hours_per_day": 9,  "on_hour": 7},
    "school_2":      {"peak_kw": 4.0,  "hours_per_day": 9,  "on_hour": 7},

    # Productive use: fish processing, cold storage, small commerce (10 units)
    # Reference: GOGLA Productive Use 2022: 1–3 kW per enterprise
    "shops":         {"peak_kw": 15.0, "hours_per_day": 12, "on_hour": 7},

    # Water pump: 700 residents × 50 L/day = 35,000 L/day
    # Head ~20 m, pump η=0.60 → P = ρgQH/η = ~3.9 kW → rounded to 5 kW
    "water_pump":    {"peak_kw": 5.0,  "hours_per_day": 8,  "on_hour": 6},
}

# Coincidence factor: IEC 62257-9-1 Annex B, rural community loads
COINCIDENCE_FACTOR = 0.60

# ── 2. Build hourly household demand shape ────────────────────────────────────
# Normalised 24-hour shape (must sum to 1.0).
# Evening peak 18:00–21:00 reflects post-sunset lighting, cooking, TV.
# Source: GOGLA 2022; Ghana Energy Commission load surveys.
HOURLY_SHAPE = np.array([
    0.01, 0.01, 0.01, 0.01, 0.01, 0.02,  # 00–05h: night (minimal)
    0.04, 0.06, 0.05, 0.03, 0.03, 0.03,  # 06–11h: morning routine
    0.03, 0.03, 0.04, 0.04, 0.05, 0.07,  # 12–17h: afternoon
    0.10, 0.12, 0.10, 0.06, 0.03, 0.02,  # 18–23h: evening peak
])

assert abs(HOURLY_SHAPE.sum() - 1.0) < 1e-9, \
    f"Shape sums to {HOURLY_SHAPE.sum():.6f}, must be 1.0"

# ── 3. Calculate daily household energy ───────────────────────────────────────
n_tier2 = int(N_HOUSEHOLDS * TIER2_FRACTION)   # 300 HH
n_tier3 = int(N_HOUSEHOLDS * TIER3_FRACTION)   # 200 HH

daily_hh_wh  = (n_tier2 * TIER2_DAILY_WH) + (n_tier3 * TIER3_DAILY_WH)
daily_hh_kwh = daily_hh_wh / 1000

print(f"Tier 2 households: {n_tier2} × {TIER2_DAILY_WH} Wh/day = "
      f"{n_tier2*TIER2_DAILY_WH/1000:.0f} kWh/day")
print(f"Tier 3 households: {n_tier3} × {TIER3_DAILY_WH} Wh/day = "
      f"{n_tier3*TIER3_DAILY_WH/1000:.0f} kWh/day")
print(f"Household daily energy demand: {daily_hh_kwh:.1f} kWh/day")

# ── 4. Build 8760-hour household load array ───────────────────────────────────
# Each element = power (kW) at that hour
# daily_shape_kwh[h] = kW drawn in hour h on a typical day
daily_shape_kwh = HOURLY_SHAPE * daily_hh_kwh * COINCIDENCE_FACTOR
hh_load_kwh     = np.tile(daily_shape_kwh, 365)  # 8760 values

print(f"Annual household energy (after CF=0.6): "
      f"{hh_load_kwh.sum():.1f} kWh/year")
print(f"Peak household hour: {hh_load_kwh.max():.2f} kW")

# ── 5. Build anchor load profiles ────────────────────────────────────────────
anchor_load_kwh = np.zeros(8760)

print(f"\nAnchor load breakdown:")
for name, params in ANCHOR_LOADS.items():
    peak_kw    = params["peak_kw"]
    hours      = params["hours_per_day"]
    start_hour = params["on_hour"]
    end_hour   = start_hour + hours

    daily_block = np.zeros(24)
    for h in range(24):
        if h == start_hour:
            daily_block[h] = peak_kw * 0.5       # ramp up
        elif start_hour < h < end_hour - 1:
            daily_block[h] = peak_kw              # full load
        elif h == end_hour - 1:
            daily_block[h] = peak_kw * 0.5       # ramp down

    annual_anchor = np.tile(daily_block, 365)
    anchor_load_kwh += annual_anchor
    print(f"  {name:<20}: peak {peak_kw:>5.1f} kW | "
          f"{annual_anchor.sum():>7.0f} kWh/year")

print(f"Total anchor load: {anchor_load_kwh.sum():.1f} kWh/year")

# ── 6. Total system load ──────────────────────────────────────────────────────
total_load_kwh    = hh_load_kwh + anchor_load_kwh
peak_load_kw      = total_load_kwh.max()
annual_energy_kwh = total_load_kwh.sum()
avg_load_kw       = annual_energy_kwh / 8760

print(f"\n{'='*50}")
print(f"LOAD PROFILE SUMMARY — Ada East Microgrid")
print(f"{'='*50}")
print(f"Peak demand:          {peak_load_kw:.2f} kW")
print(f"Average demand:       {avg_load_kw:.2f} kW")
print(f"Load factor:          {avg_load_kw/peak_load_kw:.3f}")
print(f"Annual energy:        {annual_energy_kwh:.1f} kWh/year")
print(f"Daily average:        {annual_energy_kwh/365:.1f} kWh/day")
print(f"{'='*50}")

# Sanity checks against engineering estimates
assert 40 <= peak_load_kw <= 150, \
    f"Peak {peak_load_kw:.1f} kW outside expected 40–150 kW range"
assert 150_000 <= annual_energy_kwh <= 500_000, \
    f"Annual energy {annual_energy_kwh:.0f} kWh outside expected range"
print("Sanity checks passed.\n")

# ── 7. Save to CSV ────────────────────────────────────────────────────────────
# IMPORTANT: timestamp is stored as a column, NOT as the index.
# This is what caused the CSV sum mismatch in model_verification.py —
# when loaded with index_col="timestamp", pandas miscounts rows.
# We load it with index_col="timestamp" and parse_dates=True in script 03.

timestamps = pd.date_range(start="2020-01-01 00:00", periods=8760, freq="h")

load_df = pd.DataFrame({
    "timestamp":     timestamps,
    "household_kw":  hh_load_kwh,
    "anchor_kw":     anchor_load_kwh,
    "total_load_kw": total_load_kwh,
})

load_df.to_csv("data/processed/load_profile_8760.csv", index=False)
print(f"Saved: data/processed/load_profile_8760.csv")

# Quick CSV verification — reload and check sum
verify = pd.read_csv("data/processed/load_profile_8760.csv")
print(f"CSV verification: {len(verify)} rows, "
      f"total_load_kw sum = {verify['total_load_kw'].sum():.1f} kWh")
assert abs(verify['total_load_kw'].sum() - annual_energy_kwh) < 1.0, \
    "CSV round-trip check failed"
print("CSV round-trip check passed.\n")

# ── 8. Plots ──────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(12, 7))
fig.suptitle(
    "Ada East Microgrid — Synthetic Load Profile\n"
    "500 Households + Anchor Loads, Siamekome Island, Ghana",
    fontsize=12, fontweight="bold"
)

# Panel A: one typical week
ax1 = axes[0]
week = 168
ax1.fill_between(range(week), load_df["household_kw"][:week],
                 alpha=0.7, color="#1B4FD8", label="Household load")
ax1.fill_between(range(week),
                 load_df["household_kw"][:week],
                 load_df["total_load_kw"][:week],
                 alpha=0.7, color="#16A34A", label="Anchor loads")
ax1.axhline(peak_load_kw, color="#DC2626", linestyle=":",
            linewidth=1.5, label=f"System peak: {peak_load_kw:.1f} kW")
ax1.set_xlabel("Hour of week")
ax1.set_ylabel("Power demand (kW)")
ax1.set_title("Typical week — Jan 1–7", fontsize=10)
ax1.legend(fontsize=9)
ax1.set_xlim(0, week)
ax1.grid(True, alpha=0.3, linestyle="--")

# Panel B: average 24-hour shape
ax2 = axes[1]
hourly_hh  = [hh_load_kwh[h::24].mean()     for h in range(24)]
hourly_anc = [anchor_load_kwh[h::24].mean()  for h in range(24)]
ax2.bar(range(24), hourly_hh,  color="#1B4FD8", alpha=0.8, label="Household")
ax2.bar(range(24), hourly_anc, bottom=hourly_hh,
        color="#16A34A", alpha=0.8, label="Anchor loads")
ax2.set_xlabel("Hour of day (0 = midnight)")
ax2.set_ylabel("Average power (kW)")
ax2.set_title("Average 24-hour demand profile", fontsize=10)
ax2.set_xticks(range(24))
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, linestyle="--", axis="y")

plt.tight_layout()
plt.savefig("results/figures/01_load_profile.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: results/figures/01_load_profile.png")