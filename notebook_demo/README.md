# Demonstration Directory: Sample Notebooks and Master Matrix

This directory contains sample Jupyter notebooks and a template execution matrix (`master_matrix_template.xlsx`) required to test the `DSSATspatial` batch processing workflows. The spatial modeling pipeline is driven by this primary Excel dataset and is designed to be fully crop-specific. 

The following rules specify the parameterization of the master sheet for any supported DSSAT crop model.

## Master Sheet: Column Guide

### General Parameters
* **treatment**: Treatment number (1, 2, 3, ...)
* **weather**: Weather station file code (e.g., TN012019)
* **soil**: Soil profile ID (e.g., IN04184856)
* **cultivar**: Crop-specific variety/cultivar code (e.g., Ganga for Maize, IR64 for Rice)
* **planting_date**: Planting date, supports standard format yyyymmdd (e.g., 20221022) or Julian format yyyyddd (e.g., 2001161)
* **PLPOP**: Seed population at planting, plants/m2
* **PPOE**: Emergence population, plants/m2
* **PLRS**: Row spacing, cm
* **PLDP**: Planting depth, cm
* **NYEARS**: Number of years to simulate (e.g., 1, 2)

### Irrigation Directives
Irrigation column values:
* **IR**: Irrigated
* **RF**: Rainfed
* **(blank)**: Defaults to the management protocol defined in the base crop experiment file (e.g., `.MZX` for Maize, `.RIX` for Rice, `.WHX` for Wheat)

**IRRIG_SCHEDULE** column (strictly read only when Irrigation = IR):
* **(blank)**: Automatic irrigation based on internal DSSAT thresholds
* **DAS-mm;DAS-mm;...**: Scheduled irrigation on exact days
  * *Example:* `0-50;3-50;15-50` denotes Day 0: 50mm, Day 3: 50mm, Day 15: 50mm
* *Note:* If Irrigation = RF, the IRRIG_SCHEDULE column is completely bypassed by the parser.

### Fertilizer Directives
Fertilizer column values:
* **yes**: Apply fertilizer using the N/P/K schedule columns
* **no**: No fertilizer applied, all N/P/K schedules are bypassed

**N_application, P_application, K_application** columns:
* **Format:** DAS-kg_per_ha;DAS-kg_per_ha;...
  * *Example:* `N_application = 0-62.5;25-62.5` denotes Day 0: 62.5 kg/ha N, Day 25: 62.5 kg/ha N
* **Valid Configurations:**
  1. `Fertilizer = yes` with at least one nutrient column (N, P, or K) populated.
  2. `Fertilizer = no` with all nutrient columns left explicitly blank.
* *Note:* The package does not support an automatic fertilizer algorithm. Setting Fertilizer to `yes` while leaving all three nutrient columns blank will result in an execution error.

### Schedule Column Formatting Directives
*(Applies universally to IRRIG_SCHEDULE, N_application, P_application, K_application)*

* **Event Delimiter:** Semicolon (`;`)
* **Value Delimiter:** Hyphen (`-`)
  * *Warning:* Avoid using a colon (`:`). Excel auto-formats colons into unsupported time variables.
* **DAS Definition:** Days After Sowing/Planting
* Leave the entire column blank if an application is not required for a specific treatment row.

### Excel Cell Formatting (Critical Prevention)
To prevent Excel from automatically executing mathematical formulas or altering temporal structures (e.g., calculating a `-1-17` schedule as `-18`), all cells within the master execution matrix must be formatted explicitly as **Text** prior to data entry. Alternatively, users can enforce raw string retention by prepending an apostrophe to the entry (e.g., `'-1-17`).