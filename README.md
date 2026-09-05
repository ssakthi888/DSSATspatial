# DSSATspatial

A robust, spatially-aware Python package designed to streamline and automate high-performance, multi-threaded batch processing for DSSAT (Decision Support System for Agrotechnology Transfer). 

## Overview
Refactored for Python 3.12+ compatibility, `DSSATspatial` provides a flattened, modular architecture for creating, managing, and simulating agricultural experiments across large spatial datasets. It natively supports multi-core execution for regional-scale agroecosystem modeling.

## Core Features
* **Batch Processing Engine:** Concurrent execution architecture utilizing multi-threading for rapid simulation across thousands of regional grid points.
* **Automated File Generation:** Dynamically generate FileX, `.WTH`, `.SOL`, `.SPE`, and `.CUL` configurations for multiple crops (including Maize, Rice, and Sorghum).
* **Spatial Data Integration:** Seamlessly maps coordinates, weather stations, and soil  profiles to their respective spatial simulation units.
* **Robust Environment Handling:** Dynamically maps to DSSAT versions 4.8.0 and 4.8.5.