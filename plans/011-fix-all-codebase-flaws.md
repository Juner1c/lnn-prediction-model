# Implementation Plan 011: Resolve All Codebase Flaws & Build Operational ML Pipeline

> **Plan ID**: `011-fix-all-codebase-flaws`  
> **Status**: Complete  
> **Author**: Senior AI Systems Advisor (`/improve`, `/ponytail`, `/impl-validator`)  
> **Dependencies**: `010-comprehensive-codebase-audit`  


---

## 1. Executive Summary

This plan outlines the systematic resolution of all 11 critical, high, medium, and soft flaws identified in the codebase audit. The objective is to transform `lnn-prediction-model` into a fully functional, production-ready, portable, and mathematically sound microservice with a real PyTorch training pipeline, real model inference, non-blocking async API routes, and 100% passing automated test coverage.

---

## 2. Phased Execution Order

### Phase 1: Critical Infrastructure & Portability Fixes
* **Step 1.1**: Fix absolute Windows paths across all source files and tests (`storage_adapter.py`, `parse_dataset.py`, `eda_stats.py`, `test_deployment.py`, `test_ingestion.py`, `test_stgnn_forecaster.py`).
* **Step 1.2**: Fix `pyproject.toml` configuration (`pythonpath = ["."]`) and resolve Starlette/FastAPI route initialization errors so `python -m pytest` executes cleanly.

### Phase 2: Model Training Pipeline & Real Inference Integration
* **Step 2.1**: Implement `scripts/train_stgnn.py` to train `SpatialTemporalGNN` and `LiquidDenoisingService` on `data/timeseries_15min_clean.csv` using PyTorch sliding-window dataset loaders, MSE loss, and Adam optimizer. Save weights to `data/stgnn_weights.pt`.
* **Step 2.2**: Update `src/api/routes.py` to load pre-trained weights from `data/stgnn_weights.pt` and feed real ingested telemetry into the model forward pass, eliminating the random noise and hardcoded sine wave facade.

### Phase 3: Performance, Security & Storage Optimization
* **Step 3.1**: Secure credentials by removing hardcoded API key fallbacks in `auth.py`, `config.py`, `app.js`, and `docker-compose.yml`.
* **Step 3.2**: Refactor `load_real_openmeteo_telemetry()` in `routes.py` to use non-blocking async HTTP calls with `httpx` or threadpool execution.
* **Step 3.3**: Vectorize PyTorch cell iterations in `lfm_denoiser.py` and `stgnn_forecaster.py`.
* **Step 3.4**: Optimize `storage_adapter.py` to eliminate $O(N^2)$ file re-serialization on every telemetry write.

### Phase 4: Frontend Polish & Ponytail Code Simplification
* **Step 4.1**: Remove synthetic `Math.random()` jitter injection in `app.js`.
* **Step 4.2**: Run `ponytail-review` to delete dead code and redundant abstractions across `src/`.

---

## 3. Verification & Validation Plan

Each phase will be verified using `impl-validator` and `pytest`:
1. `python -m pytest` — Ensure 100% test pass rate across all test modules.
2. `python scripts/train_stgnn.py --epochs 5` — Verify model training loss converges and weights are saved.
3. `python scripts/deploy.py` — Verify FastAPI microservice starts and `/health`, `/telemetry/dashboard`, and `/telemetry/station/st_0/forecast` return real trained forecasts.
