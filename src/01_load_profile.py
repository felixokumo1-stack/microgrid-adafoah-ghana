"""
01_load_profile.py
==================
Builds an 8760-hour synthetic load profile for the Ada Foah microgrid.

Method: Bottom-up demand estimation using IEA Multi-Tier Framework (MTF).
Reference: ESMAP/IEA (2015) Beyond Connections: Energy Access Redefined.

Author: [Felix Okumo]
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
# These values come directly from docs/assumptions.md
# Any change here must be reflected there too.

N_HOUSEHOLDS     = 500
TIER2_FRACTION   = 0.60          # 60% Tier 2 MTF households
TIER3_FRACTION   = 0.40          # 40% Tier 3 MTF households

TIER2_DAILY_WH   = 200           # Wh/day per Tier 2 household (IEA MTF 2020)
TIER3_DAILY_WH   = 1000          # Wh/day per Tier 3 household (IEA MTF 2020)

# Anchor loads (community facilities)
ANCHOR_LOADS = {
    "health_clinic":  {"peak_kw": 5.0,  "hours_per_day": 12, "on_hour": 7},
    "school_1":       {"peak_kw": 2.0,  "hours_per_day": 8,  "on_hour": 7},
    "school_2":       {"peak_kw": 2.0,  "hours_per_day": 8,  "on_hour": 7},
    "shops":          {"peak_kw": 5.0,  "hours_per_day": 10, "on_hour": 8},
    "water_pump":     {"peak_kw": 3.0,  "hours_per_day": 6,  "on_hour": 6},
}

# Coincidence factor: not all households peak at the same instant.
# 0.6 is standard for rural African communities (IEC 62257-9-1).
COINCIDENCE_FACTOR = 0.60

# ── 2. Build hourly household demand shape ────────────────────────────────────
# We define a normalised 24-hour shape (sums to 1.0).
# Peaks in morning (6-8h) and evening (18-21h) — typical Ghana rural pattern.
# Source: GOGLA 2022 Consumer Insights Report; Ghana Energy Commission load surveys.

HOURLY_SHAPE = np.array([
    0.01, 0.01, 0.01, 0.01, 0.01, 0.02,  # 00:00 – 05:00 (Night)
    0.04, 0.06, 0.05, 0.03, 0.03, 0.03,  # 06:00 – 11:00 (Morning)
    0.03, 0.03, 0.04, 0.04, 0.05, 0.07,  # 12:00 – 17:00 (Afternoon)
    0.10, 0.12, 0.10, 0.06, 0.03, 0.02,  # 18:00 – 23:00 (Evening Peak)
])

# Sanity check: shape must sum to exactly 1.0
assert abs(HOURLY_SHAPE.sum() - 1.0) < 1e-9, "Hourly shape fractions must sum to 1.0"

# ── 3. Calculate daily energy demand ──────────────────────────────────────────
n_tier2 = int(N_HOUSEHOLDS * TIER2_FRACTION)   # 300 households
n_tier3 = int(N_HOUSEHOLDS * TIER3_FRACTION)   # 200 households

daily_hh_wh = (n_tier2 * TIER2_DAILY_WH) + (n_tier3 * TIER3_DAILY_WH)
# = (300 × 200) + (200 × 1000) = 60,000 + 200,000 = 260,000 Wh/day

daily_hh_kwh = daily_hh_wh / 1000             # → 260 kWh/day
print(f"Household daily energy demand: {daily_hh_kwh:.1f} kWh/day")

# ── 4. Build the 8760-hour household load array ───────────────────────────────
# Repeat the 24-hour shape for 365 days.
# Apply coincidence factor to account for diversity of usage.

hours_per_year = 8760
daily_shape_kwh = HOURLY_SHAPE * daily_hh_kwh * COINCIDENCE_FACTOR
# daily_shape_kwh[h] = energy consumed in hour h on a typical day

# Tile (repeat) this pattern for all 365 days
hh_load_kwh = np.tile(daily_shape_kwh, 365)   # shape: (8760,)

print(f"Annual household energy: {hh_load_kwh.sum():.1f} kWh/year")
print(f"Peak household hour:     {hh_load_kwh.max():.2f} kW")

# ── 5. Build anchor load profiles ────────────────────────────────────────────
anchor_load_kwh = np.zeros(8760)

for name, params in ANCHOR_LOADS.items():
    peak_kw    = params["peak_kw"]
    hours      = params["hours_per_day"]
    start_hour = params["on_hour"]
    end_hour   = start_hour + hours

    # Build one 24-hour block for this load
    daily_block = np.zeros(24)
    # Trapezoidal shape: ramp up over 1 hour, flat, ramp down over 1 hour
    # This is more realistic than a square wave (avoids step-change discontinuities)
    for h in range(24):
        if h == start_hour:
            daily_block[h] = peak_kw * 0.5          # ramp up
        elif start_hour < h < end_hour - 1:
            daily_block[h] = peak_kw                 # full load
        elif h == end_hour - 1:
            daily_block[h] = peak_kw * 0.5          # ramp down

    # Tile for full year and add to anchor total
    anchor_load_kwh += np.tile(daily_block, 365)
    print(f"  {name}: {np.tile(daily_block,365).sum():.0f} kWh/year")

print(f"Annual anchor load energy: {anchor_load_kwh.sum():.1f} kWh/year")

# ── 6. Total system load ──────────────────────────────────────────────────────
total_load_kwh = hh_load_kwh + anchor_load_kwh

peak_load_kw      = total_load_kwh.max()
annual_energy_kwh = total_load_kwh.sum()
avg_load_kw       = annual_energy_kwh / 8760

print(f"\n{'='*45}")
print(f"LOAD PROFILE SUMMARY")
print(f"{'='*45}")
print(f"Peak demand:          {peak_load_kw:.2f} kW")
print(f"Average demand:       {avg_load_kw:.2f} kW")
print(f"Annual energy:        {annual_energy_kwh:.1f} kWh/year")
print(f"Daily average:        {annual_energy_kwh/365:.1f} kWh/day")
print(f"Load factor:          {avg_load_kw/peak_load_kw:.3f}")
print(f"{'='*45}\n")

# ── 7. Build datetime index and save to CSV ───────────────────────────────────
# pandas DatetimeIndex: hourly timestamps for 2020 (leap year = 8784 hrs)
# We use 365 days = 8760 hours as our simulation basis (standard for HOMER)
timestamps = pd.date_range(start="2020-01-01 00:00", periods=8760, freq="h")

load_df = pd.DataFrame({
    "timestamp":        timestamps,
    "household_kw":     hh_load_kwh,
    "anchor_kw":        anchor_load_kwh,
    "total_load_kw":    total_load_kwh,
})

load_df.to_csv("data/processed/load_profile_8760.csv", index=False)
print("Saved: data/processed/load_profile_8760.csv")

# ── 8. Plot 1: Typical week load profile ──────────────────────────────────────
# Show one representative week (168 hours) to validate shape
fig, axes = plt.subplots(2, 1, figsize=(12, 7))
fig.suptitle(
    "Ada Foah Microgrid — Synthetic Load Profile\n"
    "500 Households, Ada East District, Ghana",
    fontsize=12, fontweight="bold"
)

# Panel A: one week
week_hours = 168
ax1 = axes[0]
ax1.fill_between(range(week_hours), load_df["household_kw"][:week_hours],
                 alpha=0.6, color="#1B4FD8", label="Household load")
ax1.fill_between(range(week_hours),
                 load_df["household_kw"][:week_hours],
                 load_df["total_load_kw"][:week_hours],
                 alpha=0.6, color="#16A34A", label="Anchor loads")
ax1.set_xlabel("Hour of week")
ax1.set_ylabel("Power demand (kW)")
ax1.set_title("Typical week (Jan 1–7)", fontsize=10)
ax1.legend(loc="upper right")
ax1.set_xlim(0, week_hours)
ax1.grid(True, alpha=0.3, linestyle="--")
ax1.axhline(peak_load_kw, color="#DC2626", linestyle=":", linewidth=1.5,
            label=f"Peak: {peak_load_kw:.1f} kW")
ax1.legend(loc="upper right", fontsize=9)

# Panel B: average 24-hour profile
ax2 = axes[1]
hourly_avg = [total_load_kwh[h::24].mean() for h in range(24)]
hourly_hh  = [hh_load_kwh[h::24].mean()    for h in range(24)]
hourly_anc = [anchor_load_kwh[h::24].mean() for h in range(24)]

ax2.bar(range(24), hourly_hh,  color="#1B4FD8", alpha=0.7, label="Household")
ax2.bar(range(24), hourly_anc, bottom=hourly_hh,
        color="#16A34A", alpha=0.7, label="Anchor loads")
ax2.set_xlabel("Hour of day (0 = midnight)")
ax2.set_ylabel("Average power (kW)")
ax2.set_title("Average 24-hour load shape", fontsize=10)
ax2.set_xticks(range(24))
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, linestyle="--", axis="y")

plt.tight_layout()
plt.savefig("results/figures/01_load_profile.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: results/figures/01_load_profile.png")