# PROJECT BRIEF — Off-Grid Hybrid Microgrid Design
**Project number:** 01  
**Domain:** Renewable Energy Systems  
**Location:** Siamekome Island, Ada East District, Greater Accra Region, Ghana  
**Coordinates:** 5.7833°N, 0.6333°E  
**Duration:** April 2026  
**Status:** Complete  

---

## Tools and Software
| Tool | Purpose |
|------|---------|
| HOMER Pro (student licence) | System optimisation, 8760-hour dispatch |
| Python 3.x + pandas/numpy/matplotlib | Resource assessment, dispatch simulation, financial model |
| windpowerlib | Wind turbine power curve modelling |
| PVGIS ERA5 TMY | Solar irradiance data (EU JRC) |
| Renewables.ninja (MERRA-2) | Wind resource cross-check |
| GitHub | Version control, all phases committed |

---

## Problem Statement
Siamekome Island — a representative community within the Ada East Volta 
estuary cluster, Greater Accra Region, Ghana — has no grid connection and 
no feasible path to grid extension due to its island geography. Approximately 
500 households and five anchor loads (health clinic, two schools, productive 
use shops, water pump) depend on intermittent diesel generation.

**Decision question:** What is the minimum-LCOE PV-wind-battery-diesel hybrid 
configuration that provides 24/7 electricity to 500 households within a 
EUR 500,000 donor capital budget, achieving ≤5% loss of power supply probability?

---

## Constraints Verified
| Constraint | Requirement | Config B Result | Status |
|---|---|---|---|
| CAPEX ceiling | ≤ EUR 500,000 | EUR 423,000 | ✓ EUR 77,000 headroom |
| LPSP | ≤ 5% | 0.00% | ✓ Exceeded |
| Diesel backup | Required | 60 kW gen included | ✓ |
| O&M accessibility | Limited local capacity | 50m hub height, LFP battery | ✓ |

---

## Methodology
1. **Site characterisation** — coordinates locked, coastal erosion risk documented, 
   grid isolation confirmed (Ada East estuary, no submarine cable planned)
2. **Load profiling** — bottom-up demand estimation using IEA Multi-Tier Framework; 
   500 HH (60% Tier 2 / 40% Tier 3) + anchor loads; 249,660 kWh/yr; 51.5 kW peak
3. **Resource assessment** — PVGIS ERA5 TMY solar (5.16 PSH/day); ERA5 vs MERRA-2 
   wind discrepancy identified and resolved (ERA5 selected, α=0.12 IEC 61400-1); 
   IEC Class III turbine selected after Vestas V80 turbine-site mismatch diagnosed
4. **Mathematical modelling** — energy balance, SOC equations, diesel fuel curve, 
   LPSP formula all derived from first principles and documented
5. **HOMER Pro optimisation** — three configurations evaluated across 500–1,730 
   simulations each; search spaces validated to avoid boundary artefacts
6. **Python dispatch verification** — independent 8760-hour simulation; 
   LPSP 0.00% confirmed; fuel discrepancy explained by minimum-load constraint mechanics
7. **Techno-economic analysis** — LCOE, NPV, sensitivity analysis; 
   Python model within 2.5% of HOMER for all configurations

---

## Key Results

### Optimal System — Config B
| Component | Specification |
|---|---|
| PV array | 150 kWp, fixed tilt 6°, mono-Si |
| Wind turbine | 1 × 50 kW IEC Class III, 50m hub |
| Battery | 300 kWh LFP (3 × 100 kWh), 80% DoD |
| Diesel generator | 60 kW, backup only |
| Converter | 60 kW bidirectional |
| **CAPEX** | **EUR 423,000** |
| **LCOE** | **EUR 0.227/kWh** |
| **Renewable fraction** | **97.6%** |
| Annual fuel | 2,968 L/yr |
| Generator hours | 307 h/yr |
| LPSP | 0.00% |

### Three-Configuration Comparison
| KPI | Config A | Config B | Config C |
|---|---|---|---|
| LCOE (EUR/kWh) | 0.287 | **0.227** | 0.233 |
| CAPEX (EUR) | 446,500 | **423,000** | 427,000 |
| NPC (EUR) | 703,858 | **555,700** | 570,385 |
| Renewable fraction | 86.5% | **97.6%** | 97.9% |
| Annual fuel (L/yr) | 11,461 | **2,968** | 2,580 |
| vs diesel LCOE reduction | 52.7% | **63.0%** | 62.2% |

