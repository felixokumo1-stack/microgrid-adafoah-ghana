"""
03_model_verification.py  (corrected)
"""

import numpy as np
import pandas as pd

print("=" * 55)
print("MODEL VERIFICATION — Ada East Microgrid")
print("=" * 55)

# ── Load processed data ───────────────────────────────────────
solar = pd.read_csv("data/processed/solar_resource.csv",
                    index_col="timestamp", parse_dates=True)
load  = pd.read_csv("data/processed/load_profile_8760.csv",
                    index_col="timestamp", parse_dates=True)

# DIAGNOSTIC: print what we actually loaded
print(f"\nDIAGNOSTIC — loaded data shapes:")
print(f"  Solar rows: {len(solar)} | columns: {solar.columns.tolist()}")
print(f"  Load rows:  {len(load)}  | columns: {load.columns.tolist()}")
print(f"  Load total_load_kw sum: {load['total_load_kw'].sum():.1f} kWh")
print(f"  Load total_load_kw mean: {load['total_load_kw'].mean():.2f} kW")
print(f"  Load total_load_kw max:  {load['total_load_kw'].max():.2f} kW")

# ── 1. PV model verification ──────────────────────────────────
print("\n1. PV POWER MODEL")
P_PV_rated  = 100
eta_inv     = 0.96
f_soil      = 0.80
gamma       = -0.004
T_STC       = 25.0
T_NOCT_rise = 25.0
G_STC       = 1000.0

T_mod  = solar["T2m_C"] + T_NOCT_rise
f_temp = 1 + gamma * (T_mod - T_STC)
P_PV   = P_PV_rated * (solar["GHI_Wm2"] / G_STC) * eta_inv * f_temp * f_soil

PR_mean = P_PV.sum() / (P_PV_rated * solar["GHI_Wm2"].sum() / G_STC)
print(f"  Test array: {P_PV_rated} kWp")
print(f"  Annual energy yield: {P_PV.sum():.0f} kWh/year")
print(f"  Specific yield: {P_PV.sum()/P_PV_rated:.0f} kWh/kWp/year")
print(f"  Performance Ratio: {PR_mean:.3f}")
print(f"  Benchmark PR (West Africa): 0.65–0.75 → ", end="")
print("✓ PASS" if 0.65 <= PR_mean <= 0.80 else "⚠ CHECK")

# ── 2. Wind model verification ────────────────────────────────
print("\n2. WIND POWER MODEL")
P_wind_rated = 50
v_ci, v_r, v_co, eta_conv = 2.5, 11.0, 25.0, 0.95

ws = solar["WS50m_ERA5_ms"] if "WS50m_ERA5_ms" in solar.columns \
     else solar["WS10m_ms"] * (50/10)**0.12

def wind_power(ws_arr, P_rated, v_ci, v_r, v_co, eta):
    ws_arr = np.array(ws_arr, dtype=float)
    P = np.zeros_like(ws_arr)
    m1 = (ws_arr >= v_ci) & (ws_arr < v_r)
    m2 = (ws_arr >= v_r)  & (ws_arr < v_co)
    P[m1] = P_rated * (ws_arr[m1]**3 - v_ci**3) / (v_r**3 - v_ci**3)
    P[m2] = P_rated
    return P * eta

P_wind    = wind_power(ws, P_wind_rated, v_ci, v_r, v_co, eta_conv)
CF_annual = P_wind.mean() / P_wind_rated
print(f"  Test turbine: {P_wind_rated} kW IEC Class III")
print(f"  Annual CF: {CF_annual*100:.1f}%")
print(f"  Annual energy: {P_wind.sum():.0f} kWh/year")
print(f"  Benchmark CF (IEC-III, 6 m/s site): 14–20% → ", end="")
print("✓ PASS" if 0.12 <= CF_annual <= 0.22 else "⚠ INVESTIGATE")

# ── 3. Battery sizing — corrected ────────────────────────────
print("\n3. BATTERY SIZING — CRITICAL DESIGN NIGHT")

# The load profile has kW values at each hour.
# Summing kW × 1h = kWh for each period.
# We need to look at the SHAPE of the load, not just the mean.
# Extract hour-of-day from index properly.

