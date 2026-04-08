"""
02_resource_assessment.py
=========================
Processes PVGIS TMY and Renewables.ninja wind data for Ada East, Ghana.

Outputs:
  - data/processed/solar_resource.csv    (8760-hour GHI, T2m, DNI, DHI)
  - data/processed/wind_resource.csv     (8760-hour wind speed + capacity factor)
  - results/figures/02a_solar_resource.png
  - results/figures/02b_wind_resource.png
  - results/figures/02c_resource_overlap.png

References:
  - PVGIS ERA5 TMY methodology: Huld et al. (2012), Solar Energy
  - Wind shear: IEC 61400-1:2019 Ed.4, Table 1
  - Air density correction: IEC 61400-12-1:2017

Author: Felix Okumo
Date: April 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

os.makedirs("data/processed", exist_ok=True)
os.makedirs("results/figures", exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# PART 1 — SOLAR RESOURCE (PVGIS TMY)
# ═══════════════════════════════════════════════════════════════

print("=" * 55)
print("PART 1: SOLAR RESOURCE — PVGIS ERA5 TMY")
print("=" * 55)

# ── 1.1 Load PVGIS TMY CSV ───────────────────────────────────
# Fix 1: skiprows=17 lands exactly on the correct header for this specific file structure
pvgis_raw = pd.read_csv(
    "data/raw/pvgis_tmy_adafoah.csv",
    skiprows=17,          
    on_bad_lines="skip"
)

# Print raw columns so we can see exactly what PVGIS gave us
print("\nRaw PVGIS columns:", pvgis_raw.columns.tolist())
print(f"Raw rows: {len(pvgis_raw)}")

# ── 1.2 Rename and select columns ────────────────────────────
# PVGIS column names vary slightly by download version.
# Map whatever we got to standard internal names.

rename_map = {}
for col in pvgis_raw.columns:
    cl = col.strip().lower()
    if "g(h)"   in cl or "ghi"  in cl: rename_map[col] = "GHI_Wm2"
    if "gb(n)"  in cl or "dni"  in cl: rename_map[col] = "DNI_Wm2"
    if "gd(h)"  in cl or "dhi"  in cl: rename_map[col] = "DHI_Wm2"
    if "t2m"    in cl or "temp" in cl: rename_map[col] = "T2m_C"
    if "ws10m"  in cl or "wind" in cl: rename_map[col] = "WS10m_ms"
    if "time"   in cl:                 rename_map[col] = "time_str"

pvgis = pvgis_raw.rename(columns=rename_map)
print("\nRenamed columns available:", pvgis.columns.tolist())

# Keep only the columns we need
keep = [c for c in ["GHI_Wm2","DNI_Wm2","DHI_Wm2","T2m_C","WS10m_ms","time_str"]
        if c in pvgis.columns]
pvgis = pvgis[keep].copy()

# Fix 2: Force numeric conversion to avoid "Unknown format code 'f' for str"
cols_to_fix = [c for c in ["GHI_Wm2","DNI_Wm2","DHI_Wm2","T2m_C","WS10m_ms"] if c in pvgis.columns]
for col in cols_to_fix:
    pvgis[col] = pd.to_numeric(pvgis[col], errors="coerce")

# Drop any non-numeric footer junk safely
if "GHI_Wm2" in pvgis.columns and "T2m_C" in pvgis.columns:
    pvgis = pvgis.dropna(subset=["GHI_Wm2", "T2m_C"]).copy()

# ── 1.3 Build a clean 8760-hour DatetimeIndex ─────────────────
# PVGIS TMY timestamps use year 2005 as the base year internally.
# We re-index to a clean 2020 calendar for consistency with load profile.

pvgis = pvgis.head(8760).reset_index(drop=True)   # ensure exactly 8760 rows
timestamps = pd.date_range("2020-01-01 00:00", periods=8760, freq="h")
pvgis.index = timestamps
pvgis.index.name = "timestamp"

# ── 1.4 Data validation ──────────────────────────────────────
print(f"\nRows after trimming to 8760: {len(pvgis)}")
print(f"GHI range:  {pvgis['GHI_Wm2'].min():.1f} – {pvgis['GHI_Wm2'].max():.1f} W/m²")
print(f"T2m range:  {pvgis['T2m_C'].min():.1f} – {pvgis['T2m_C'].max():.1f} °C")
if "WS10m_ms" in pvgis.columns:
    print(f"WS10m range:{pvgis['WS10m_ms'].min():.1f} – {pvgis['WS10m_ms'].max():.1f} m/s")

# Physical sanity checks — GHI cannot be negative or > 1400 W/m²
assert pvgis["GHI_Wm2"].min() >= 0,        "ERROR: Negative GHI values found"
assert pvgis["GHI_Wm2"].max() <= 1400,     "ERROR: GHI exceeds physical maximum"
assert pvgis["T2m_C"].min()  >= 10,        "ERROR: Temperature below 10°C — check site"
print("\nSanity checks passed.")

# ── 1.5 Key solar metrics ─────────────────────────────────────
# Daily sum: GHI (W/m²) × 1 hour → Wh/m²; divide by 1000 → kWh/m²/day
daily_ghi   = pvgis["GHI_Wm2"].resample("D").sum() / 1000   # kWh/m²/day
annual_ghi  = daily_ghi.sum()                               # kWh/m²/year
avg_daily   = daily_ghi.mean()                              # kWh/m²/day (annual average)
peak_sun_hrs = avg_daily   # PSH = average daily GHI in kWh/m²/day (numerically equal)

print(f"\n{'─'*45}")
print(f"SOLAR RESOURCE SUMMARY")
print(f"{'─'*45}")
print(f"Annual GHI:            {annual_ghi:.0f} kWh/m²/year")
print(f"Average daily GHI:     {avg_daily:.2f} kWh/m²/day")
print(f"Peak sun hours (PSH):  {peak_sun_hrs:.2f} h/day")
print(f"Max hourly GHI:        {pvgis['GHI_Wm2'].max():.0f} W/m²")
print(f"Mean temperature:      {pvgis['T2m_C'].mean():.1f} °C")
print(f"{'─'*45}")

# ── 1.6 PV temperature derating factor ──────────────────────
# PV output decreases as module temperature rises above STC (25°C).
# Module temp ≈ T2m + 25°C (NOCT correction, open-rack mounting, IEC 61215)
# Power Temperature Coefficient for typical mono-Si: -0.40 %/°C (manufacturer spec)

TEMP_COEFF   = -0.004          # per °C (i.e. -0.40%/°C)
T_stc        = 25.0            # °C, Standard Test Conditions
T_noct_rise  = 25.0            # °C, NOCT rise above ambient (open rack)

pvgis["T_module_C"]     = pvgis["T2m_C"] + T_noct_rise
pvgis["derating_factor"] = 1 + TEMP_COEFF * (pvgis["T_module_C"] - T_stc)

mean_derate = pvgis["derating_factor"].mean()
print(f"\nMean PV temperature derating factor: {mean_derate:.4f}")
print(f"  → PV output reduced by {(1-mean_derate)*100:.1f}% on average due to heat")
print(f"  (Worst-case hour derating: {pvgis['derating_factor'].min():.4f})")

# ── 1.7 Save processed solar data ────────────────────────────
pvgis.to_csv("data/processed/solar_resource.csv")
print("\nSaved: data/processed/solar_resource.csv")


# ═══════════════════════════════════════════════════════════════
# PART 2 — WIND RESOURCE (Renewables.ninja)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("PART 2: WIND RESOURCE — Renewables.ninja MERRA-2")
print("=" * 55)

# ── 2.1 Load ninja CSV ───────────────────────────────────────
# Fix 3: Use comment='#' to skip the JSON metadata in Ninja files
ninja_raw = pd.read_csv(
    "data/raw/ninja_wind_adafoah_2019.csv",
    comment="#",
    on_bad_lines="skip"
)

print(f"\nRaw Ninja columns: {ninja_raw.columns.tolist()}")
print(f"Raw rows: {len(ninja_raw)}")

# ── 2.2 Rename columns ───────────────────────────────────────
rename_wind = {}
for col in ninja_raw.columns:
    cl = col.strip().lower()
    if cl == "time":               # Exact match to prevent catching "local_time"
        rename_wind[col] = "timestamp"
    elif "electricity" in cl: 
        rename_wind[col] = "cf_wind"      # capacity factor 0–1
    elif "wind_speed" in cl: 
        rename_wind[col] = "WS_hub_ms"    # m/s at hub height

ninja = ninja_raw.rename(columns=rename_wind)

# Drop local_time to keep the dataframe clean
if "local_time" in ninja.columns:
    ninja = ninja.drop(columns=["local_time"])

print("Renamed wind columns:", ninja.columns.tolist())

# Convert wind to numeric to avoid formatting errors
for col in ["cf_wind", "WS_hub_ms"]:
    if col in ninja.columns:
        ninja[col] = pd.to_numeric(ninja[col], errors="coerce")

if "cf_wind" in ninja.columns:
    ninja = ninja.dropna(subset=["cf_wind"]).copy()

# ── 2.3 Parse timestamps and reindex to 8760 ─────────────────
ninja["timestamp"] = pd.to_datetime(ninja["timestamp"])
ninja = ninja.set_index("timestamp")

# Ninja 2019 gives 8760 hours (non-leap year) — trim to be safe
ninja = ninja.head(8760).copy()

# Re-index to 2020 calendar (matching load and solar)
ninja.index = timestamps
ninja.index.name = "timestamp"

# ── 2.4 Wind shear extrapolation (verification) ──────────────
# Ninja already provides wind speed at hub height (50m).
# We verify this matches our hand-calculation from Phase 0.

ALPHA    = 0.12          # wind shear exponent, IEC 61400-1, coastal flat
H_REF    = 10.0          # reference height (m) — Ninja raw wind is at 10m internally
H_HUB    = 50.0          # our hub height

if "WS_hub_ms" in ninja.columns:
    mean_ws_hub = ninja["WS_hub_ms"].mean()
    # Cross-check: apply shear to PVGIS 10m wind
    if "WS10m_ms" in pvgis.columns:
        ws_10m_pvgis   = pvgis["WS10m_ms"].mean()
        ws_50m_calc    = ws_10m_pvgis * (H_HUB / H_REF) ** ALPHA
        print(f"\nWind speed cross-check:")
        print(f"  PVGIS WS at 10m (TMY mean):    {ws_10m_pvgis:.2f} m/s")
        print(f"  Extrapolated to 50m (α=0.12):  {ws_50m_calc:.2f} m/s")
        print(f"  Ninja WS at 50m hub (mean):    {mean_ws_hub:.2f} m/s")
        discrepancy = abs(ws_50m_calc - mean_ws_hub)
        print(f"  Discrepancy: {discrepancy:.2f} m/s", end="  ")
        print("✓ ACCEPTABLE" if discrepancy < 1.0 else "⚠ CHECK DATA SOURCES")

# ── 2.5 Key wind metrics ──────────────────────────────────────
cf_mean   = ninja["cf_wind"].mean()
cf_max    = ninja["cf_wind"].max()
hours_above_cutout = (ninja["cf_wind"] == 0).sum()   # hours turbine is shut down

# Weibull fit: characterises wind speed distribution
# Used later in HOMER; computed here for documentation
if "WS_hub_ms" in ninja.columns:
    from scipy.stats import weibull_min
    ws_positive = ninja["WS_hub_ms"][ninja["WS_hub_ms"] > 0.5]
    # Weibull shape (k) and scale (λ) parameters
    shape_k, loc, scale_lam = weibull_min.fit(ws_positive, floc=0)
    print(f"\n{'─'*45}")
    print(f"WIND RESOURCE SUMMARY (50m hub)")
    print(f"{'─'*45}")
    print(f"Mean wind speed:          {ninja['WS_hub_ms'].mean():.2f} m/s")
    print(f"Max wind speed:           {ninja['WS_hub_ms'].max():.2f} m/s")
    print(f"Mean capacity factor:     {cf_mean:.3f}  ({cf_mean*100:.1f}%)")
    print(f"Weibull k (shape):        {shape_k:.2f}")
    print(f"Weibull λ (scale):        {scale_lam:.2f} m/s")
    print(f"Hours at zero output:     {hours_above_cutout} h/yr ({hours_above_cutout/87.6:.1f}%)")
    print(f"{'─'*45}")

# ── 2.6 Air density correction note ──────────────────────────
# Standard air density at sea level, 15°C (ISA): 1.225 kg/m³
# Ada East: ~2m asl, mean T2m ~28°C
# Actual ρ = 1.225 × (288.15 / (273.15 + 28)) × (101325 / 101325) ≈ 1.165 kg/m³
# Power ∝ ρ, so turbine output reduced by factor: 1.165/1.225 = 0.951 → ~5% less
# Renewables.ninja applies this correction internally — we note it here for transparency

RHO_std  = 1.225
T_mean_K = 273.15 + pvgis["T2m_C"].mean()
RHO_site = RHO_std * (288.15 / T_mean_K)
density_correction = RHO_site / RHO_std
print(f"\nAir density at site:        {RHO_site:.3f} kg/m³")
print(f"Density correction factor: {density_correction:.3f}")
print(f"  → Wind turbine output reduced by {(1-density_correction)*100:.1f}% vs ISA standard")
print(f"  (Ninja applies this internally; noted for transparency)")

# ── 2.7 Save processed wind data ─────────────────────────────
ninja.to_csv("data/processed/wind_resource.csv")
print("\nSaved: data/processed/wind_resource.csv")


# ═══════════════════════════════════════════════════════════════
# PART 3 — VISUALISATIONS
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("PART 3: GENERATING FIGURES")
print("=" * 55)

# ── Figure 1: Solar resource overview ────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle(
    "Ada East Microgrid — Solar Resource Assessment\n"
    "PVGIS ERA5 TMY | Coordinates: 5.7833°N, 0.6333°E",
    fontsize=11, fontweight="bold"
)

# Panel A: Full-year GHI time series
ax = axes[0, 0]
ax.fill_between(pvgis.index, pvgis["GHI_Wm2"], alpha=0.6, color="#1B4FD8")
ax.set_title("Annual GHI time series", fontsize=9)
ax.set_ylabel("GHI (W/m²)")
ax.set_xlabel("Month")
ax.grid(True, alpha=0.3, linestyle="--")

# Panel B: Monthly average daily GHI
ax = axes[0, 1]
monthly_ghi = pvgis["GHI_Wm2"].resample("ME").sum() / 1000 / \
              pvgis["GHI_Wm2"].resample("ME").count() * 24
# Simpler: daily sum per month averaged
monthly_avg = daily_ghi.resample("ME").mean()
months = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]
ax.bar(range(12), monthly_avg.values, color="#1B4FD8", alpha=0.8)
ax.axhline(avg_daily, color="#DC2626", linestyle="--", linewidth=1.5,
           label=f"Annual avg: {avg_daily:.2f} kWh/m²/day")
ax.set_xticks(range(12))
ax.set_xticklabels(months, fontsize=7)
ax.set_title("Monthly average daily GHI", fontsize=9)
ax.set_ylabel("GHI (kWh/m²/day)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Panel C: Average 24-hour GHI profile
ax = axes[1, 0]
hourly_ghi_avg = [pvgis["GHI_Wm2"].iloc[h::24].mean() for h in range(24)]
ax.fill_between(range(24), hourly_ghi_avg, alpha=0.7, color="#1B4FD8")
ax.set_title("Average 24-hour irradiance profile", fontsize=9)
ax.set_ylabel("GHI (W/m²)")
ax.set_xlabel("Hour of day")
ax.set_xticks(range(0, 24, 2))
ax.grid(True, alpha=0.3, linestyle="--")

# Panel D: Temperature distribution
ax = axes[1, 1]
ax.hist(pvgis["T2m_C"], bins=30, color="#16A34A", alpha=0.75, edgecolor="white")
ax.axvline(T_stc, color="#DC2626", linestyle="--", linewidth=1.5,
           label=f"STC = {T_stc}°C")
ax.axvline(pvgis["T2m_C"].mean(), color="#1B4FD8", linestyle="--", linewidth=1.5,
           label=f"Mean = {pvgis['T2m_C'].mean():.1f}°C")
ax.set_title("Ambient temperature distribution", fontsize=9)
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Hours per year")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("results/figures/02a_solar_resource.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: results/figures/02a_solar_resource.png")

# ── Figure 2: Wind resource ───────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
fig.suptitle(
    "Ada East Microgrid — Wind Resource Assessment\n"
    "Renewables.ninja MERRA-2 | 50m hub height | 2019",
    fontsize=11, fontweight="bold"
)

if "WS_hub_ms" in ninja.columns:
    # Panel A: Monthly mean wind speed
    ax = axes[0]
    monthly_ws = ninja["WS_hub_ms"].resample("ME").mean()
    ax.bar(range(12), monthly_ws.values, color="#16A34A", alpha=0.8)
    ax.axhline(ninja["WS_hub_ms"].mean(), color="#DC2626",
               linestyle="--", linewidth=1.5,
               label=f"Annual mean: {ninja['WS_hub_ms'].mean():.2f} m/s")
    ax.set_xticks(range(12))
    ax.set_xticklabels(months, fontsize=7)
    ax.set_title("Monthly mean wind speed (50m)", fontsize=9)
    ax.set_ylabel("Wind speed (m/s)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, linestyle="--", axis="y")

    # Panel B: Wind speed frequency distribution (Weibull)
    ax = axes[1]
    ws_vals = ninja["WS_hub_ms"].values
    ax.hist(ws_vals, bins=40, density=True, alpha=0.65,
            color="#16A34A", edgecolor="white", label="Observed")
    # Overlay fitted Weibull PDF
    x = np.linspace(0, ws_vals.max(), 200)
    from scipy.stats import weibull_min
    pdf = weibull_min.pdf(x, shape_k, loc=0, scale=scale_lam)
    ax.plot(x, pdf, color="#1B4FD8", linewidth=2,
            label=f"Weibull k={shape_k:.2f}, λ={scale_lam:.2f}")
    ax.set_title("Wind speed distribution (50m)", fontsize=9)
    ax.set_xlabel("Wind speed (m/s)")
    ax.set_ylabel("Probability density")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, linestyle="--")

# Panel C: Monthly wind capacity factor
ax = axes[2]
monthly_cf = ninja["cf_wind"].resample("ME").mean()
ax.bar(range(12), monthly_cf.values * 100, color="#1B4FD8", alpha=0.8)
ax.axhline(cf_mean * 100, color="#DC2626", linestyle="--", linewidth=1.5,
           label=f"Annual CF: {cf_mean*100:.1f}%")
ax.set_xticks(range(12))
ax.set_xticklabels(months, fontsize=7)
ax.set_title("Monthly wind capacity factor (50m)", fontsize=9)
ax.set_ylabel("Capacity factor (%)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

plt.tight_layout()
plt.savefig("results/figures/02b_wind_resource.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: results/figures/02b_wind_resource.png")

# ── Figure 3: Solar–wind complementarity ─────────────────────
# This is a key engineering plot. It shows whether solar and wind
# peak at different times — if they do, they complement each other
# and reduce battery/diesel requirements.

fig, axes = plt.subplots(2, 1, figsize=(14, 7))
fig.suptitle(
    "Ada East Microgrid — Solar–Wind Complementarity\n"
    "Monthly averages: do the resources offset each other?",
    fontsize=11, fontweight="bold"
)

# Normalise both to 0–1 scale for visual comparison
ghi_norm  = daily_ghi.resample("ME").mean() / daily_ghi.max()
cf_monthly = ninja["cf_wind"].resample("ME").mean()

ax = axes[0]
x = np.arange(12)
width = 0.35
ax.bar(x - width/2, ghi_norm.values,  width, label="Solar GHI (normalised)", color="#1B4FD8", alpha=0.8)
ax.bar(x + width/2, cf_monthly.values, width, label="Wind capacity factor",   color="#16A34A", alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(months, fontsize=8)
ax.set_ylabel("Normalised output / CF")
ax.set_title("Monthly solar vs wind output — are they complementary?", fontsize=9)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Correlation: if correlation is negative, resources complement well
corr = np.corrcoef(ghi_norm.values, cf_monthly.values)[0, 1]
ax.text(0.02, 0.95, f"Pearson correlation: {corr:.2f}",
        transform=ax.transAxes, fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

# Panel B: Average 24-hour profiles on same axis
ax = axes[1]
hourly_cf_avg = [ninja["cf_wind"].iloc[h::24].mean() for h in range(24)]
hourly_ghi_n  = np.array(hourly_ghi_avg) / max(hourly_ghi_avg)
hourly_cf_n   = np.array(hourly_cf_avg) / max(hourly_cf_avg) if max(hourly_cf_avg)>0 else hourly_cf_avg

ax.fill_between(range(24), hourly_ghi_n,  alpha=0.5, color="#1B4FD8", label="Solar (norm.)")
ax.fill_between(range(24), hourly_cf_n,   alpha=0.5, color="#16A34A", label="Wind (norm.)")
ax.set_title("Average 24-hour solar vs wind profile", fontsize=9)
ax.set_xlabel("Hour of day")
ax.set_ylabel("Normalised output")
ax.set_xticks(range(0, 24, 2))
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("results/figures/02c_resource_overlap.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: results/figures/02c_resource_overlap.png")

print("\n" + "=" * 55)
print("PHASE 1 COMPLETE — Resource assessment done.")
print("=" * 55)

# ── DIAGNOSTIC: wind speed cross-check at multiple heights ────
print("\n" + "=" * 55)
print("WIND DIAGNOSTIC — Shear extrapolation table")
print("=" * 55)
print(f"PVGIS ERA5 mean WS at 10m: {pvgis['WS10m_ms'].mean():.3f} m/s")
print(f"Alpha (IEC 61400-1):       {ALPHA}")
print()
print(f"{'Height (m)':<15} {'WS from PVGIS+shear (m/s)':<28} {'Wind power index'}")
print("-" * 58)
for h in [10, 20, 30, 40, 50, 60, 80]:
    ws_h = pvgis["WS10m_ms"].mean() * (h / 10) ** ALPHA
    power_index = (ws_h / pvgis["WS10m_ms"].mean()) ** 3
    print(f"{h:<15} {ws_h:<28.3f} {power_index:.3f}")

print(f"\nRenewables.ninja reported at 50m: {ninja['WS_hub_ms'].mean():.3f} m/s")
print(f"Ratio ninja/pvgis-extrapolated:   "
      f"{ninja['WS_hub_ms'].mean() / (pvgis['WS10m_ms'].mean()*(50/10)**ALPHA):.3f}")

# Monthly wind speed comparison
print(f"\nMonthly mean wind speed at 50m (Ninja MERRA-2):")
monthly_ninja_ws = ninja["WS_hub_ms"].resample("ME").mean()
for i, (month, val) in enumerate(zip(months, monthly_ninja_ws)):
    pvgis_10m_month = pvgis["WS10m_ms"].resample("ME").mean().iloc[i]
    extrapolated = pvgis_10m_month * (50/10)**ALPHA
    print(f"  {month}: Ninja={val:.2f} m/s | PVGIS-extrapolated={extrapolated:.2f} m/s")

    # ═══════════════════════════════════════════════════════════════
# PART 4 — WIND RESOURCE RECONCILIATION
# Use ERA5 (PVGIS) as primary wind basis; MERRA-2 as conservative case
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("PART 4: WIND RECONCILIATION — ERA5 PRIMARY BASIS")
print("=" * 55)

# ── 4.1 Extrapolate ERA5 wind from 10m to 50m ────────────────
# Using power law: v(h) = v_ref * (h/h_ref)^alpha
# IEC 61400-1:2019, Section 6.3, alpha=0.12 coastal flat terrain

ALPHA  = 0.12
H_REF  = 10.0
H_HUB  = 50.0

pvgis["WS50m_ms"] = pvgis["WS10m_ms"] * (H_HUB / H_REF) ** ALPHA

mean_era5_50m  = pvgis["WS50m_ms"].mean()
mean_merra2_50m = ninja["WS_hub_ms"].mean()

print(f"\nERA5  mean WS at 50m (primary):      {mean_era5_50m:.3f} m/s")
print(f"MERRA-2 mean WS at 50m (conservative): {mean_merra2_50m:.3f} m/s")
print(f"Spread (uncertainty range):           "
      f"{mean_merra2_50m:.2f} – {mean_era5_50m:.2f} m/s")

# ── 4.2 Theoretical capacity factor estimate from ERA5 ───────
# Using Weibull distribution fitted to ERA5 50m wind speeds.
# This gives a site-specific CF estimate independent of Ninja's
# turbine simulation, which was based on underestimated MERRA-2 wind.

ws50_vals = pvgis["WS50m_ms"].values

from scipy.stats import weibull_min
shape_k50, loc50, scale_lam50 = weibull_min.fit(
    ws50_vals[ws50_vals > 0.5], floc=0
)

print(f"\nERA5 50m Weibull fit:")
print(f"  Shape k  = {shape_k50:.3f}")
print(f"  Scale λ  = {scale_lam50:.3f} m/s")

# Vestas V80 simplified power curve for CF estimation
# Cut-in: 4 m/s, Rated: 16 m/s, Cut-out: 25 m/s, Rated power: 2000 kW
# We use a cubic approximation between cut-in and rated speed
def vestas_v80_cf(ws):
    """Normalised capacity factor from wind speed (m/s)."""
    ws = np.atleast_1d(ws)
    cf = np.zeros_like(ws, dtype=float)
    # Between cut-in (4) and rated (16): CF scales as (v^3 - v_ci^3)/(v_r^3 - v_ci^3)
    mask_partial = (ws >= 4.0) & (ws < 16.0)
    cf[mask_partial] = (ws[mask_partial]**3 - 4.0**3) / (16.0**3 - 4.0**3)
    cf[ws >= 16.0] = 1.0    # rated power
    cf[ws >= 25.0] = 0.0    # cut-out
    return cf

cf_era5   = vestas_v80_cf(pvgis["WS50m_ms"].values).mean()
cf_merra2 = vestas_v80_cf(ninja["WS_hub_ms"].values).mean()

print(f"\nEstimated annual CF (ERA5 basis):   {cf_era5*100:.1f}%")
print(f"Estimated annual CF (MERRA-2 basis): {cf_merra2*100:.1f}%")
print(f"\nConclusion: Wind CF range = {cf_merra2*100:.0f}% – {cf_era5*100:.0f}%")
print(f"Design basis (ERA5): {cf_era5*100:.0f}%  |  "
      f"Conservative (MERRA-2): {cf_merra2*100:.0f}%")

# ── 4.3 Seasonal wind pattern — critical for dispatch ────────
print(f"\nSeasonal wind pattern (ERA5, 50m):")
print(f"{'Month':<8} {'WS (m/s)':<12} {'CF est.':<12} {'Season'}")
print("-" * 50)
season_map = {
    1:"Dry NE", 2:"Dry NE", 3:"Transition", 4:"Wet SW",
    5:"Wet SW", 6:"Wet SW", 7:"Peak SW", 8:"Peak SW",
    9:"Wet SW", 10:"Transition", 11:"Dry NE", 12:"Dry NE"
}
monthly_era5_ws = pvgis["WS50m_ms"].resample("ME").mean()
for i, (m, ws) in enumerate(zip(months, monthly_era5_ws)):
    cf_m = vestas_v80_cf(np.array([ws]))[0]
    season = season_map[i+1]
    print(f"{m:<8} {ws:<12.2f} {cf_m*100:<12.1f} {season}")

# ── 4.4 Save reconciled wind resource ────────────────────────
# Add ERA5-extrapolated 50m wind to the solar resource file
pvgis["WS50m_ERA5_ms"] = pvgis["WS50m_ms"]
pvgis.to_csv("data/processed/solar_resource.csv")

# Create standalone wind summary for HOMER input
wind_homer = pd.DataFrame({
    "timestamp":          pvgis.index,
    "WS10m_ERA5_ms":      pvgis["WS10m_ms"].values,
    "WS50m_ERA5_ms":      pvgis["WS50m_ms"].values,
    "WS50m_MERRA2_ms":    ninja["WS_hub_ms"].values,
    "cf_wind_MERRA2":     ninja["cf_wind"].values,
})
wind_homer.to_csv("data/processed/wind_resource_reconciled.csv", index=False)
print(f"\nSaved: data/processed/wind_resource_reconciled.csv")

# ── 4.5 Final comparison figure ───────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
fig.suptitle(
    "Wind Resource Reconciliation — ERA5 vs MERRA-2\n"
    "Ada East, Ghana | 50m Hub Height",
    fontsize=11, fontweight="bold"
)

# Monthly comparison
ax = axes[0]
x = np.arange(12)
w = 0.35
monthly_merra2 = ninja["WS_hub_ms"].resample("ME").mean()
ax.bar(x - w/2, monthly_era5_ws.values,   w,
       label=f"ERA5 (primary, mean={mean_era5_50m:.2f} m/s)",
       color="#1B4FD8", alpha=0.85)
ax.bar(x + w/2, monthly_merra2.values, w,
       label=f"MERRA-2 (conservative, mean={mean_merra2_50m:.2f} m/s)",
       color="#DC2626", alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(months, fontsize=8)
ax.set_ylabel("Wind speed (m/s)")
ax.set_title("Monthly mean wind speed at 50m", fontsize=9)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# CF comparison bar
ax = axes[1]
labels = ["ERA5\n(primary)", "MERRA-2\n(conservative)"]
cfs    = [cf_era5 * 100, cf_merra2 * 100]
colors = ["#1B4FD8", "#DC2626"]
bars = ax.bar(labels, cfs, color=colors, alpha=0.85, width=0.4)
for bar, val in zip(bars, cfs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=11,
            fontweight="bold")
ax.set_ylabel("Annual capacity factor (%)")
ax.set_title("Estimated wind CF — design range", fontsize=9)
ax.set_ylim(0, max(cfs) * 1.3)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.axhspan(cfs[1], cfs[0], alpha=0.1, color="#1B4FD8",
           label="Uncertainty range")
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig("results/figures/02d_wind_reconciliation.png", dpi=150, bbox_inches="tight")
plt.show()
print("Saved: results/figures/02d_wind_reconciliation.png")

print("\n" + "=" * 55)
print("PHASE 1 FULLY COMPLETE")
print(f"  Solar PSH:          {avg_daily:.2f} h/day")
print(f"  Wind WS at 50m:     {mean_merra2_50m:.2f} – {mean_era5_50m:.2f} m/s")
print(f"  Wind CF range:      {cf_merra2*100:.0f}% – {cf_era5*100:.0f}%")
print(f"  PV derating:        {(1-mean_derate)*100:.1f}%")
print(f"  Air density factor: {density_correction:.3f}")
print("=" * 55)

# ── DIAGNOSTIC: Power curve analysis ─────────────────────────
import numpy as np
import matplotlib.pyplot as plt

print("=" * 55)
print("POWER CURVE DIAGNOSTIC — Vestas V80 vs site wind")
print("=" * 55)

# Vestas V80 2000 kW power curve parameters
v_cutin  = 4.0   # m/s — below this: zero output
v_rated  = 16.0  # m/s — above this: full 2000 kW
v_cutout = 25.0  # m/s — above this: emergency shutdown

mean_ws_era5   = 6.149  # m/s at 50m
mean_ws_merra2 = 4.431  # m/s at 50m

print(f"\nVestas V80 cut-in speed:  {v_cutin} m/s")
print(f"Vestas V80 rated speed:   {v_rated} m/s")
print(f"Site mean WS (ERA5 50m):  {mean_ws_era5:.2f} m/s")
print(f"Site mean WS (MERRA2 50m):{mean_ws_merra2:.2f} m/s")

# The core problem: rated speed is 16 m/s but site mean is 6 m/s
# This turbine is designed for HIGH-WIND sites (North Sea, etc.)
# At 6 m/s mean, it barely moves above cut-in

print(f"\nAt mean wind speed of {mean_ws_era5:.1f} m/s:")
cf_at_mean = (mean_ws_era5**3 - v_cutin**3) / (v_rated**3 - v_cutin**3)
print(f"  CF from cubic law: {cf_at_mean*100:.1f}%")
print(f"  This turbine needs {v_rated} m/s to reach rated power")
print(f"  Site wind is {v_rated/mean_ws_era5:.1f}x BELOW rated speed")

# Compare: what turbine is actually designed for this wind regime?
# IEC Wind Class III: mean WS 6.0–7.5 m/s — LOW WIND turbines
# Appropriate: Enercon E33 (330kW), rated at ~13 m/s
# Or small turbines: Bergey Excel 10 (10kW), rated at ~11 m/s

print(f"\n{'─'*50}")
print(f"APPROPRIATE TURBINE COMPARISON")
print(f"{'─'*50}")
turbines = [
    ("Vestas V80 2000kW",   4.0, 16.0, 25.0, "IEC Class I/II (high wind)"),
    ("Enercon E33 330kW",   2.5, 13.0, 28.0, "IEC Class II/III (medium wind)"),
    ("Vestas V27 225kW",    3.5, 14.0, 20.0, "IEC Class II/III"),
    ("Bergey Excel 15 15kW",2.5, 11.0, None, "Small/IEC Class III (low wind)"),
    ("Generic 50kW IEC-III",2.5, 11.0, 25.0, "IEC Class III (low wind)"),
]

print(f"{'Turbine':<28} {'Cut-in':<10} {'Rated':<10} {'CF@6.15m/s':<14} {'Class'}")
print("-" * 80)
for name, vci, vr, vco, cls in turbines:
    if mean_ws_era5 < vci:
        cf = 0.0
    elif mean_ws_era5 >= vr:
        cf = 1.0
    else:
        cf = (mean_ws_era5**3 - vci**3) / (vr**3 - vci**3)
    print(f"{name:<28} {vci:<10.1f} {vr:<10.1f} {cf*100:<14.1f} {cls}")

# The real issue: we need IEC Class III turbines for 6 m/s mean wind
# Rated speed of 11-13 m/s vs V80's 16 m/s makes an enormous difference
print(f"\nKey insight:")
print(f"  V80 at 6.15 m/s: operating at {6.15/16*100:.0f}% of rated speed")
print(f"  E33 at 6.15 m/s: operating at {6.15/13*100:.0f}% of rated speed")
print(f"  Power scales as v^3, so position on power curve matters enormously")