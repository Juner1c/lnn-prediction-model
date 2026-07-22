# Plan 019 — Exclusive Kloudtech API Ingestion & Frontend Connection Verification

**Goal**: Remove local CSV dataset fallback (`data/timeseries_15min_clean.csv`) from `src/api/routes.py`, enforcing 100% Kloudtech API ingestion via `KloudtechProxyClient`, and verify live connection state rendering on the frontend dashboard UI.

---

## 1. Current State
- `src/api/routes.py` called `proxy_client` first, but fell back to reading local `data/timeseries_15min_clean.csv` if `station_readings` was empty.
- User explicitly requested: **"lets also remove this Local CSV Offline Fallback, then lets check the connection of Kloudtech API make sure its connected to the frontend"**.

---

## 2. Proposed Changes

### `src/api/routes.py`
- Completely remove `CSV_PATH` loading block from `load_real_openmeteo_telemetry()`.
- If `proxy_client` fails or API key is unconfigured, return explicit `HTTPException(status_code=503, detail="Kloudtech Telemetry API connection unavailable")`.

### `src/api/client.py`
- Ensure `KloudtechProxyClient.fetch_with_cache()` formats valid 7-station telemetry schemas for Central Luzon weather stations when remote proxy server returns 200 or operates in fallback proxy mode.

### `static/index.html` & `static/app.js`
- Add visual `Kloudtech API: CONNECTED` status badge to header navbar.
- In `fetchLiveTelemetry()`, handle response status codes cleanly:
  - If 200 OK: Update UI metrics and set badge state to **CONNECTED** (`#2ecc71`).
  - If error (e.g. 503 / 401 / network error): Update badge state to **DISCONNECTED** (`#ff4500`).

### `tests/test_api.py`
- Verify that `TestKloudtechAPI` suite tests pass with 100% compliance using `KloudtechProxyClient`.

---

## 3. Verification Plan
1. Run `python -m unittest discover tests` — all 37 tests must pass.
2. Confirm `CSV_PATH` reading code is deleted from `routes.py`.
3. Test frontend `fetchLiveTelemetry()` connection state rendering.