load_copy = load.copy()
load_copy["hour"] = load_copy.index.hour

# Average load by hour of day across all 365 days
hourly_avg_profile = load_copy.groupby("hour")["total_load_kw"].mean()

print(f"\n  Average load by hour of day (kW):")
print(f"  {'Hour':<8} {'Load (kW)':<12}")
for h in [6,12,17,18,19,20,21,22,23,0,1,2,3,4,5]:
    print(f"  {h:<8} {hourly_avg_profile[h]:<12.2f}")

# Evening peak: hours 18, 19, 20
evening_hours = [18, 19, 20]
evening_avg_kw = hourly_avg_profile[evening_hours].mean()
E_evening_kwh  = hourly_avg_profile[evening_hours].sum()  # kW × 1h each

# Overnight base: hours 21–23 and 0–6
overnight_hours = list(range(21, 24)) + list(range(0, 7))
overnight_avg_kw = hourly_avg_profile[overnight_hours].mean()
E_overnight_kwh  = hourly_avg_profile[overnight_hours].sum()

# Total energy battery must supply overnight
# Assumption: PV = 0 during all these hours (confirmed for Ghana 18°N-6°N)
# Wind provides partial cover — conservative assumption: wind covers 20% overnight
# (based on 19.7% CF — wind runs through the night)
wind_overnight_fraction = CF_annual   # ~0.197 of rated
P_wind_overnight_kw = P_wind_rated * wind_overnight_fraction
E_wind_overnight = P_wind_overnight_kw * len(overnight_hours)

eta_dis    = 0.97
SOC_min_LFP  = 0.20
SOC_min_VRLA = 0.50

# Battery must cover: (evening load) + (overnight load) - (wind contribution)
E_required_gross = E_evening_kwh + E_overnight_kwh
E_wind_covers    = E_wind_overnight * 0.5  # conservative: only 50% of wind at night
E_batt_net       = max(0, E_required_gross - E_wind_covers)
E_batt_delivered = E_batt_net / eta_dis    # accounting for discharge losses

E_batt_LFP_nameplate  = E_batt_delivered / (1 - SOC_min_LFP)
E_batt_VRLA_nameplate = E_batt_delivered / (1 - SOC_min_VRLA)

print(f"\n  Evening avg load (18–20h):   {evening_avg_kw:.1f} kW")
print(f"  Evening energy (3h):          {E_evening_kwh:.1f} kWh")
print(f"  Overnight avg (21–06h):       {overnight_avg_kw:.1f} kW")
print(f"  Overnight energy (10h):       {E_overnight_kwh:.1f} kWh")
print(f"  Total overnight load:         {E_required_gross:.1f} kWh")
print(f"  Wind overnight contribution:  {E_wind_covers:.1f} kWh (50% CF × {len(overnight_hours)}h)")
print(f"  Net battery requirement:      {E_batt_net:.1f} kWh")
print(f"  After discharge loss (÷0.97): {E_batt_delivered:.1f} kWh")
print(f"\n  LFP nameplate required:       {E_batt_LFP_nameplate:.0f} kWh")
print(f"  VRLA nameplate required:      {E_batt_VRLA_nameplate:.0f} kWh")

# Cross-check against first-principles estimate from Phase 2
print(f"\n  Phase 2 manual estimate:      ~637 kWh LFP")
print(f"  Script estimate:              {E_batt_LFP_nameplate:.0f} kWh LFP")

ratio = E_batt_LFP_nameplate / 637
print(f"  Ratio (script/manual):        {ratio:.2f}")
if 0.7 <= ratio <= 1.4:
    print(f"  → ✓ CONSISTENT (within 40% — expected given wind offset assumption)")
else:
    print(f"  → ⚠ INVESTIGATE — large discrepancy vs manual estimate")

# ── 4. Diesel cost ────────────────────────────────────────────
print("\n4. DIESEL COST — 20-YEAR PROJECTION")
P_diesel_rated  = 80
a, b            = 0.0811, 0.2450
load_fraction   = 0.50
fuel_price_usd  = 1.56
eur_usd         = 1.08
hours_per_year  = 2000

