---
title: Kloudtech Telemetry & Heat Index API Specification
category: reference
tags: [api, openapi, kloudtech, telemetry, auth, endpoints, fastapi]
sources: [Kloudtech API Documentation, src/api/routes.py]
created: 2026-07-20T11:49:00Z
updated: 2026-07-20T11:49:00Z
---

# Kloudtech Telemetry & Heat Index API Specification

This reference details the REST API specification, security headers, data schemas, and microservice endpoints implementing the **Kloudtech Telemetry API** and **LNN Heat Index Prediction Engine**.

---

## 1. Authentication & Security

* **Base URL**: `https://api.kloudtechsea.com/api/v1`
* **Header Name**: `x-kloudtrack-key` (Required)
* **Fallback Header**: `x-api-key`
* **Rate Limit**: 20 requests per minute per account.
* **Unauthorized Error (401)**: Returned when the `x-kloudtrack-key` header is missing or invalid.

### Recommended Production Integration Flow
To protect private API keys and manage rate-limit quotas, browser and client apps must not call KloudTrack directly. Instead, requests route through the backend proxy & cache layer:

```
Client App  ──>  Client Backend / Proxy Cache Layer (`src/api/client.py`)  ──>  KloudTrack API (`https://api.kloudtechsea.com/api/v1`)
```
* **Benefits**: Keeps API keys private, eliminates duplicate client-side requests, enforces in-memory response caching (TTL: 60s), and guarantees reliable quota management.

---

## 2. Standard API Response Envelope

All API endpoints return responses wrapped in a unified JSON envelope:

```json
{
  "success": true,
  "message": "Dashboard telemetry retrieved successfully",
  "data": { ... }
}
```

---

## 3. Implemented Endpoints & Routes

| Method | Endpoint | Authorization | Description |
|---|---|---|---|
| `GET` | `/health` | None | Service health, version, and status check. |
| `GET` | `/telemetry/dashboard` | `x-kloudtrack-key` | Returns all stations accessible to the user with their latest telemetry snapshot. |
| `GET` | `/telemetry/station/{stationId}/current` | `x-kloudtrack-key` | Retrieves latest single telemetry reading for a given station hashid. |
| `GET` | `/telemetry/station/{stationId}/history` | `x-kloudtrack-key` | Returns paginated time-series telemetry (`skip`, `take`, `interval`, `startDate`, `endDate`). |
| `GET` | `/telemetry/station/{stationId}/history/{variable}` | `x-kloudtrack-key` | Returns single-metric historical time-series (`temperature`, `humidity`, `pressure`, `heatIndex`, `windSpeed`). |
| `GET` | `/telemetry/record/{id}` | `x-kloudtrack-key` | Retrieves a single telemetry record by numeric ID. |
| `POST` | `/api/v1/heat-index/calculate` | `x-kloudtrack-key` | Computes instant Rothfusz Heat Index & risk level from temperature and humidity inputs. |

---

## 4. Key Pydantic Data Schemas (`src/api/schemas.py`)

```python
class WeatherStationApiReading(BaseModel):
    id: int
    recordedAt: str
    createdAt: str
    temperature: float
    humidity: float
    dewPoint: Optional[float]
    apparentTemperature: Optional[float]
    heatIndex: Optional[float]
    windSpeed: Optional[float]
    windDirection: Optional[float]
    pressure: Optional[float]
```

---

## Related
- [[references/heat-index-dataset-variables]]
- [[references/open-meteo-3month-dataset]]
- [[concepts/system-architecture]]
