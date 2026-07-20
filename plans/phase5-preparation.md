# Implementation Plan: Phase 5 (Heat-Index Module Integration)

Phase 5 expands the **Deterministic Heat-Index Calculation Module** (`src/data/heat_index.py`) to support Lu & Romps apparent temperature formulas, Wet-Bulb Temperature estimations, NOAA NWS Rothfusz regressions, vectorized array processing for high-throughput batching, and risk level categorization.

---

## Objectives of Phase 5

1. **Enhanced Deterministic Calculator (`src/data/heat_index.py`)**:
   - Rothfusz NWS Heat Index regression.
   - Lu & Romps / Steadman Apparent Temperature algorithm (incorporating temperature, humidity, dew point, and wind speed).
   - Stull's Wet Bulb Temperature approximation formula.
   - Vectorized batch computation (`calculate_heat_index_batch`).
   - Categorization helper (`get_heat_risk_category`).
2. **Expanded Test Suite (`tests/test_heat_index.py`)**:
   - Test baseline input (e.g., 30°C temp / 25°C dew point -> ~33°C apparent temp).
   - Test Rothfusz extremes, Wet-Bulb approximations, and vectorized array operations.
3. **Knowledge Vault Preservation**:
   - Create `obsidian-vault/concepts/heat-index-calculator-module.md`.
   - Update `obsidian-vault/index.md`, `log.md`, and `hot.md`.

---

## Component Details

### `src/data/heat_index.py`
- `calculate_heat_index(temp_c, rh)`: NWS Rothfusz formula.
- `calculate_apparent_temp_lu_romps(temp_c, dew_point_c, wind_speed_kmh)`: Lu & Romps / Steadman apparent temperature.
- `calculate_wet_bulb_stull(temp_c, rh)`: Stull empirical Wet-Bulb equation.
- `calculate_heat_index_batch(temps, rhs)`: NumPy vectorized array function.
- `get_heat_risk_category(hi_c)`: Maps °C to NOAA risk strings.

### `tests/test_heat_index.py`
- Validates 30°C / 25°C dew point -> ~33°C apparent temp benchmark.
- Validates Wet Bulb, Rothfusz regression edge cases, and batch execution.

---

## Verification Plan

### Automated Verification
- Run `python -m unittest discover tests` (100% pass rate).

### Knowledge Vault Update
- Create `obsidian-vault/concepts/heat-index-calculator-module.md`.
- Update `index.md`, `log.md`, and `hot.md`.