### Financial Performance — Config B vs Diesel Baseline
| Metric | Value |
|---|---|
| Annual cost saving vs diesel | EUR 89,849/yr |
| NPV of 20-year savings | EUR 882,154 |
| Simple payback period | 4.7 years |
| Breakeven discount rate | ~16.8% |

---

## Key Engineering Insights

### Insight 1 — Wind integration value
Adding one 50 kW IEC Class III wind turbine (EUR 75,000 capital) to 
Config A enables downsizing PV by 50 kWp (−EUR 60,000) and battery by 
100 kWh (−EUR 35,000), yielding a net CAPEX reduction of EUR 23,500 
despite adding wind. Over 20 years, the turbine generates EUR 148,158 
in NPC savings driven by 74% fuel reduction. The resource complementarity 
(Pearson r = −0.24, SW monsoon wind peaks during ITCZ solar suppression) 
is the physical mechanism enabling this efficiency.

### Insight 2 — Diminishing returns at second turbine
A second wind turbine (Config C) allows further downsizing but increases 
NPC by EUR 14,685 versus Config B. The system is already 97.6% renewable 
at Config B — only 2,968 L/yr of diesel remains to displace. The second 
turbine's lifecycle cost (EUR ~104,000 NPC) exceeds its fuel displacement 
value (EUR ~25,000 NPC), confirming single-turbine as the economic optimum.

### Insight 3 — Discount rate is dominant risk
Config B LCOE ranges from EUR 0.206/kWh (6% concessional) to 
EUR 0.323/kWh (15% commercial). The project break-even discount rate 
is 16.8% — above all realistic financing scenarios for donor-funded 
Sub-Saharan African energy projects. The economic case is robust.

### Insight 4 — Fuel price insensitivity
At 97.6% renewable fraction, Config B LCOE changes by only EUR 0.016/kWh 
across a diesel price range of EUR 0.90–2.00/L. This near-immunity to 
fuel price volatility is a key resilience advantage for a remote community 
previously dependent entirely on diesel supply chains.

### Insight 5 — O&M vs fuel trade-off
Config B O&M is EUR 1,893/yr higher than Config A due to wind turbine 
coastal maintenance. This fixed cost is offset by EUR 14,686/yr in fuel 
savings. Net annual benefit: EUR 12,793/yr. At 307 h/yr generator runtime, 
the diesel generator reaches its 15,000-hour overhaul threshold in 48.9 
years — eliminating generator replacement within the 20-year project life 
and further reducing lifecycle costs.

---

## Lessons Learned
1. **Turbine-site matching is critical.** The initial Vestas V80 reference 
   turbine (rated speed 16 m/s) produced 4.2% CF at this site vs 19.7% for 
   an IEC Class III turbine (rated speed 11 m/s). Wrong turbine class would 
   have invalidated the entire wind analysis.
2. **Reanalysis dataset disagreement.** ERA5 and MERRA-2 disagreed by 32% 
   on mean wind speed at 10m. Validation against West Africa literature 
   confirmed ERA5 as primary basis. Single-source wind data is insufficient.
3. **Search space boundary artefacts.** Initial Config A optimisation with 
   PV ceiling of 200 kWp produced a boundary optimum. Extending to 300 kWp 
   confirmed 250 kWp as true unconstrained optimum (budget constraint then 
   applied to select 200 kWp as budget-constrained result).
4. **MTF threshold vs typical consumption.** IEA MTF Tier 2/3 values 
   (200/1000 Wh/day) are access thresholds, not typical consumption. 
   Using thresholds produced a 4× underestimate of annual load. Revised 
   to GOGLA 2022 typical values (500/1500 Wh/day).
5. **Dispatch model limitations.** Rule-based hourly dispatch overstates 
   diesel runtime by ~49% vs HOMER's optimising engine, primarily due to 
   minimum load ratio handling at battery floor. LPSP agreement is exact; 
   fuel discrepancy is documented and explained.

---

## Links
- GitHub repository: [microgrid-adafoah-ghana]
- Key output files:
  - `results/dispatch_8760.csv` — full 8760-hour dispatch simulation
  - `results/techno_economic_summary.csv` — three-configuration comparison
  - `results/figures/05_dispatch_8760.png` — dispatch visualisation
  - `results/figures/06_techno_economic.png` — financial analysis
  - `homer/Config_B_PV_Wind_Batt_Diesel.homer` — HOMER Pro project file