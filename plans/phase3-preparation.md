# Implementation Plan: Phase 3 Preparation (Data Ingestion Prototype)

Phase 3 builds the data ingestion prototype to validate the raw telemetry flow from Automated Weather (AW) stations / Kloudtech APIs into local and cloud storage adapters (S3 / Parquet) with automated data quality validation.

---

## Objectives of Phase 3

1. **Sensor Ingestion Client (`src/data/ingestion_client.py`)**: Client that polls live/simulated telemetry from Kloudtech endpoints or processes batch CSV slices from `data/timeseries_15min_clean.csv`.
2. **Telemetry Validation Engine (`src/data/validator.py`)**: Data quality validator enforcing physical thresholds (e.g. Temperature -10°C to +60°C, Humidity 0-100%, Wind Speed 0-150 km/h) and assigning quality flags (`GOOD`, `OUT_OF_BOUNDS`, `MISSING_FIELD`).
3. **Storage Adapter (`src/data/storage_adapter.py`)**: Storage interface supporting local JSON/Parquet storage and simulated/real Amazon S3 bucket uploads.
4. **Automated Ingestion Tests (`tests/test_ingestion.py`)**: `unittest` suite validating raw telemetry ingestion, schema validation, quality flagging, and storage persistence.

---

## Component Details

### 1. `src/data/validator.py`
- Enforces range checks and flags anomalies.
- Returns `TelemetryValidationResult` with `is_valid: bool`, `quality_flag: str`, and `cleaned_data: dict`.

### 2. `src/data/ingestion_client.py`
- `KloudtechIngestionClient`: Fetches readings from local dataset or Kloudtech API endpoints.

### 3. `src/data/storage_adapter.py`
- `LocalStorageAdapter`: Saves raw telemetry JSON/Parquet partitions by date (`data/raw/YYYY-MM-DD/`).
- `S3StorageAdapter`: S3 boto3/mock client for S3 raw bucket uploads (`s3://weather-telemetry-raw/`).

### 4. `tests/test_ingestion.py`
- Verifies ingestion flow, validation pass/fail cases, and storage partition creation.

---

## Verification Plan

### Automated Verification
- Run `python -m unittest discover tests` to ensure all ingestion and validation tests pass (100% OK).

### Vault Knowledge Base Update
- Create `obsidian-vault/references/data-ingestion-architecture.md`.
- Update `obsidian-vault/index.md`, `log.md`, and `hot.md`.
