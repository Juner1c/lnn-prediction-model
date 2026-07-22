# Plan 021 — Real Kloudtech API Ingestion & System Audit Remediation

**Goal**: Eliminate hardcoded station placeholders (`st_0`, `st_1`, "Subic Bay Observatory", etc.) and fake test passes across the microservice. Dynamically ingest real weather stations, telemetry metrics, and 24-hour historical time-series arrays exclusively from the live **Kloudtech Telemetry API** (`https://api.kloudtechsea.com/api/v1`).

---

## 1. Audit Findings & Root Causes

1. **Hardcoded Station Disconnect**: `src/api/routes.py` hardcoded `CENTRAL_LUZON_STATIONS` (`st_0`..`st_6`). When querying live Kloudtech API, real IDs (`Rjz2dbXW`, `4VAl2p9k`, `3nzr8bGo`, etc.) were returned, causing `readings.get("st_0")` to return `None` and fall back to dummy arrays `[30.0]*96`. Real telemetry was ignored.
2. **Missing 24h History Ingestion**: Kloudtech `/telemetry/dashboard` returns snapshot telemetry, not 24h history. 24h history must be fetched via `/telemetry/station/{id}/history?take=96`.
3. **Station Index Hacking**: `station.id.split("_")[-1]` evaluated to `0` for all hashIDs (`Rjz2dbXW`), causing all station forecasts to read index 0.
4. **Fake Test Passes**: `tests/test_api.py` used a fake key `"kloudtrack_secret_key_123"` and dummy station IDs (`st_0`, `st_1`), missing real Kloudtech response validation.
5. **Frontend Absolute URL Refusal**: `static/app.js` used `http://127.0.0.1:8000` causing connection refused errors when server wasn't running on 8000, and had default station ID `"st_1"`.

---

## 2. Proposed Remediation

- **`src/api/client.py`**: Add `fetch_station_history(station_id, take=96)` method to fetch time-series history arrays from Kloudtech API.
- **`src/api/routes.py`**:
  - Remove `CENTRAL_LUZON_STATIONS` and `fetch_live_openmeteo_station_telemetry()` stub.
  - Rename `load_real_openmeteo_telemetry()` to `load_real_kloudtech_telemetry()`.
  - Fetch 24-hour history for each active station via `proxy_client.fetch_station_history()`.
  - Dynamically construct STGNN 3D input tensor `[nodes, 96, 5]` from real Kloudtech history.
  - Dynamically compute STGNN spatial graph adjacency matrix from active Kloudtech station coordinates `[lat, lon]`.
  - Map `stationId` to exact active station list index in forecast route.
- **`static/app.js`**: Use clean relative paths `/telemetry/...` and set `activeStationId` dynamically to `data[0].station.id`.
- **`tests/test_api.py`**: Update tests to validate real Kloudtech station data and headers with 100% compliance.

---

## 3. Verification Plan
1. Run `python -m unittest discover tests`.
2. Execute API verification snippets testing live Kloudtech station telemetry ingestion & 24h history tensor construction.
