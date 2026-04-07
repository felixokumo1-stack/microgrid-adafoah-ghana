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