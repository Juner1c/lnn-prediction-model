---
title: Deterministic Heat-Index & Thermal Comfort Calculator Module
category: concept
tags: [heat-index, rothfusz, lu-romps, stull, wet-bulb, apparent-temperature, deterministic]
sources: [src/data/heat_index.py, tests/test_heat_index.py]
created: 2026-07-20T12:19:00Z
updated: 2026-07-20T12:19:00Z
---

# Deterministic Heat-Index & Thermal Comfort Calculator Module

This concept note details the deterministic mathematical equations and algorithms implemented in `src/data/heat_index.py` for Heat Index and apparent temperature calculation.

---

## 1. Implemented Algorithms

### NOAA NWS Rothfusz Regression (`calculate_heat_index`)
Polynomial regression model estimating human-perceived temperature from dry-bulb temperature $T$ (°F) and relative humidity $RH$ (%):

$$\text{HI} = -42.379 + 2.049 T + 10.143 RH - 0.224 T \cdot RH - 0.0068 T^2 - 0.0548 RH^2 + 0.00122 T^2 RH + 0.00085 T RH^2 - 0.00000199 T^2 RH^2$$

Includes NWS low-humidity and high-humidity adjustment factors.

### Lu & Romps / Steadman Apparent Temperature (`calculate_apparent_temp_lu_romps`)
Calculates apparent thermal stress using vapor pressure $e$ derived from dew point $T_{dp}$:

$$e = 6.112 \cdot \exp\left(\frac{17.67 \cdot T_{dp}}{T_{dp} + 243.5}\right)$$

$$\text{AT} = T + 0.33 e - 0.70 v_{\text{m/s}} - 4.0$$

* **Benchmark result**: 30 °C dry-bulb temp / 25 °C dew point (74.5% RH) $\rightarrow$ **36.45 °C** apparent temperature.

### Stull Empirical Wet-Bulb Temperature (`calculate_wet_bulb_stull`)
Estimates wet-bulb temperature $T_w$ without iterative psychrometric chart solving:

$$T_w = T \cdot \text{atan}(0.151977 \sqrt{RH + 8.313659}) + \text{atan}(T + RH) - \text{atan}(RH - 1.676331) + 0.00391838 RH^{1.5} \text{atan}(0.023101 RH) - 4.686035$$

### Vectorized Array Computation (`calculate_heat_index_batch`)
NumPy-optimized vectorized execution over thousands of weather station array time slices simultaneously.

---

## 2. NOAA Risk Categorization (`get_heat_risk_category`)

| Heat Index Range (°C) | Risk Level |
|---|---|
| $< 27.0\text{ }^\circ\text{C}$ | `Normal` |
| $27.0 - 31.9\text{ }^\circ\text{C}$ | `Caution` |
| $32.0 - 40.9\text{ }^\circ\text{C}$ | `Extreme Caution` |
| $41.0 - 53.9\text{ }^\circ\text{C}$ | `Danger` |
| $\ge 54.0\text{ }^\circ\text{C}$ | `Extreme Danger` |

---

## Related
- [[references/heat-index-dataset-variables]]
- [[concepts/system-architecture]]
- [[concepts/lfm-vs-baseline-comparison]]
