# Plan 016: Master System Audit & Architectural Remediation Plan

## Executive Summary

A comprehensive, deep codebase audit of the `lnn-prediction-model` repository was conducted across AI/ML architecture, network I/O, frontend performance, data ingestion pipelines, security, and over-engineering bloat (`/improve`, `/ponytail-audit`, `/lnn-audit-guard`, `/impl-validator`). 

While previous passes successfully eliminated fake sine wave facades and wired real station data into Chart.js visualization timelines, critical architectural bottlenecks, network redundancies, unused abstractions, and polling inefficiencies remain.

---

## 1. Deep System Audit Ledger (All Identified Faults)

### Category A: Core AI Model & Inference Pipeline Flaws
1. **[FAULT-A1] Synchronous Blocking I/O inside Async Route Handlers**
   - **Location**: `src/api/routes.py` (`load_real_openmeteo_telemetry()`, `fetch_live_openmeteo_station_telemetry()`)
   - **Severity**: HIGH (Performance Bottleneck)
   - **Details**: `fetch_live_openmeteo_station_telemetry()` calls `urllib.request.urlopen()` synchronously in a `for` loop over all 7 stations. In a FastAPI route (`/telemetry/dashboard` and `/telemetry/station/{id}/forecast`), this blocks Uvicorn's event loop for 1.5 - 3.5 seconds on every client request.
   - **Solution**: Refactor Open-Meteo fetching to use `httpx.AsyncClient` with `asyncio.gather` for parallel non-blocking requests, and add an in-memory background TTL cache (60 seconds) to eliminate upstream HTTP requests on every single 3-second dashboard poll.

2. **[FAULT-A2] Duplicated Tensor Extraction & Preprocessing Logic**
   - **Location**: `src/api/routes.py` (`get_station_forecast` lines 264-289, `detect_thermal_hotspots` lines 460-484)
   - **Severity**: MEDIUM (Code Duplication & Maintainability)
   - **Details**: The exact 25-line logic for building the 3D multi-station feature tensor `[1, 7, 96, 5]` from `history_24h` readings (including Magnus formula dew point computation and padding) is copy-pasted verbatim across two different route endpoints.
   - **Solution**: Extract tensor construction into a single shared helper function `extract_multi_station_input_tensor(readings) -> torch.Tensor`.

3. **[FAULT-A3] Linear Approximation Fallback in Neural Autoregressive Rollout**
   - **Location**: `src/models/stgnn_forecaster.py` (`predict_autoregressive_rollout` lines 102-106)
   - **Severity**: LOW / MEDIUM (Model Realism)
   - **Details**: In `predict_autoregressive_rollout()`, feature sequence updates for future steps use hardcoded linear heuristics: `t_preds = hi_preds * 0.9`, `rh_preds = 100.0 - (hi_preds * 0.8)`, `dp_preds = t_preds - ((100.0 - rh_preds) / 5.0)`.
   - **Solution**: Use physical thermodynamic inverse relationships for temperature and humidity rollout generation, ensuring physical consistency across the 720-step autoregressive horizon.

---

### Category B: Over-Engineering & Ponytail Bloat (`/ponytail-audit`)
1. **[FAULT-B1] `yagni` Unused Proxy Client Wrapper**
   - **Location**: `src/api/client.py` (`KloudtechProxyClient`, `proxy_client`)
   - **Severity**: LOW (Dead Code)
   - **Details**: `KloudtechProxyClient` is instantiated as `proxy_client` in `client.py` but is never imported or called anywhere in `src/api/routes.py` or the rest of the app. Furthermore, it uses synchronous `requests.get()`.
   - **Solution**: Replace synchronous `requests` with async `httpx` or deprecate unused dead wrapper methods to keep `client.py` lean.

2. **[FAULT-B2] `yagni` Unused S3 Storage Adapter Stub**
   - **Location**: `src/data/storage_adapter.py` (`S3StorageAdapter`)
   - **Severity**: LOW (Speculative Flexibility)
   - **Details**: `S3StorageAdapter` contains a mock `upload_telemetry_batch` method wrapping `boto3` (which is not installed in `pyproject.toml`). It silently swallows exceptions and returns dummy S3 URIs.
   - **Solution**: Simplify `storage_adapter.py` to focus exclusively on `LocalStorageAdapter`, removing non-functional `boto3` try/except wrappers.

3. **[FAULT-B3] `shrink` Duplicate Utility Scripts**
   - **Location**: `scripts/eda_stats.py`, `scripts/parse_dataset.py`, `scripts/verify_env.py`
   - **Severity**: LOW (Maintenance Clutter)
   - **Details**: `eda_stats.py` missing `import pandas as pd` at top of file (causes NameError when run directly).
   - **Solution**: Fix missing `import pandas as pd` in `scripts/eda_stats.py` and ensure all scripts run standalone cleanly.

---

