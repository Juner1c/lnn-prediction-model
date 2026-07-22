# Plan 018 — Kloudtech API Direct Ingestion & Active Station Verification (No Open-Meteo)

**Goal**: Discontinue external Open-Meteo HTTP API queries, relying exclusively on Kloudtech API (`https://api.kloudtechsea.com/api/v1`) for real-time station telemetry, station active status detection, and API functionality verification with local CSV fallback.

---

## 1. Current State
- `src/api/routes.py` previously attempted Kloudtech API ingestion first, but fell back to querying `https://api.open-meteo.com/v1/forecast` over HTTP if Kloudtech data was pending.
- User explicitly mandated: **"no open-meteo just Kloudtech API, use its data so we know what stations are active right now and so we know the API is functional"**.

---

## 2. Proposed Changes

### `src/api/routes.py`
1. **Remove Open-Meteo HTTP Fetch Calls**:
   - Deprecate `fetch_live_openmeteo_station_telemetry()` so no outbound traffic goes to `api.open-meteo.com`.
2. **Kloudtech API Data Ingestion & Active Status Marking**:
   - Query Kloudtech API via `proxy_client.fetch_with_cache("/telemetry/dashboard")` (or station endpoints).
   - If Kloudtech API returns station readings, mark stations as `is_active: True`, `status: "online"`, `source: "Kloudtech API"`.
   - If a station is not returned or key is missing, fallback directly to local clean CSV (`data/timeseries_15min_clean.csv`) marked as `is_active: False`, `source: "Local CSV Fallback"`.
3. **API Response Enhancement**:
   - Include `api_status`, `active_source`, and `active_stations_count` metadata in `/telemetry/dashboard` and `/telemetry/station/{stationId}/current` responses to clearly signify Kloudtech API status.
4. **Physical Thermodynamic Diurnal Baseline for Forecasts**:
   - Compute STGNN 16-day forecasts using latest Kloudtech/CSV station metrics and physical thermodynamic diurnal curves (`calculate_heat_index`), avoiding external Open-Meteo dependencies.

### `tests/test_api.py`
- Verify that `/telemetry/dashboard` returns valid station data and Kloudtech proxy metadata without invoking Open-Meteo HTTP calls.
- Verify unit tests pass with 100% compliance.

---

## 3. Verification Plan
1. Run `python -m unittest discover tests` — ensure all 37 tests pass.
2. Confirm zero HTTP calls are initiated toward `api.open-meteo.com`.
3. Verify `/telemetry/dashboard` returns station telemetry with active station indicators and Kloudtech API integration status.
