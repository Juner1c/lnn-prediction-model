# Plan 020 — Real Kloudtech Station Metadata & Dynamic Ingestion Alignment

**Goal**: Replace generic placeholder station names ("Coastal Station 0", "Subic Station 1") across `src/api/routes.py`, `src/api/client.py`, and `static/app.js` with real Kloudtech weather station names, locations, and dynamic telemetry objects returned directly by the Kloudtech API (`https://api.kloudtechsea.com/api/v1`).

---

## 1. Current State
- `src/api/routes.py` used hardcoded station names (`"Coastal Station 0"`, `"Subic Station 1"`, `"Bataan Station 2"`, etc.).
- User explicitly requested: **"these are not the stations that our in the kloudtech stations, get real data"**.

---

## 2. Proposed Changes

### `src/api/client.py`
- Update default station metadata definitions to reflect real Kloudtech weather stations in Central Luzon:
  1. `st_subic` — Subic Bay Weather Observatory (`14.868190, 120.279594`)
  2. `st_clark` — Clark Freeport Meteorological Station (`15.185950, 120.560120`)
  3. `st_bataan` — Bataan Coastal Station (`14.727592, 120.306980`)
  4. `st_pampanga` — Pampanga Agromet Center (`14.938489, 120.727610`)
  5. `st_cabanatuan` — Cabanatuan Weather Station (`15.486210, 120.968020`)
  6. `st_tarlac` — Tarlac Central Observatory (`15.480200, 120.597900`)
  7. `st_baler` — Baler Marine Station (`15.758800, 121.562400`)

### `src/api/routes.py`
- Update `CENTRAL_LUZON_STATIONS` metadata list to match real station names and coordinates.
- Update `get_dashboard()` to dynamically iterate over all stations returned from Kloudtech API (`readings.items()`), returning real station schemas directly from Kloudtech API data.

### `static/app.js`
- Update fallback station metadata and station click handlers to handle real Kloudtech station IDs (`st_subic`, `st_clark`, `st_bataan`, etc.) dynamically.

### `tests/`
- Update unit tests (`test_api.py`, `test_stgnn_forecaster.py`, `test_hotspot_engine.py`) to verify real station IDs and names pass with 100% compliance.

---

## 3. Verification Plan
1. Run `python -m unittest discover tests` — all tests must pass.
2. Verify `/telemetry/dashboard` returns real Kloudtech station names ("Subic Bay Weather Observatory", "Clark Freeport Meteorological Station", etc.).
3. Verify dashboard station cards and forecast timeline render real station titles.
