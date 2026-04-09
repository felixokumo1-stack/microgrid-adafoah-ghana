# Mathematical Model — Ada East Hybrid Microgrid
**Project:** Off-Grid Hybrid Microgrid, Siamekome Island, Ada East, Ghana  
**Author:** Felix Okumo  
**Date:** April 2026  
**Reference standard:** IEC 62257-9-1:2020 (Hybrid systems for rural electrification)

---

## 1. System Architecture

The system consists of four generation/storage components connected to a 
common AC bus through power electronics:

| Component | Symbol | Unit | Role |
|-----------|--------|------|------|
| PV array | P_PV | kW | Primary generation |
| Wind turbine | P_wind | kW | Supplementary generation |
| Battery bank | P_batt | kW | Storage / dispatch buffer |
| Diesel generator | P_diesel | kW | Backup / firm capacity |
| Load | P_load | kW | Demand to be served |

Dispatch priority (rule-based controller):
1. PV generation (zero marginal cost)
2. Wind generation (zero marginal cost)  
3. Battery discharge (if SOC > SOC_min)
4. Diesel generator (last resort)

Time resolution: hourly (Δt = 1 h)  
Simulation horizon: 8,760 hours (1 non-leap year)  
Index: t = 1, 2, ..., 8760

---

## 2. Master Energy Balance

At each time step t, the system must satisfy:

    P_PV(t) + P_wind(t) + P_batt_dis(t) + P_diesel(t) 
        = P_load(t) + P_batt_chg(t) + P_loss(t) + LPS(t)     ... (1)

Where:
- LPS(t) ≥ 0  (Loss of Power Supply, kW — unmet demand)
- P_batt_dis(t) · P_batt_chg(t) = 0  (cannot charge and discharge simultaneously)
- P_loss(t) = α_loss · P_load(t),  α_loss = 0.05  (5% system losses, IEC 62257)

The controller objective is to minimise Σ LPS(t) across all 8760 hours
subject to CAPEX ≤ EUR 500,000 and LPSP ≤ 0.05.

---

## 3. PV Power Model

    P_PV(t) = P_PV_rated × [G_POA(t)/1000] × η_inv × f_temp(t) × f_soil  ... (2)

Parameters:
| Parameter | Symbol | Value | Source |
|-----------|--------|-------|--------|
| Inverter efficiency | η_inv | 0.96 | SMA/Fronius spec, industry standard |
| Temp coefficient | γ | −0.004 /°C | Mono-Si manufacturer spec |
| NOCT rise | ΔT_NOCT | 25°C | IEC 61215, open-rack mounting |
| STC temperature | T_STC | 25°C | IEC 60904-3 |
| Soiling/derating | f_soil | 0.80 | IEC 62548:2023, tropical coastal |

Combined mean performance ratio:
    PR = η_inv × f_temp_mean × f_soil = 0.96 × 0.895 × 0.80 = 0.687

Interpretation: 100 kWp nameplate → 68.7 kW mean real output at this site.
This is the Performance Ratio (PR). Benchmark for West Africa: 0.65–0.75 (IRENA 2023).
Our PR of 0.687 is within benchmark → model is consistent.

---

## 4. Wind Power Model

    P_wind(t) = P_rated × Cp(v(t)) × η_conv                              ... (3)

Where Cp(v) follows the piecewise power curve:

    Cp(v) = 0                              v < v_ci = 2.5 m/s
    Cp(v) = (v³ - v_ci³)/(v_r³ - v_ci³)  v_ci ≤ v < v_r = 11.0 m/s  
    Cp(v) = 1                              v_r ≤ v < v_co = 25.0 m/s
    Cp(v) = 0                              v ≥ v_co

Design turbine: IEC Wind Class III, 50 kW nameplate (HOMER reference)
Parameters:
| Parameter | Value | Basis |
|-----------|-------|-------|
| Rated power P_rated | 50 kW | Sized for ~100 kW peak load, one unit |
| Cut-in speed v_ci | 2.5 m/s | IEC Class III specification |
| Rated speed v_r | 11.0 m/s | IEC Class III specification |
| Cut-out speed v_co | 25.0 m/s | Standard |
| Converter efficiency η_conv | 0.95 | Industry standard |
| Hub height | 50 m | O&M accessibility constraint |
| Wind shear exponent α | 0.12 | IEC 61400-1, coastal flat |

Annual energy yield estimate (ERA5 basis):
    E_wind = 50 kW × 0.165 CF × 8760 h × 0.95 = 68,607 kWh/year
    As fraction of annual load (420,000 kWh): 16.3%

    ---

## 5. Battery State-of-Charge Model

### 5.1 SOC update equations

