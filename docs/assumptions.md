# Project Assumptions Log

**Project:** Off-Grid Hybrid Microgrid — Ada Foah, Ghana
**Engineer:** Felix Okumo
**Last updated:** April 7, 2026

## Site

- **Coordinates:** 5.7833°N, 0.6333°E (Ada East District, Greater Accra Region, Ghana)
- **Altitude:** ~2 m asl
- **Grid connection:** None assumed (off-grid design basis)
- **Climate:** Köppen Aw (tropical savanna, coastal)

## Site identification note
- Siamekome Island is used as a representative community within the Ada East estuary
  cluster for design basis purposes. Geographic and meteorological parameters are
  based on verified Ada East District data (5.7833°N, 0.6333°E).

## Load
- **500 households:** 60% Tier 2 MTF (~200 Wh/day), 40% Tier 3 (~1,000 Wh/day)
- **Anchor loads:** 1 clinic, 2 schools, 10 shops, 1 water pump
- **Estimated daily energy:** 420 kWh/day
- **Estimated peak demand:** 65–75 kW (coincidence factor 0.6)
- **Source:** IEA Multi-Tier Framework; GOGLA 2022 market report

## Financial
- **CAPEX ceiling:** EUR 500,000 (donor-funded)
- **Project lifetime:** 20 years
- **Discount rate:** 8% (typical for donor-funded African energy projects, IRENA 2022)
- **Diesel price:** USD 1.56/litre (NPA price floor + margins, April 2026) 
- **Currency:** EUR primary, USD secondary; EUR/USD = 1.08 

## Reliability
- **LPSP target:** ≤ 5% (Loss of Power Supply Probability)
- **Reference:** IEC 62257-9-1 (standalone PV systems — extended to hybrid)

## Standards referenced
- IEC 62257 series (rural electrification systems)
- IEEE 1562 (guide for array and battery sizing for stand-alone PV)
- IEA ESMAP Multi-Tier Framework for energy access
- Ghana Renewable Energy Act 832, 2011

## Site Risk
- Coastal erosion rate: ~1.94 m/yr (eastern estuary shoreline), ~0.58 m/yr (western)
  Source: Appeaning Addo (2015); Geoenvironmental Disasters journal (2020)
  Implication: All infrastructure sited minimum 50m from active shoreline;
  elevated mounting structures required; 20-year project life erosion = ~39m eastern retreat
- Saline environment: All electrical equipment rated to IEC 60721-3-4 (salt mist Class 4S)
- Seasonal flooding: PV arrays mounted minimum 1.5m above highest flood level

## Solar resource data
- Database: PVGIS-ERA5 TMY (2005–2020)
- Justification: Superior tropical/coastal accuracy vs SARAH-3 due to ITCZ convective
cloud regime at 5.78°N; validated for West Africa (Journée et al. 2012)
- Single-year comparison with SARAH-3 noted as limitation; flagged for sensitivity

## Wind resource
- Hub height: 50 m (O&M accessibility constraint; limited local technical capacity)
- Wind shear exponent α = 0.12 (IEC 61400-1; coastal flat terrain, Class A)
- 60 m sensitivity case: to be run in Phase 5
- Data source: Renewables.ninja (NASA MERRA-2), year 2019

## Wind resource — data source decision

ERA5 (PVGIS): 5.07 m/s mean at 10m → 6.15 m/s at 50m (α=0.12)
MERRA-2 (Renewables.ninja): 3.54 m/s at 10m → 4.43 m/s at 50m

Primary basis: ERA5 (better validated for West African coastal sites;
Gbobaniyi et al. 2014, Climate Dynamics)
Conservative case: MERRA-2 (used in Phase 5 sensitivity analysis)
Limitation: No ground-measured wind data available; met mast recommended
for bankable study. ERA5/MERRA-2 uncertainty range: ±20–30%.

## Revised system configurations (post resource assessment)

Config A — PV + Battery + Diesel (solar-dominant, no wind)
  Rationale: Baseline; strong solar resource (5.16 PSH); simplest O&M
  
Config B — PV + Wind + Battery + Diesel (hybrid, balanced)
  Wind turbine: IEC Class III, 50–100 kW nameplate, rated speed ~11 m/s
  Rationale: Wind supplements PV during ITCZ cloud season (Jun–Sep)
              and provides overnight generation
              
