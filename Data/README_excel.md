# Demonstration Directory: Sample Notebooks and Master Matrix

This directory contains a template execution matrix (`Master_maize.xlsx`) required to test the `DSSATspatial` batch processing workflows. The spatial modeling pipeline is driven by this primary Excel dataset and is designed to be fully crop-specific. 

The following rules specify the parameterization of the master sheet for any supported DSSAT crop model.

## Master Sheet: Column Guide

### General Parameters
- **treatment**: Treatment number (1, 2, 3, ...)
- **weather**: Weather station file code (e.g., TN012019)
- **soil**: Soil profile ID (e.g., IN04184856)
- **cultivar**: Crop-specific variety/cultivar code (e.g., Ganga for Maize, IR64 for Rice)
- **planting_date**: Planting date, supports standard format yyyymmdd (e.g., 20221022) or Julian format yyyyddd (e.g., 2001161)
- **PLPOP**: Seed population at planting, plants/m2
- **PPOE**: Emergence population, plants/m2
- **PLRS**: Row spacing, cm
- **PLDP**: Planting depth, cm
- **NYEARS**: Number of years to simulate (e.g., 1, 2)

### Advanced Planting Details (Optional)
- **PLME**: Planting Method (`S` = Seed, `T` = Transplant, `P` = Pre-germinated, etc.)
- **PLDS**: Planting Distribution (`R` = Row, `B` = Broadcast, `H` = Hill)
- **PAGE**: Transplant age in days (crucial for Rice)
- **PLWT**: Transplant weight in kg/ha (crucial for Rice)
- **PLRD**: Row direction (degrees from North)

*Note: If left blank, these will inherit default values from the master `.RIX` or `.MZX` base file.*

### Explicit Calendar Overrides (Optional)
Overrides the internal dynamic day-shifting engine to force specific dates:
- **SDATE**: Explicit simulation start date (yyyymmdd or yyyyddd). Bypasses the default 7-day buffer.
- **TDATE**: Explicit tillage date (yyyymmdd or yyyyddd). If this date precedes the simulated start date, the engine will safely step the simulation start date back to accommodate it.

### Irrigation Directives
Irrigation column values:
- **IR**: Irrigated
- **RF**: Rainfed
- **(blank)**: Defaults to the management protocol defined in the base crop experiment file.

**IRRIG_SCHEDULE** column (strictly read only when Irrigation = IR):
- **(blank)**: Automatic irrigation based on internal DSSAT thresholds
- **DAS-mm;DAS-mm;...**: Scheduled irrigation on exact days
  * *Example:* `0-50;3-50;15-50` denotes Day 0: 50mm, Day 3: 50mm, Day 15: 50mm

### Fertilizer Directives
Fertilizer column values:
- **yes**: Apply fertilizer using the N/P/K schedule columns
- **no**: No fertilizer applied, all N/P/K schedules are bypassed

**N_application, P_application, K_application** columns:
- **Format:** DAS-kg_per_ha;DAS-kg_per_ha;...
  * *Example:* `0-62.5;25-62.5` denotes Day 0: 62.5 kg/ha N, Day 25: 62.5 kg/ha N

### Harvest Directives (Optional)
- **Harvest_mode**: Defines the harvest trigger mechanism. Options include:
  - `M`: Automatic harvest at physiological maturity (Default if left blank).
  - `A`: Automatic harvest based on internal crop-specific rules.
  - `R`: Reported calendar date.
- **HDATE_DAS**: Days After Sowing (DAS) to execute the harvest. *Mandatory if `Harvest_mode` is set to `R`.* Example: `120`.

### Simulation & Environmental Methods (Optional)
Overrides the internal physics and environment switches normally locked in the base file:
- **CO2**: Override baseline CO2 (`M` = Default 380vpm, `D` = Keeling curve, `W` = Read from weather file)
- **EVAPO**: Evapotranspiration Method (`R` = Priestley-Taylor/Ritchie, `F` = FAO-56)
- **INFIL**: Infiltration Method (`S` = Soil Conservation Service, `R` = Ritchie)
- **PHOTO**: Photosynthesis Method (`C` = Canopy curve daily, `L` = Leaf hourly)

### Schedule Column Formatting Directives (Critical Prevention)
* **Event Delimiter:** Semicolon (`;`)
* **Value Delimiter:** Hyphen (`-`) for Nutrients/Irrigation schedules.
* **DAS Definition:** Days After Sowing/Planting (can be negative for pre-planting actions).
* **Excel Cell Formatting:** To prevent Excel from automatically executing mathematical formulas (e.g., calculating a `-1-17` schedule as `-18`), all schedule cells **must be formatted explicitly as Text** prior to data entry, or prefixed with an apostrophe (`'`).