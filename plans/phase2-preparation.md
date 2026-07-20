# Implementation Plan: Phase 2 Preparation (Kloudtech Telemetry API & FastAPI Service)

Phase 2 implements the OpenAPI specification, authentication middleware, data schemas, and microservice endpoints aligned with the **Kloudtech Telemetry API** specification (`x-kloudtrack-key` authorization, rate-limiting, and response shapes).

---

## 1. Kloudtech API Specification & Response Shapes

Authentication Header: `x-kloudtrack-key: <API_KEY>`  
Rate Limit Target: 20 requests per minute per account.

### Standard Response Envelope
```json
{
  "success": true,
  "message": "Telemetry retrieved successfully",
  "data": { ... }
}
```

### Key Endpoints to Implement in FastAPI:
1. `GET /telemetry/dashboard` — Returns all accessible weather stations paired with their latest telemetry snapshot.
2. `GET /telemetry/station/{stationId}/current` — Returns the single most recent telemetry reading for a given station.
3. `GET /telemetry/station/{stationId}/history` — Returns paginated/downsampled historical telemetry (`skip`, `take`, `interval`, `startDate`, `endDate`, `filterOutliers`).
4. `GET /telemetry/station/{stationId}/history/{variable}` — Returns single-metric historical time-series (`temperature`, `humidity`, `pressure`, `heatIndex`, `windSpeed`, `windDirection`, etc.).
5. `GET /telemetry/record/{id}` — Retrieves a single telemetry record by numeric ID.
6. `POST /api/v1/heat-index/calculate` — Computes instant NWS Rothfusz Heat Index.
7. `GET /api/v1/forecast/{stationId}` — 24-hour LNN/GNN Heat Index forecast endpoint.

---

## 2. Proposed Component Implementation

### `src/api/schemas.py`
- Pydantic models matching Kloudtech types:
  - `StationInfo` (`id`, `name`, `latitude`, `longitude`, `elevation`, `organizationId`).
  - `WeatherStationApiReading` (`id`, `recordedAt`, `createdAt`, `temperature`, `humidity`, `dewPoint`, `apparentTemperature`, `heatIndex`, `windSpeed`, `windDirection`, `pressure`).
  - `VariableReading` (`id`, `recordedAt`, `createdAt`, `value`).
  - `WeatherStationDashboardEntry` (`station`, `telemetry`).
  - `KloudtrackResponse[T]` generic envelope (`success`, `message`, `data`).

### `src/api/auth.py`
- FastAPI `Security` dependency inspecting header `x-kloudtrack-key` (and `x-api-key` fallback). Returns 401 Unauthorized if missing or invalid.

### `src/api/routes.py` & `src/api/main.py`
- Implements all Kloudtech telemetry routes and Heat Index calculation/forecast routes using FastAPI.

### `tests/test_api.py`
- Comprehensive `unittest` suite testing 401 Unauthorized rejection, 200 OK responses, Pydantic validation, and Heat Index calculations.

---

## 3. Verification Plan

- Run `python -m unittest discover tests` to verify 100% test pass rate.
- Generate `obsidian-vault/references/kloudtech-api-specification.md` in knowledge vault.
