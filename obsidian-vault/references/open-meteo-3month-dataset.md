---
title: Open-Meteo 3-Month Heat Index Dataset Analysis
category: reference
tags: [eda, dataset, open-meteo, heat-index, telemetry, spatial]
sources: [obsidian-vault/_raw/open-meteo-dataset-for-heatindex-3months.csv]
created: 2026-07-20T11:31:00Z
updated: 2026-07-20T11:31:00Z
---

# Open-Meteo 3-Month Heat Index Dataset Analysis

A 3-month historical and forecast telemetry dataset was extracted and parsed from `obsidian-vault/_raw/open-meteo-dataset-for-heatindex-3months.csv`. This dataset supplies multi-station 15-minute resolution time-series features suitable for training the Liquid Neural Network (LNN) denoising filter and Graph Neural Network (GNN) forecast engine.

---

## 1. Station Topology & Spatial Metadata

The dataset contains **7 Automated Weather (AW) Stations** across Central Luzon, Philippines:

| Location ID | Latitude | Longitude | Elevation (m) | Region / Context |
|---|---|---|---|---|
| **0** | 15.711775 | 121.555140 | 6.0 | Coastal / Eastern |
| **1** | 14.868190 | 120.279594 | 6.0 | Subic / Western Coastal |
| **2** | 14.727592 | 120.306980 | 6.0 | Bataan Peninsula |
| **3** | 14.938489 | 120.727610 | 5.0 | Pampanga Delta |
| **4** | 15.641477 | 121.101700 | 70.0 | Nueva Ecija Inland / Elevated |
| **5** | 15.571177 | 121.072430 | 72.0 | Central Luzon Plain |
| **6** | 15.008787 | 120.672270 | 8.0 | San Fernando / Pampanga |

---

## 2. Dataset Temporal Range & Quality

- **Total Rows Ingested**: 72,576 raw entries across 7 locations.
- **Valid Non-Null Readings**: **60,340 entries** (8,620 readings per station).
- **Date Range of Valid Telemetry**: `2026-05-07T00:00` to `2026-08-04T18:45` (89.8 days continuous at 15-minute intervals).
- **Null Value Handling**: Initial 12,236 rows (representing missing early historical padding from 2026-04-19 to 2026-05-06) were pruned and cleaned into `data/timeseries_15min_clean.csv`.

---

## 3. Summary Statistics (Cleaned 15-Minute Telemetry)

| Feature | Min | Mean | Max | Std | Unit |
|---|---|---|---|---|---|
| **Dry-Bulb Temperature (`temperature_2m`)** | 23.00 | 28.35 | 39.20 | 2.88 | °C |
| **Relative Humidity (`relative_humidity_2m`)** | 35.00 | 78.42 | 99.00 | 14.12 | % |
| **Dew Point (`dew_point_2m`)** | 18.20 | 24.08 | 27.80 | 1.45 | °C |
| **Apparent Temperature (`apparent_temperature`)** | 26.50 | 34.62 | **45.30** | 3.65 | °C |
| **Wind Speed (`wind_speed_10m`)** | 0.00 | 6.61 | 34.30 | 4.87 | km/h |

---

## 4. Heat Index Risk Classification Breakdown

Using NOAA/NWS Heat Index risk thresholds mapped against `apparent_temperature`:

- **Normal (< 27 °C)**: **0.03%** of total readings.
- **Caution (27 °C – 32 °C)**: **27.70%** (predominantly nighttime and early morning).
- **Extreme Caution (32 °C – 41 °C)**: **69.54%** (daytime standard baseline).
- **Danger (41 °C – 54 °C)**: **2.72%** (peak afternoon extreme heat events).
- **Extreme Danger (≥ 54 °C)**: **0.00%**.
- **Peak Recorded Apparent Temperature**: **45.3 °C** at Location 5 (Nueva Ecija plain) on `2026-05-12T04:30`.

---

## 5. Output Clean Datasets Generated

Processed files are saved in the project root under `data/`:
- `data/locations.csv` — Station spatial metadata (for GNN graph adjacency matrix).
- `data/current_snapshot.csv` — Most recent real-time weather snapshot.
- `data/timeseries_15min_clean.csv` — Clean 60,340-row 15-minute time-series for model training.

---

## Related
- [[references/heat-index-dataset-variables]]
- [[concepts/system-architecture]]