Config C — PV + Wind (larger) + Battery + Diesel (wind-augmented)
  Wind turbine: IEC Class III, 100–150 kW nameplate
  Rationale: Tests whether larger wind fraction reduces LCOE
             despite higher CAPEX

Wind CF design basis: 16.5% (ERA5, IEC Class III turbine, 50m)
Wind CF conservative:  5.4% (MERRA-2, same turbine)
Both cases run in HOMER Phase 3.

## Phase 1 Resource Assessment — Final Summary
Completed: April 2026

### Solar (PVGIS ERA5 TMY, 2005–2020)
- Annual GHI:              1,884 kWh/m²/year
- Daily average GHI (PSH): 5.16 h/day  
- Max hourly GHI:          992 W/m²
- Mean ambient temp:       26.3°C
- PV thermal derating:     −10.5% (NOCT correction, mono-Si, −0.40%/°C)
- Air density correction:  −3.8% on wind turbine output vs ISA

### Wind (ERA5 primary / MERRA-2 conservative)
- ERA5 mean WS at 10m:     5.07 m/s
- ERA5 mean WS at 50m:     6.15 m/s  ← design basis
- MERRA-2 mean WS at 50m:  4.43 m/s  ← conservative/sensitivity case
- Weibull k (ERA5, 50m):   3.976
- Weibull λ (ERA5, 50m):   6.791 m/s
- Design turbine class:    IEC Class III (rated speed 11 m/s, cut-in 2.5 m/s)
- Design basis CF:         16.5% (ERA5 + IEC Class III)
- Conservative CF:          5.4% (MERRA-2 + IEC Class III)
- Vestas V80 rejected:     turbine-site mismatch (CF 4.2%); wrong wind class

### Key finding — solar–wind complementarity
- ITCZ cloud season (Jun–Sep) suppresses solar GHI
- SW monsoon peak (Jul–Aug) is strongest wind period
- Resources are partially anti-correlated → hybrid design is justified
- Pearson correlation (monthly solar vs wind): - 0.24

### Design implications confirmed
1. PV is primary generation source — unambiguous
2. Wind is viable as supplementary source with IEC Class III turbine
3. Battery must cover evening peak (18:00–21:00) + overnight base load
4. Diesel is backup only — not primary dispatch
5. Wind CF uncertainty range (5–17%) → sensitivity analysis required in Phase 5

## Load Profile — Final Verified Values (Phase 0/1 corrected)
Revised: April 2026 — Tier consumption corrected from MTF minimums to 
typical coastal Ghana values (GOGLA 2022)

| Parameter | Value | Basis |
|-----------|-------|-------|
| Tier 2 consumption | 500 Wh/day/HH | GOGLA 2022; ESMAP MTF Ghana |
| Tier 3 consumption | 1,500 Wh/day/HH | Ghana Energy Commission 2021 |
| Household daily energy | 450 kWh/day (gross) → 270 kWh/day (after CF=0.6) | |
| Anchor load daily | ~414 kWh/day | WHO/UNICEF; GOGLA PRO 2022 |
| Peak system demand | 51.5 kW | Script verified |
| Peak system demand | 51.5 kW at 08:00 | Coincidence peak: full anchor loads + morning household routine |
| Secondary peak | 44.5 kW at 18:00 | Evening household peak as anchor loads wind down |
| Critical design period | 08:00 morning (solar gap) | Battery must cover ~27.5 kW deficit for 1–2h at partial solar |
| Critical design period | 18:00–06:00 (no solar) | Battery must cover evening peak + overnight base load |
| Average demand | 28.5 kW | Script verified |
| Load factor | 0.553 | Script verified |
| Annual energy | 249,660 kWh/year | CSV round-trip verified |
| Daily average | 684 kWh/day | Script verified |
| HOMER battery search range | 150–450 kWh LFP nameplate | Revised from 400–900 |
| Pre-optimisation LCOE | EUR 0.36–0.46/kWh | At full EUR 500k CAPEX |
| Diesel-only alternative | EUR 0.35–0.55/kWh | ESMAP 2023 benchmark |

## Simulation tool
- Tool: HOMER Pro (v2.81 or later), student academic licence
- Rationale: Off-grid optimisation primary use case; full battery cycling model;
  detailed LPSP analysis; generator dispatch constraints
- HOMER Grid rejected: designed for grid-connected DER, not off-grid primary