Charging (when P_chg(t) > 0):
    SOC(t) = SOC(t-1) + [P_chg(t) × η_chg × Δt] / E_batt        ... (4a)

Discharging (when P_dis(t) > 0):
    SOC(t) = SOC(t-1) − [P_dis(t) × Δt] / (η_dis × E_batt)      ... (4b)

### 5.2 Hard constraints

    SOC_min ≤ SOC(t) ≤ 1.0                                         ... (4c)
    P_chg(t) × P_dis(t) = 0    (no simultaneous charge/discharge)  ... (4d)
    P_dis(t) ≤ C_rate × E_batt                                     ... (4e)

### 5.3 Battery technology comparison

| Parameter | LFP (Li-ion) | VRLA (lead-acid) |
|-----------|-------------|-----------------|
| SOC_min (DoD limit) | 0.20 (80% usable) | 0.50 (50% usable) |
| Round-trip efficiency η_chg × η_dis | 0.92–0.95 | 0.75–0.85 |
| Cycle life at design DoD | 3,000–6,000 | 500–1,200 |
| CAPEX (EUR/kWh nameplate) | 350–500 | 150–250 |
| Calendar life | 10–15 years | 5–8 years |
| Suitability for coastal saline env. | Good (sealed) | Moderate |

Design choice: LFP selected for HOMER baseline.
Rationale: Higher DoD, longer cycle life, better LCOE over 20-year project life
despite higher upfront cost. VRLA modelled as sensitivity case in Phase 5.

### 5.4 Preliminary battery sizing (critical design night)

Evening peak + overnight base load requirement: ~510 kWh
LFP nameplate required (80% DoD): 510 / 0.80 = 637.5 kWh
HOMER optimisation range: 400–900 kWh (±40% around estimate)
If HOMER returns <300 kWh or >1,500 kWh: investigate immediately.

### 5.5 Parameters

| Parameter | Symbol | Value | Source |
|-----------|--------|-------|--------|
| Charge efficiency | η_chg | 0.97 | LFP manufacturer spec |
| Discharge efficiency | η_dis | 0.97 | LFP manufacturer spec |
| Round-trip efficiency | η_rt | 0.94 | η_chg × η_dis |
| Min SOC | SOC_min | 0.20 | LFP design limit |
| Max C-rate | C_rate | 0.5C | Conservative for cycle life |
| Self-discharge | σ | 0.02%/h | LFP spec (negligible) |

---

## 6. Diesel Generator Model

### 6.1 Operating constraints

    P_diesel(t) = 0  OR  P_diesel(t) ≥ f_min × P_rated_diesel      ... (5a)
    f_min = 0.30  (minimum load ratio, wet-stacking prevention)

    P_diesel(t) ≤ P_rated_diesel                                     ... (5b)

### 6.2 Fuel consumption model (linearised)

    F(t) = P_rated × [a + b × (P_diesel(t) / P_rated)]   [L/h]     ... (5c)

    a = 0.0811 L/kWh  (no-load coefficient, EPA Tier 2)
    b = 0.2450 L/kWh  (marginal coefficient, EPA Tier 2)

    Source: HOMER Pro documentation; EPA Tier 2 emission standards

### 6.3 Annual fuel cost sensitivity

    Diesel price: USD 1.56/L (NPA Ghana, April 2026)
    EUR/USD: 1.08 → EUR 1.44/L

    At 2,000 h/yr runtime, 60 kW generator, 50% avg load:
    Annual fuel cost ≈ USD 38,000/yr → EUR 35,200/yr
    Over 20 years (undiscounted): EUR 704,000 — exceeds CAPEX budget
    → Minimising diesel runtime is the dominant LCOE lever

### 6.4 Generator sizing

    Rated capacity: P_rated_diesel = P_load_peak / f_min_load
                  = 78 kW / 0.30 ≈ 80 kW (round up to standard size)
    Standard sizes: 60 kW, 80 kW, 100 kW
    Design basis: 80 kW (covers peak with 2.6% headroom)
    FLAG: HOMER will optimise this — treat 80 kW as initial estimate only

    ---

## 7. Reliability — Loss of Power Supply Probability

    LPSP = Σ[t=1..8760] LPS(t) / Σ[t=1..8760] P_load(t)           ... (6)

    LPS(t) = max(0,  P_load(t) − P_PV(t) − P_wind(t) 
                    − P_batt_dis(t) − P_diesel(t))                  ... (7)

Constraint: LPSP ≤ 0.05  (≤5% unmet energy fraction)
Reference: IEC 62257-9-1:2020; ESMAP rural electrification guidelines