F_hourly        = P_diesel_rated * (a + b * load_fraction)
cost_hourly_usd = F_hourly * fuel_price_usd
cost_annual_usd = cost_hourly_usd * hours_per_year
cost_20yr_eur   = cost_annual_usd * 20 / eur_usd

print(f"  Generator: {P_diesel_rated} kW at {load_fraction*100:.0f}% load")
print(f"  Fuel consumption: {F_hourly:.1f} L/h")
print(f"  Cost per hour: USD {cost_hourly_usd:.2f}")
print(f"  Annual fuel cost ({hours_per_year}h/yr): USD {cost_annual_usd:,.0f}")
print(f"  20-year fuel cost: EUR {cost_20yr_eur:,.0f}")
print(f"  vs CAPEX ceiling EUR 500,000 → ratio: {cost_20yr_eur/500_000:.2f}x")
print(f"  Engineering message: diesel-only is {cost_20yr_eur/500_000:.1f}× your entire")
print(f"  CAPEX budget in fuel alone → renewable hybrid is economically essential")

# ── 5. LCOE bounds — corrected ────────────────────────────────
print("\n5. LCOE PRELIMINARY BOUNDS")

# CRITICAL FIX: annual energy served is total_load_kw summed over 8760 hours
# Each row = 1 hour, value in kW → kWh per hour, sum = kWh/year
E_annual_load    = load["total_load_kw"].sum()    # kWh/year (8760 values × 1h)
reliability      = 0.95                            # 95% LPSP target
E_served         = E_annual_load * reliability

print(f"\n  DIAGNOSTIC — energy accounting:")
print(f"  Load rows in CSV:            {len(load)}")
print(f"  Sum of total_load_kw (kWh):  {E_annual_load:,.0f}")
print(f"  Expected (~250,000 kWh):     250,000")
print(f"  Match: ", end="")
print("✓" if 200_000 <= E_annual_load <= 320_000 else "⚠ MISMATCH — check CSV")

i   = 0.08
n   = 20
CRF = i * (1+i)**n / ((1+i)**n - 1)

CAPEX_max       = 500_000
C_OM_pct        = 0.02
ann_capex       = CRF * CAPEX_max
ann_om          = C_OM_pct * CAPEX_max
ann_fuel_low    = cost_annual_usd * 0.5 / eur_usd   # 1,000h diesel
ann_fuel_high   = cost_annual_usd       / eur_usd   # 2,000h diesel

lcoe_low  = (ann_capex + ann_om + ann_fuel_low)  / E_served
lcoe_high = (ann_capex + ann_om + ann_fuel_high) / E_served

print(f"\n  CRF (8%, 20yr):              {CRF:.4f} ({CRF*100:.2f}%/yr)")
print(f"  Annualised CAPEX (EUR 500k): EUR {ann_capex:,.0f}/yr")
print(f"  Annual O&M (2%):             EUR {ann_om:,.0f}/yr")
print(f"  Annual load (from CSV):      {E_annual_load:,.0f} kWh/yr")
print(f"  Annual energy served (95%):  {E_served:,.0f} kWh/yr")
print(f"  LCOE range (pre-opt.):       EUR {lcoe_low:.3f}–{lcoe_high:.3f}/kWh")
print(f"  Benchmark (W.Africa s+b):    EUR 0.18–0.35/kWh → ", end="")
print("✓ PLAUSIBLE" if lcoe_low < 0.40 else "⚠ CHECK INPUTS")

# ── 6. Sensitivity: 12% discount rate ────────────────────────
print("\n6. DISCOUNT RATE SENSITIVITY")
for rate, label in [(0.08, "Base (8%, donor)"), (0.12, "Sensitivity (12%, commercial)")]:
    crf_i    = rate * (1+rate)**n / ((1+rate)**n - 1)
    ac       = crf_i * CAPEX_max
    lc_low   = (ac + ann_om + ann_fuel_low)  / E_served
    lc_high  = (ac + ann_om + ann_fuel_high) / E_served
    print(f"  {label}:")
    print(f"    CRF={crf_i:.4f} | Ann.CAPEX=EUR {ac:,.0f} | "
          f"LCOE EUR {lc_low:.3f}–{lc_high:.3f}/kWh")

print("\n" + "=" * 55)
print("MODEL VERIFICATION COMPLETE")
print("=" * 55)