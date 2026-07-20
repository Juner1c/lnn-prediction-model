---
title: Heat Index Dataset Variables Specification
category: reference
tags: [heat-index, datasets, variables, telemetry, open-meteo]
sources: [Open-Meteo API Selector]
created: 2026-07-20T11:21:00Z
updated: 2026-07-20T11:21:00Z
---

# Heat Index Dataset Variables Specification

To accurately calculate and forecast the **Heat Index (Apparent Temperature)** and related thermal comfort metrics (such as Wet Bulb Temperature and WBGT), the system requires specific primary and environmental features from Open-Meteo / AW Station APIs.

---

## 1. Current Weather (Real-Time Telemetry & Monitoring)

### Essential (Core Heat Index Calculation)
- **Temperature (2 m)**: Ambient dry-bulb air temperature at 2 meters.
- **Relative Humidity (2 m)**: Air moisture percentage required for Rothfusz & NWS Heat Index equations.
- **Apparent Temperature**: Ground-truth / baseline apparent temperature provided by the source.
- **Wind Speed (10 m)**: Surface wind speed (mitigates apparent heat via convective cooling).

### Secondary (Convective & Pressure Context)
- **Surface Pressure** or **Sea Level Pressure**: Needed for psychrometric equations and dewpoint conversion.
- **Wind Direction (10 m)** & **Wind Gusts (10 m)**: Micro-climate thermal transport factors.
- **Is Day or Night**: Indicates diurnal solar radiation status.

---

## 2. 15-Minutely Weather Variables (High-Resolution LNN Denoising Input)

### Essential (High-Frequency Heat Metrics)
- **Temperature (2 m)**
- **Relative Humidity (2 m)**
- **Dewpoint (2 m)**: Direct indicator of atmospheric moisture; essential fallback when RH fluctuates.
- **Apparent Temperature**
- **Wind Speed (10 m)**

### Secondary (Solar Radiation & Heat Load Factors)
- **Shortwave Solar Radiation GHI (Global Horizontal Irradiance)**: Direct ground heat load.
- **Direct Solar Radiation** & **Diffuse Solar Radiation DHI**: Differentiates direct sun heat load vs shaded heat.
- **Wind Gusts (10 m)**
- **Is Day or Night**
- **Visibility**

---

## 3. Hourly Weather Variables (GNN Spatial-Temporal Model Input)

### Essential (Core Model Features)
- **Temperature (2 m)**
- **Relative Humidity (2 m)**
- **Dewpoint (2 m)**
- **Apparent Temperature**
- **Vapour Pressure Deficit**: Key metric for evaporation rate and body heat dissipation capacity.
- **Wind Speed (10 m)**

### Secondary (Environmental & Ground Thermal Mass)
- **Surface Pressure**
- **Cloud Cover Total**: Directly impacts solar radiation reaching the surface.
- **Soil Temperature (0 cm & 6 cm)**: Ground heat storage contributing to ambient heat radiation.
- **Soil Moisture (0-1 cm)**: Evaporative cooling capacity of the surrounding ground.

---

## 4. Daily Weather Variables (Macro Trend & Extremes Evaluation)

### Essential (Daily Heat Extreme Metrics)
- **Maximum Temperature (2 m)**
- **Minimum Temperature (2 m)**
- **Maximum Apparent Temperature (2 m)**: Daily peak heat index benchmark.
- **Minimum Apparent Temperature (2 m)**: Nighttime recovery benchmark.
- **UV Index**: Daily maximum solar ultraviolet intensity.

### Secondary (Diurnal Energy Balance)
- **Daylight Duration** & **Sunshine Duration**: Total solar exposure hours per day.
- **Shortwave Radiation Sum**: Cumulative daily solar energy influx.
- **Precipitation Sum**: Indicates cooling events and moisture recharge.

---

## 5. Additional Variables & Advanced Thermal Metrics

### Essential (Advanced Heat Stress Metrics)
- **Wet Bulb Temperature (2 m)**: Crucial for calculating Wet-Bulb Globe Temperature (WBGT) and human heat threshold limits.
- **Total Column Integrated Water Vapour**: Measures total atmospheric column moisture (correlates with heat retention).

### Secondary (Atmospheric Instability & Convection)
- **UV Index** & **UV Index Clear Sky**
- **CAPE (Convective Available Potential Energy)**: Tracks thermal atmospheric instability and heat thunderstorm potential.
- **Boundary Layer Height PBL**: Height of mixed layer trapping heat near the surface.
