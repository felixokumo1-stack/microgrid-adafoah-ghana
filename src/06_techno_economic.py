"""
06_techno_economic.py
=====================
Techno-economic analysis for Ada East Hybrid Microgrid.
Calculates LCOE, NPV, payback period and sensitivity analysis
for all three configurations.

Method: Annualised Life Cycle Cost (ALCC) method
Reference: IEC 62257-9-1; IRENA (2023) Renewable Power Generation Costs;
           HOMER Pro NPC methodology

Author: Felix Okumo
Date: April 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

os.makedirs("results", exist_ok=True)
os.makedirs("results/figures", exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 1. PROJECT PARAMETERS
# ═══════════════════════════════════════════════════════════════

N_YEARS       = 20          # project lifetime (years)
DISCOUNT_RATE = 0.08        # base case: social discount rate, donor-funded
EUR_USD       = 1.08        # exchange rate (April 2026)
FUEL_PRICE    = 1.44        # EUR/L (USD 1.56 / 1.08)
INFLATION     = 0.025       # annual fuel price escalation (2.5%)

# Capital Recovery Factor — annualises upfront CAPEX over project life
# CRF = i(1+i)^n / [(1+i)^n - 1]
def CRF(i, n):
    return i * (1+i)**n / ((1+i)**n - 1)

# Sinking Fund Factor — annualises a future replacement cost
# SFF = i / [(1+i)^m - 1]  where m = years until replacement
def SFF(i, m):
    return i / ((1+i)**m - 1)

# Present Worth Factor — discounts a future cost to today
def PWF(i, m):
    return 1 / (1+i)**m

crf_base = CRF(DISCOUNT_RATE, N_YEARS)
print(f"CRF (8%, 20yr): {crf_base:.4f} ({crf_base*100:.2f}%/yr)")

# ═══════════════════════════════════════════════════════════════
# 2. COMPONENT COSTS
# ═══════════════════════════════════════════════════════════════
# All costs in EUR. Source: docs/assumptions.md Phase 3 cost basis.

COSTS = {
    "pv_capital_per_kw":      1200,   # EUR/kWp installed
    "pv_replacement_per_kw":  1000,   # EUR/kWp (modules + labour)
    "pv_om_per_kw_yr":          12,   # EUR/kWp/yr
    "pv_lifetime_yr":           25,   # > project life → no replacement needed

    "wind_capital_per_kw":    1500,   # EUR/kW installed (EUR 75,000 / 50 kW)
    "wind_replacement_per_kw":1300,   # EUR/kW
    "wind_om_per_kw_yr":        60,   # EUR/kW/yr (4% of EUR 1,500)
    "wind_lifetime_yr":         20,   # = project life → no replacement

    "batt_capital_per_kwh":    350,   # EUR/kWh (EUR 35,000 / 100 kWh)
    "batt_replacement_per_kwh":280,   # EUR/kWh (cost decline by year 14)
    "batt_om_per_kwh_yr":        4,   # EUR/kWh/yr (EUR 400 / 100 kWh)
    "batt_lifetime_yr":         15,   # replacement at year 15

    "gen_capital_per_kw":      700,   # EUR/kW installed
    "gen_replacement_per_kw":  600,   # EUR/kW
    "gen_om_per_hr":          0.08,   # EUR/operating hour
    "gen_lifetime_hr":       15000,   # hours (overhaul trigger)

    "conv_capital_per_kw":     350,   # EUR/kW
    "conv_replacement_per_kw": 300,   # EUR/kW
    "conv_om_per_kw_yr":        10,   # EUR/kW/yr
    "conv_lifetime_yr":         15,   # replacement at year 15
}

# ═══════════════════════════════════════════════════════════════
# 3. SYSTEM SIZING — Three configurations
# ═══════════════════════════════════════════════════════════════

CONFIGS = {
    "A": {
        "name": "Config A — PV + Battery + Diesel",
        "pv_kw":    200,
        "wind_kw":    0,
        "batt_kwh": 400,
        "gen_kw":    60,
        "conv_kw":   70,
        "annual_fuel_L":   11461,   # from HOMER
        "gen_hours_yr":      400,   # estimated from HOMER (not explicit in CSV)
        "energy_served_kwh": 249660,
        "homer_lcoe":        0.287,
        "homer_npc":         703858,
        "ren_fraction":      0.865,
    },
    "B": {
        "name": "Config B — PV + Wind + Battery + Diesel (OPTIMAL)",
        "pv_kw":    150,
        "wind_kw":   50,
        "batt_kwh": 300,
        "gen_kw":    60,
        "conv_kw":   60,
        "annual_fuel_L":    2968,   # from HOMER
        "gen_hours_yr":      307,   # from HOMER
        "energy_served_kwh": 249660,
        "homer_lcoe":        0.227,
        "homer_npc":         555700,
        "ren_fraction":      0.976,
    },
    "C": {
        "name": "Config C — PV + Wind×2 + Battery + Diesel",
        "pv_kw":    120,
        "wind_kw":  100,
        "batt_kwh": 200,
        "gen_kw":    60,
        "conv_kw":   60,
        "annual_fuel_L":    2580,   # from HOMER
        "gen_hours_yr":      267,   # from HOMER CSV row for 120/2/60/2/60/LF
        "energy_served_kwh": 249660,
        "homer_lcoe":        0.233,
        "homer_npc":         570385,
        "ren_fraction":      0.979,
    },
}

# ═══════════════════════════════════════════════════════════════
# 4. LCOE CALCULATION FUNCTION
# ═══════════════════════════════════════════════════════════════

def calculate_lcoe(cfg, i=DISCOUNT_RATE, fuel_price=FUEL_PRICE):
    """
    Calculate LCOE using Annualised Life Cycle Cost method.
    LCOE = (CRF×CAPEX + C_OM + C_fuel + C_replacement) / E_served

    Returns dict of cost components and LCOE.
    """
    crf = CRF(i, N_YEARS)
    c   = COSTS
    n   = N_YEARS

    # ── CAPEX ─────────────────────────────────────────────
    capex_pv   = cfg["pv_kw"]   * c["pv_capital_per_kw"]
    capex_wind = cfg["wind_kw"] * c["wind_capital_per_kw"]
    capex_batt = cfg["batt_kwh"]* c["batt_capital_per_kwh"]
    capex_gen  = cfg["gen_kw"]  * c["gen_capital_per_kw"]
    capex_conv = cfg["conv_kw"] * c["conv_capital_per_kw"]
    capex_total = capex_pv + capex_wind + capex_batt + capex_gen + capex_conv

    # ── Annual O&M ─────────────────────────────────────────
    om_pv   = cfg["pv_kw"]   * c["pv_om_per_kw_yr"]
    om_wind = cfg["wind_kw"] * c["wind_om_per_kw_yr"]
    om_batt = cfg["batt_kwh"]* c["batt_om_per_kwh_yr"]
    om_gen  = cfg["gen_hours_yr"] * c["gen_om_per_hr"]
    om_conv = cfg["conv_kw"] * c["conv_om_per_kw_yr"]
    om_total = om_pv + om_wind + om_batt + om_gen + om_conv

    # ── Annual fuel cost (with inflation) ─────────────────
    # Present worth of escalating fuel costs over N years
    # PW = Σ [F₀(1+e)^t / (1+i)^t] for t=1..N
    # = F₀ × [(1-(1+e)^N/(1+i)^N)] / (i-e)  if i≠e
    F0 = cfg["annual_fuel_L"] * fuel_price   # EUR year 1
    if abs(i - INFLATION) < 1e-6:
        pw_fuel = F0 * N_YEARS / (1 + i)
    else:
        pw_fuel = F0 * (1 - ((1+INFLATION)/(1+i))**N_YEARS) / (i - INFLATION)
    ann_fuel = pw_fuel * crf   # annualised fuel cost

    # ── Replacement costs (sinking fund method) ───────────
    # Battery replacement at year 15
    repl_batt_yr = c["batt_lifetime_yr"]
    if repl_batt_yr < N_YEARS:
        repl_batt_cost = cfg["batt_kwh"] * c["batt_replacement_per_kwh"]
        ann_repl_batt  = repl_batt_cost * SFF(i, repl_batt_yr)
    else:
        ann_repl_batt = 0.0

    # Converter replacement at year 15
    repl_conv_yr = c["conv_lifetime_yr"]
    if repl_conv_yr < N_YEARS:
        repl_conv_cost = cfg["conv_kw"] * c["conv_replacement_per_kw"]
        ann_repl_conv  = repl_conv_cost * SFF(i, repl_conv_yr)
    else:
        ann_repl_conv = 0.0

    # Generator replacement (based on hours)
    # Hours until overhaul: 15,000h / gen_hours_yr
    gen_replace_yr = c["gen_lifetime_hr"] / max(cfg["gen_hours_yr"], 1)
    if gen_replace_yr < N_YEARS:
        repl_gen_cost = cfg["gen_kw"] * c["gen_replacement_per_kw"]
        ann_repl_gen  = repl_gen_cost * SFF(i, gen_replace_yr)
    else:
        ann_repl_gen = 0.0

    ann_repl_total = ann_repl_batt + ann_repl_conv + ann_repl_gen

    # ── Salvage value (end of project) ────────────────────
    # Linear depreciation: salvage = replacement_cost × (remaining_life/total_life)
    # Battery: replaced at yr 15, has 5 yrs remaining at yr 20
    salvage_batt = (cfg["batt_kwh"] * c["batt_replacement_per_kwh"]) \
                   * (5/c["batt_lifetime_yr"]) * PWF(i, N_YEARS)
    # PV: 25yr life, 20yr project → 5yr remaining
    salvage_pv   = (cfg["pv_kw"] * c["pv_replacement_per_kw"]) \
                   * (5/c["pv_lifetime_yr"]) * PWF(i, N_YEARS)
    ann_salvage  = (salvage_batt + salvage_pv) * crf

    # ── Total annualised cost ──────────────────────────────
    ann_capex    = crf * capex_total
    ann_total    = ann_capex + om_total + ann_fuel + ann_repl_total \
                   - ann_salvage

    # ── LCOE ──────────────────────────────────────────────
    lcoe = ann_total / cfg["energy_served_kwh"]

    return {
        "capex_total":    capex_total,
        "capex_pv":       capex_pv,
        "capex_wind":     capex_wind,
        "capex_batt":     capex_batt,
        "capex_gen":      capex_gen,
        "capex_conv":     capex_conv,
        "ann_capex":      ann_capex,
        "ann_om":         om_total,
        "ann_fuel":       ann_fuel,
        "ann_repl":       ann_repl_total,
        "ann_salvage":    ann_salvage,
        "ann_total":      ann_total,
        "lcoe":           lcoe,
        "gen_replace_yr": gen_replace_yr,
    }

# ═══════════════════════════════════════════════════════════════
# 5. CALCULATE AND PRINT RESULTS
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*65)
print("TECHNO-ECONOMIC ANALYSIS — Ada East Hybrid Microgrid")
print("="*65)

results = {}
for cfg_id, cfg in CONFIGS.items():
    r = calculate_lcoe(cfg)
    results[cfg_id] = r

    print(f"\n{'─'*65}")
    print(f"{cfg['name']}")
    print(f"{'─'*65}")
    print(f"  CAPEX breakdown:")
    print(f"    PV ({cfg['pv_kw']} kWp):       EUR {r['capex_pv']:>10,.0f}")
    if cfg['wind_kw'] > 0:
        print(f"    Wind ({cfg['wind_kw']} kW):      EUR {r['capex_wind']:>10,.0f}")
    print(f"    Battery ({cfg['batt_kwh']} kWh):  EUR {r['capex_batt']:>10,.0f}")
    print(f"    Generator ({cfg['gen_kw']} kW):  EUR {r['capex_gen']:>10,.0f}")
    print(f"    Converter ({cfg['conv_kw']} kW): EUR {r['capex_conv']:>10,.0f}")
    print(f"    TOTAL CAPEX:           EUR {r['capex_total']:>10,.0f}")
    print(f"\n  Annualised costs (EUR/yr):")
    print(f"    Capital (CRF×CAPEX):       {r['ann_capex']:>10,.0f}")
    print(f"    O&M:                       {r['ann_om']:>10,.0f}")
    print(f"    Fuel (escalated PW):       {r['ann_fuel']:>10,.0f}")
    print(f"    Replacements (sinking):    {r['ann_repl']:>10,.0f}")
    print(f"    Salvage (deduction):      -{r['ann_salvage']:>10,.0f}")
    print(f"    TOTAL ANNUAL COST:         {r['ann_total']:>10,.0f}")
    print(f"\n  LCOE (Python):             EUR {r['lcoe']:.4f}/kWh")
    print(f"  LCOE (HOMER reference):    EUR {cfg['homer_lcoe']:.4f}/kWh")
    print(f"  Discrepancy:               {(r['lcoe']-cfg['homer_lcoe'])/cfg['homer_lcoe']*100:+.1f}%")
    print(f"  Generator overhaul year:       {r['gen_replace_yr']:.1f}")

# ═══════════════════════════════════════════════════════════════
# 6. COMPARATIVE SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print(f"COMPARATIVE SUMMARY")
print(f"{'='*65}")
print(f"{'Metric':<30} {'Config A':>12} {'Config B':>12} {'Config C':>12}")
print(f"{'─'*65}")

metrics = [
    ("CAPEX (EUR)",          "capex_total",    "€{:,.0f}"),
    ("Ann. capital cost",    "ann_capex",      "€{:,.0f}"),
    ("Ann. O&M",             "ann_om",         "€{:,.0f}"),
    ("Ann. fuel cost",       "ann_fuel",       "€{:,.0f}"),
    ("Ann. replacement",     "ann_repl",       "€{:,.0f}"),
    ("LCOE (EUR/kWh)",       "lcoe",           "€{:.4f}"),
]

for label, key, fmt in metrics:
    vals = [fmt.format(results[c][key]) for c in ["A","B","C"]]
    print(f"{label:<30} {vals[0]:>12} {vals[1]:>12} {vals[2]:>12}")

print(f"\n{'Renewable fraction':<30} "
      f"{'86.5%':>12} {'97.6%':>12} {'97.9%':>12}")
print(f"{'Annual fuel (L/yr)':<30} "
      f"{11461:>12,} {2968:>12,} {2580:>12,}")
print(f"{'HOMER LCOE (EUR/kWh)':<30} "
      f"{'€0.2870':>12} {'€0.2267':>12} {'€0.2330':>12}")

# ═══════════════════════════════════════════════════════════════
# 7. NPV vs DIESEL BASELINE
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print(f"NPV ANALYSIS vs DIESEL-ONLY BASELINE")
print(f"{'='*65}")

# Diesel-only baseline: generator + fuel only, no PV/wind/battery
DIESEL_ONLY = {
    "gen_kw":        60,
    "annual_fuel_L": 249660 / 2.8,   # L/yr — realistic diesel system efficiency
                                       # 2.8 kWh/L accounts for part-load operation
                                       # and distribution losses (ESMAP 2019)
    "gen_hours_yr":  8760 * 0.85,    # 85% availability for primary diesel
    "energy_served_kwh": 249660 * 0.95,
    "wind_kw": 0, "pv_kw": 0, "batt_kwh": 0, "conv_kw": 0,
}
r_diesel = calculate_lcoe(DIESEL_ONLY)

print(f"\n  Diesel-only baseline:")
print(f"    CAPEX:               EUR {DIESEL_ONLY['gen_kw']*COSTS['gen_capital_per_kw']:>8,.0f}")
print(f"    Annual fuel:         EUR {DIESEL_ONLY['annual_fuel_L']*FUEL_PRICE:>8,.0f}/yr")
print(f"    LCOE (Python):       EUR {r_diesel['lcoe']:.4f}/kWh")
print(f"    LCOE (ESMAP range):  EUR 0.3500–0.5500/kWh")

for cfg_id in ["A","B","C"]:
    cfg  = CONFIGS[cfg_id]
    r    = results[cfg_id]
    ann_saving = r_diesel["ann_total"] - r["ann_total"]
    npv_saving = ann_saving / CRF(DISCOUNT_RATE, N_YEARS)
    lcoe_reduction = (r_diesel["lcoe"] - r["lcoe"]) / r_diesel["lcoe"] * 100
    print(f"\n  Config {cfg_id} vs diesel-only:")
    print(f"    Annual cost saving:  EUR {ann_saving:>8,.0f}/yr")
    print(f"    NPV of savings:      EUR {npv_saving:>8,.0f}")
    print(f"    LCOE reduction:      {lcoe_reduction:.1f}%")
    payback = r["capex_total"] / max(ann_saving, 1)
    print(f"    Simple payback:      {payback:.1f} years")

# ═══════════════════════════════════════════════════════
# 8. SENSITIVITY ANALYSIS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print(f"SENSITIVITY ANALYSIS — Config B (optimal)")
print(f"{'='*65}")

base_lcoe_B = results["B"]["lcoe"]
cfg_B = CONFIGS["B"]

sensitivity_params = {
    "Discount rate":    ("discount", [0.06, 0.08, 0.10, 0.12, 0.15]),
    "Diesel price (EUR/L)": ("fuel",  [0.90, 1.10, 1.44, 1.70, 2.00]),
    "Battery cost (EUR/kWh)": ("batt", [250,  300,  350,  400,  450]),
    "PV cost (EUR/kW)":   ("pv",    [900, 1050, 1200, 1350, 1500]),
    "Annual fuel (L/yr)": ("fuel_vol",[1500,2000,2968,4000,5000]),
}

sens_results = {}
for param_name, (param_type, values) in sensitivity_params.items():
    lcoe_vals = []
    for v in values:
        if param_type == "discount":
            r = calculate_lcoe(cfg_B, i=v)
        elif param_type == "fuel":
            r = calculate_lcoe(cfg_B, fuel_price=v)
        elif param_type == "batt":
            orig = COSTS["batt_capital_per_kwh"]
            COSTS["batt_capital_per_kwh"] = v
            r = calculate_lcoe(cfg_B)
            COSTS["batt_capital_per_kwh"] = orig
        elif param_type == "pv":
            orig = COSTS["pv_capital_per_kw"]
            COSTS["pv_capital_per_kw"] = v
            r = calculate_lcoe(cfg_B)
            COSTS["pv_capital_per_kw"] = orig
        elif param_type == "fuel_vol":
            cfg_mod = dict(cfg_B)
            cfg_mod["annual_fuel_L"] = v
            r = calculate_lcoe(cfg_mod)
        lcoe_vals.append(r["lcoe"])
    sens_results[param_name] = (values, lcoe_vals)
    print(f"\n  {param_name}:")
    for v, l in zip(values, lcoe_vals):
        marker = " ← base" if abs(l - base_lcoe_B) < 0.001 else ""
        print(f"    {v:>10} → LCOE EUR {l:.4f}/kWh{marker}")

# ═══════════════════════════════════════════════════════════════
# 9. SAVE RESULTS TO CSV
# ═══════════════════════════════════════════════════════════════
summary_rows = []
for cfg_id, cfg in CONFIGS.items():
    r = results[cfg_id]
    summary_rows.append({
        "Config":             cfg_id,
        "Description":        cfg["name"],
        "PV_kWp":             cfg["pv_kw"],
        "Wind_kW":            cfg["wind_kw"],
        "Battery_kWh":        cfg["batt_kwh"],
        "Generator_kW":       cfg["gen_kw"],
        "CAPEX_EUR":          r["capex_total"],
        "Ann_Capital_EUR":    round(r["ann_capex"],   0),
        "Ann_OM_EUR":         round(r["ann_om"],      0),
        "Ann_Fuel_EUR":       round(r["ann_fuel"],    0),
        "Ann_Replacement_EUR":round(r["ann_repl"],    0),
        "Ann_Total_EUR":      round(r["ann_total"],   0),
        "LCOE_Python_EUR_kWh":round(r["lcoe"],        4),
        "LCOE_HOMER_EUR_kWh": cfg["homer_lcoe"],
        "Ren_Fraction_pct":   cfg["ren_fraction"]*100,
        "Annual_Fuel_L":      cfg["annual_fuel_L"],
        "HOMER_NPC_EUR":      cfg["homer_npc"],
    })

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv("results/techno_economic_summary.csv", index=False)
print(f"\nSaved: results/techno_economic_summary.csv")

# ═══════════════════════════════════════════════════════════════
# 10. VISUALISATIONS
# ═══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 12))
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.35)
fig.suptitle(
    "Ada East Microgrid — Techno-Economic Analysis\n"
    "Three-Configuration Comparison | 8% Discount Rate | 20-year Project Life",
    fontsize=12, fontweight="bold"
)

configs_list = ["A", "B", "C"]
config_labels = ["Config A\nPV+Batt+Diesel",
                 "Config B\nPV+Wind+Batt+Diesel",
                 "Config C\nPV+Wind×2+Batt+Diesel"]
colors_main  = ["#DC2626", "#1B4FD8", "#16A34A"]

# Panel 1: LCOE comparison — stacked bar by cost component
ax1 = fig.add_subplot(gs[0, 0])
cap_ann  = [results[c]["ann_capex"] / CONFIGS[c]["energy_served_kwh"]
            for c in configs_list]
om_ann   = [results[c]["ann_om"]    / CONFIGS[c]["energy_served_kwh"]
            for c in configs_list]
fuel_ann = [results[c]["ann_fuel"]  / CONFIGS[c]["energy_served_kwh"]
            for c in configs_list]
repl_ann = [results[c]["ann_repl"]  / CONFIGS[c]["energy_served_kwh"]
            for c in configs_list]

x = np.arange(3)
w = 0.45
b1 = ax1.bar(x, cap_ann,  w, label="Capital",     color="#1B4FD8", alpha=0.9)
b2 = ax1.bar(x, om_ann,   w, bottom=cap_ann,
             label="O&M",        color="#16A34A", alpha=0.9)
b3 = ax1.bar(x, fuel_ann, w,
             bottom=[a+b for a,b in zip(cap_ann, om_ann)],
             label="Fuel",       color="#DC2626", alpha=0.9)
b4 = ax1.bar(x, repl_ann, w,
             bottom=[a+b+c for a,b,c in zip(cap_ann, om_ann, fuel_ann)],
             label="Replacement",color="#BA7517", alpha=0.9)

for i, c in enumerate(configs_list):
    lcoe = results[c]["lcoe"]
    ax1.text(i, lcoe + 0.003, f"€{lcoe:.3f}",
             ha="center", va="bottom", fontsize=9, fontweight="bold")

ax1.axhline(0.35, color="#DC2626", linestyle=":", linewidth=1.5,
            label="Diesel ceiling (€0.35)")
ax1.axhline(0.227, color="#1B4FD8", linestyle="--", linewidth=1.0, alpha=0.5)
ax1.set_xticks(x)
ax1.set_xticklabels(config_labels, fontsize=8)
ax1.set_ylabel("LCOE (EUR/kWh)")
ax1.set_title("LCOE by cost component", fontsize=10)
ax1.legend(fontsize=8, loc="upper right")
ax1.grid(True, alpha=0.25, linestyle="--", axis="y")

# Panel 2: CAPEX breakdown — stacked bar
ax2 = fig.add_subplot(gs[0, 1])
capex_pv   = [results[c]["capex_pv"]   / 1000 for c in configs_list]
capex_wind = [results[c]["capex_wind"] / 1000 for c in configs_list]
capex_batt = [results[c]["capex_batt"] / 1000 for c in configs_list]
capex_gen  = [results[c]["capex_gen"]  / 1000 for c in configs_list]
capex_conv = [results[c]["capex_conv"] / 1000 for c in configs_list]

ax2.bar(x, capex_pv,   w, label="PV",        color="#1B4FD8", alpha=0.9)
ax2.bar(x, capex_wind, w, bottom=capex_pv,
        label="Wind",       color="#16A34A", alpha=0.9)
ax2.bar(x, capex_batt, w,
        bottom=[a+b for a,b in zip(capex_pv, capex_wind)],
        label="Battery",    color="#534AB7", alpha=0.9)
ax2.bar(x, capex_gen,  w,
        bottom=[a+b+c for a,b,c in zip(capex_pv, capex_wind, capex_batt)],
        label="Generator",  color="#DC2626", alpha=0.9)
ax2.bar(x, capex_conv, w,
        bottom=[a+b+c+d for a,b,c,d in
                zip(capex_pv, capex_wind, capex_batt, capex_gen)],
        label="Converter",  color="#BA7517", alpha=0.9)

ax2.axhline(500, color="#0F1923", linestyle="--", linewidth=1.5,
            label="Budget ceiling (€500k)")
ax2.set_xticks(x)
ax2.set_xticklabels(config_labels, fontsize=8)
ax2.set_ylabel("CAPEX (kEUR)")
ax2.set_title("CAPEX breakdown by component", fontsize=10)
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.25, linestyle="--", axis="y")

# Panel 3: Sensitivity — tornado chart for Config B
ax3 = fig.add_subplot(gs[1, 0])
base = base_lcoe_B
sens_ranges = []
sens_labels = []
for param_name, (values, lcoe_vals) in sens_results.items():
    low  = min(lcoe_vals)
    high = max(lcoe_vals)
    sens_ranges.append((low - base, high - base))
    sens_labels.append(param_name)

# Sort by total range (largest impact at top)
order = sorted(range(len(sens_ranges)),
               key=lambda i: sens_ranges[i][1]-sens_ranges[i][0],
               reverse=True)
sens_ranges = [sens_ranges[i] for i in order]
sens_labels = [sens_labels[i] for i in order]

y_pos = np.arange(len(sens_labels))
for i, (low_d, high_d) in enumerate(sens_ranges):
    ax3.barh(i, high_d, left=0,    height=0.5,
             color="#DC2626", alpha=0.8)
    ax3.barh(i, low_d,  left=0,    height=0.5,
             color="#1B4FD8", alpha=0.8)

ax3.axvline(0, color="#0F1923", linewidth=1.5)
ax3.set_yticks(y_pos)
ax3.set_yticklabels(sens_labels, fontsize=8)
ax3.set_xlabel("ΔLCOE from base (EUR/kWh)")
ax3.set_title("Sensitivity analysis — Config B\n(tornado chart)", fontsize=10)
ax3.grid(True, alpha=0.25, linestyle="--", axis="x")

# Panel 4: 20-year cumulative cash flow — Config B vs diesel
ax4 = fig.add_subplot(gs[1, 1])
years = np.arange(1, N_YEARS + 1)

# Config B annual cost (simplified: capex yr0 + annual costs)
# Diesel annual cost (escalating fuel)
capex_B   = results["B"]["capex_total"]
ann_om_B  = results["B"]["ann_om"]

cumcost_B = np.zeros(N_YEARS + 1)
cumcost_D = np.zeros(N_YEARS + 1)
cumcost_B[0] = capex_B

for yr in range(1, N_YEARS + 1):
    fuel_yr_B = CONFIGS["B"]["annual_fuel_L"] * FUEL_PRICE * (1+INFLATION)**(yr-1)
    fuel_yr_D = DIESEL_ONLY["annual_fuel_L"]  * FUEL_PRICE * (1+INFLATION)**(yr-1)
    cumcost_B[yr] = cumcost_B[yr-1] + ann_om_B + fuel_yr_B
    cumcost_D[yr] = cumcost_D[yr-1] + COSTS["gen_capital_per_kw"] * \
                    DIESEL_ONLY["gen_kw"] * (1 if yr==1 else 0) + fuel_yr_D

ax4.plot(range(N_YEARS+1), cumcost_B/1000, color="#1B4FD8",
         linewidth=2, label="Config B (hybrid)")
ax4.plot(range(N_YEARS+1), cumcost_D/1000, color="#DC2626",
         linewidth=2, linestyle="--", label="Diesel-only baseline")

# Find crossover
crossover = None
for yr in range(N_YEARS + 1):
    if cumcost_B[yr] <= cumcost_D[yr]:
        crossover = yr
        break

if crossover and crossover > 0:
    ax4.axvline(crossover, color="#16A34A", linestyle=":",
                linewidth=1.5, label=f"Breakeven: yr {crossover}")
    ax4.scatter([crossover], [cumcost_B[crossover]/1000],
                color="#16A34A", zorder=5, s=80)

ax4.set_xlabel("Year")
ax4.set_ylabel("Cumulative cost (kEUR)")
ax4.set_title("20-year cumulative cost\nConfig B vs diesel-only", fontsize=10)
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.25, linestyle="--")

plt.savefig("results/figures/06_techno_economic.png",
            dpi=150, bbox_inches="tight")
plt.show()
print("Saved: results/figures/06_techno_economic.png")

print("\n" + "="*65)
print("PHASE 5 COMPLETE")
print("="*65)