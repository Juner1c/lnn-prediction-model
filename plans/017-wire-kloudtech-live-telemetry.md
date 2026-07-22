# Plan 017 — Wire Kloudtech Remote Live Telemetry API into Microservice Pipeline

**Goal**: Integrate the remote Kloudtech Telemetry API (`https://api.kloudtechsea.com/api/v1`) via `KloudtechProxyClient` into `src/api/routes.py` for live station telemetry ingestion with fallback to Open-Meteo and local CSV.

---

## 1. Current State
- `src/api/client.py` contains `KloudtechProxyClient` configured with `KLOUDTECH_BASE_URL` and `KLOUDTRACK_API_KEY` from `src/api/config.py`.
- `src/api/routes.py` fetches live weather telemetry primarily from Open-Meteo API with fallback to `data/timeseries_15min_clean.csv`.
- `KloudtechProxyClient` is initialized but not yet actively called inside the telemetry loading pipeline in `routes.py`.

---

## 2. Proposed Changes

### `src/api/client.py`
- Enhance `fetch_with_cache` to support optional query headers (`x-kloudtrack-key`) and custom timeouts.
- Add helper method `fetch_station_current(station_id: str)` and `fetch_dashboard_telemetry()` targeting `https://api.kloudtechsea.com/api/v1`.

### `src/api/routes.py`
- Integrate `proxy_client` at the top of `load_real_openmeteo_telemetry()`:
  - If `KLOUDTRACK_API_KEY` is set and valid, attempt fetching live station telemetry from Kloudtech remote API.
  - If Kloudtech remote API returns 200 with valid station readings, parse and cache them into station readings format.
  - Fall back gracefully to Open-Meteo live API and local CSV dataset if remote endpoint is unreachable or pending.

### `tests/test_api.py`
- Update proxy client unit tests to verify remote endpoint query construction, caching TTL, and authorization header injection.

---

## 3. Verification Plan
1. Run `python -m unittest discover tests` — all unit tests must pass.
2. Verify fallback hierarchy (Kloudtech API -> Open-Meteo -> Local CSV) returns consistent 7-station schemas for STGNN forecast tensor construction.