In absolute terms:
    Max allowable unmet energy = 0.05 × 420,000 = 21,000 kWh/year
    Equivalent continuous unmet power = 21,000/8760 = 2.4 kW (average)
    
LPSP is computed in Phase 4 (Python dispatch simulation) and must
be verified against HOMER output. If they disagree by >2 percentage
points, investigate dispatch logic before proceeding to Phase 5.

---

## 8. Techno-Economic Model — LCOE

### 8.1 Levelised Cost of Energy

    LCOE = (CRF × CAPEX + C_OM + C_fuel) / E_served    [EUR/kWh]   ... (8)

### 8.2 Capital Recovery Factor

    CRF = i(1+i)^n / [(1+i)^n − 1]                                  ... (9)

    i = 0.08  (base case: social discount rate, donor-funded project, IRENA 2022)
    Sensitivity: i = 0.12 (commercial rate, private investor perspective — Phase 5)
    n = 20 years
    CRF (base, 8%):  0.1019
    CRF (sensitivity, 12%): 0.1339  

    Annualised CAPEX at EUR 500k ceiling: 0.1019 × 500,000 = EUR 50,950/year

### 8.3 Component costs (design basis — to be confirmed in Phase 5)

| Component | Unit cost | Source |
|-----------|-----------|--------|
| PV modules | EUR 250/kWp | IRENA 2023, utility Africa includes Ghana import duty ~12% and island logistics|
| Inverter/charge controller | EUR 100/kWp | Industry quote basis |
| Wind turbine (IEC Class III) | EUR 1,500/kW installed | IRENA 2023 small wind |
| LFP battery | EUR 400/kWh nameplate | BNEF 2023 pack price |
| Diesel generator | EUR 300/kW installed | Generator supplier Africa |
| BOS, wiring, civil | 20% of equipment cost | Standard estimating factor |
| O&M (annual) | 2% of CAPEX/year | IEC 62257, limited O&M context |
| O&M — PV + battery + civil | 2% of PV+battery CAPEX/year | IEC 62257; standard solar |
| O&M — wind turbine | 4% of wind CAPEX/year | IRENA 2019; coastal saline environment |
| O&M — diesel generator | 3% of diesel CAPEX/year + fuel | EPA Tier 2 maintenance schedule |

FLAG: All costs require verification against current supplier quotes in Phase 5.
These are design-basis estimates for HOMER input only.

### 8.4 LCOE target benchmarks

| Benchmark | LCOE (EUR/kWh) | Source |
|-----------|---------------|--------|
| Diesel-only generation, West Africa | 0.35–0.55 | ESMAP 2023 |
| Solar+battery mini-grid, West Africa | 0.18–0.35 | IRENA 2023 |
| Grid electricity, Ghana (ECG tariff) | 0.08–0.12 | PURC 2024 |
| Our target (donor-funded) | ≤ 0.30 | Project design basis |

If our LCOE exceeds EUR 0.35/kWh, the project is uncompetitive vs diesel.
If below EUR 0.20/kWh, it is excellent for this context.
Grid connection status: CONFIRMED GREENFIELD — grid isolated by Volta estuary.
Submarine cable extension not planned (Ghana Ministry of Energy, 2020–2025).
ECG tariff (EUR 0.08–0.12/kWh) is aspirational benchmark only.
Relevant competitor: diesel-only generation at EUR 0.35–0.55/kWh.
Project LCOE target of ≤ EUR 0.30/kWh represents ~35–45% cost reduction
vs diesel baseline → the primary economic justification.

### 8.5 Component replacement costs (sinking fund method)

For components with lifetimes shorter than the 20-year project life,
replacement cost is annualised using a sinking fund factor (SFF):

    SFF = i / [(1+i)^m − 1]

Where m = years until replacement.

| Component | Replacement year | Replacement cost | SFF (8%) | Annual provision |
|-----------|-----------------|-----------------|----------|-----------------|
| Inverter | Year 12 | EUR 60/kWp × capacity | i/[(1.08)^12−1] = 0.0527 | cost × 0.0527 |
| LFP battery | Year 14 | EUR 400/kWh × capacity | i/[(1.08)^14−1] = 0.0430 | cost × 0.0430 |
| Diesel genset overhaul | Year 10 | EUR 150/kW × capacity | i/[(1.08)^10−1] = 0.0690 | cost × 0.0690 |

Updated LCOE formula (full):

    LCOE = (CRF×CAPEX + C_OM + C_fuel + C_replacement) / E_served   ... (8b)

    C_replacement = Σ (replacement_cost_j × SFF_j)  for each component j

FLAG: Replacement costs will be calculated with actual sized capacities
in Phase 5. Placeholder formula established here.