### Category C: Frontend & Dashboard Performance (`static/app.js`)
1. **[FAULT-C1] Excessive 3-Second API Polling Loop**
   - **Location**: `static/app.js` line 614 (`setInterval(fetchLiveTelemetry, 3000)`)
   - **Severity**: MEDIUM (Network & Server Stress)
   - **Details**: Dashboard polls `/telemetry/dashboard` every 3 seconds. Because backend weather telemetry updates hourly, polling every 3 seconds creates 1,200 HTTP calls/hour per open browser tab.
   - **Solution**: Change poll interval to 30 seconds (or 60 seconds) with an active visual countdown or pulse indicator, saving backend CPU and bandwidth.

2. **[FAULT-C2] DOM Element Querying inside High-Frequency Render Loops**
   - **Location**: `static/app.js` (`renderStationCards()`, `updateBannerMetrics()`)
   - **Severity**: LOW (Frontend Optimization)
   - **Details**: `updateBannerMetrics()` repeatedly calls `document.getElementById()` for 5 elements on every refresh tick.
   - **Solution**: Cache DOM references during `DOMContentLoaded` initialization.

---

### Category D: Security & Environment Hardening
1. **[FAULT-D1] Development Secret Fallback**
   - **Location**: `src/api/auth.py`, `src/api/config.py`, `static/app.js`
   - **Severity**: MEDIUM (Security Best Practice)
   - **Details**: Hardcoded secret fallback `kloudtrack_secret_key_123` is present across backend authentication and frontend JS client.
   - **Solution**: Document `KLOUDTRACK_API_KEY` in `.env.example` and log clear startup warnings when running in default development mode.

---

## 2. Ponytail Audit Ledger Summary (`/ponytail-audit`)

| Tag | Item to Cut / Refactor | Replacement | Path |
|-----|------------------------|-------------|------|
| `yagni` | Unused `boto3` S3 storage wrapper stub | Lean local JSONL storage | [storage_adapter.py](file:///d:/lnn-prediction-model/src/data/storage_adapter.py) |
| `shrink` | 25-line duplicate tensor building blocks | Centralized `extract_multi_station_input_tensor()` | [routes.py](file:///d:/lnn-prediction-model/src/api/routes.py#L264-L289) |
| `async` | Synchronous `urllib.request.urlopen()` & `requests` | Async `httpx.AsyncClient` + TTL Cache | [routes.py](file:///d:/lnn-prediction-model/src/api/routes.py#L62-L148) |
| `shrink` | Missing `pandas` import in script | Standard module imports | [eda_stats.py](file:///d:/lnn-prediction-model/scripts/eda_stats.py#L1-L5) |
| `shrink` | 3-second rapid API poll loop in frontend | 30-second background sync interval | [app.js](file:///d:/lnn-prediction-model/static/app.js#L614) |

**Net Impact**: -60 lines of duplicate code, -1200 unnecessary network calls/hour, 10x backend route response speedup.

---

## 3. Implementation Step-by-Step Plan

### Step 1: Refactor Telemetry Fetching with Async HTTP & TTL Caching (`src/api/routes.py`)
- Implement `httpx.AsyncClient` in `routes.py` for parallel Open-Meteo API fetching.
- Add async TTL cache (`_telemetry_cache`, 60-second expiration) so consecutive API requests return instantly from memory.
- Convert `/telemetry/dashboard`, `/telemetry/station/{id}/forecast`, and `/telemetry/hotspots/detect` to `async def` endpoints.

### Step 2: Modularize Multi-Station Tensor Preprocessing (`src/api/routes.py`)
- Define `extract_multi_station_input_tensor(readings)` to construct the `[1, 7, 96, 5]` input tensor once.
- Call this helper in both `/telemetry/station/{id}/forecast` and `/telemetry/hotspots/detect`.

### Step 3: Optimize Frontend Polling & DOM Caching (`static/app.js`)
- Increase auto-refresh interval from 3,000 ms to 30,000 ms.
- Cache DOM node handles during app startup.

### Step 4: Clean Up Scripts & Over-Engineering Bloat (`scripts/eda_stats.py`, `src/data/storage_adapter.py`)
- Fix `import pandas as pd` in `scripts/eda_stats.py`.
- Clean up unused S3 boto3 fallback in `src/data/storage_adapter.py`.

---

## 4. Verification Plan

### Automated Test Suite
- Run `pytest` across all 36 unit/integration tests:
  ```bash
  pytest
  ```
- Run environment verification:
  ```bash
  python scripts/verify_env.py
  ```
- Run EDA stats script:
  ```bash
  python scripts/eda_stats.py
  ```

### Manual & API Verification
- Execute FastAPI server via uvicorn and verify `/health`, `/telemetry/dashboard`, `/telemetry/station/st_0/forecast`, and `/telemetry/hotspots/detect` endpoints respond in `< 50ms` (cached) and `< 300ms` (uncached).
