---
title: Data Ingestion & Quality Validation Architecture
category: reference
tags: [ingestion, telemetry, validation, storage, s3, partitioned-storage]
sources: [src/data/validator.py, src/data/storage_adapter.py, src/data/ingestion_client.py]
created: 2026-07-20T12:13:00Z
updated: 2026-07-20T12:13:00Z
---

# Data Ingestion & Quality Validation Architecture

This reference documents the telemetry ingestion pipeline, data quality validation rules, and partitioned storage adapters (local & Amazon S3) implemented in Phase 3.

---

## 1. Physical Bounds Validation Rules (`src/data/validator.py`)

Every incoming telemetry reading undergoes physical range validation before being accepted into the storage layer or fed into LNN/GNN models:

| Field | Min Bound | Max Bound | Quality Flag on Failure |
|---|---|---|---|
| **Temperature (`temperature`)** | -10.0 °C | +60.0 °C | `OUT_OF_BOUNDS` |
| **Relative Humidity (`humidity`)** | 0.0 % | 100.0 % | `OUT_OF_BOUNDS` |
| **Wind Speed (`windSpeed`)** | 0.0 km/h | 150.0 km/h | `OUT_OF_BOUNDS` |
| **Mandatory Fields** | `temperature`, `humidity` | — | `MISSING_FIELD` |

Valid readings receive the `GOOD` quality flag.

---

## 2. Partitioned Storage Architecture (`src/data/storage_adapter.py`)

### Local Filesystem Partitioning
Telemetry readings are stored in date-partitioned JSON files:

```
data/raw/
└── YYYY-MM-DD/
    ├── station_0.json
    ├── station_1.json
    └── ...
```

### Amazon S3 Bucket Partitioning
For production cloud ingestion, the S3 adapter routes batch objects to the raw telemetry bucket:

$$\text{S3 Key}: \texttt{s3://weather-telemetry-raw/raw/YYYY-MM-DD/station\_<station\_id>.json}$$

---

## 3. Telemetry Ingestion Flow

$$\text{AW Station / CSV / API} \xrightarrow{\quad \text{Raw JSON / Row} \quad} \underbrace{\text{TelemetryValidator}}_{\text{Bounds \& Null Check}} \xrightarrow[\text{If GOOD}]{\quad \text{Validated} \quad} \underbrace{\text{Storage Adapters}}_{\text{Local Date Partition + S3 Raw}}$$

---

## Related
- [[references/kloudtech-api-specification]]
- [[references/open-meteo-3month-dataset]]
- [[concepts/system-architecture]]
