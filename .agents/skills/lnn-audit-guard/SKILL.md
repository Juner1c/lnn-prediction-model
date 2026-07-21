---
name: lnn-audit-guard
description: Anti-pattern guard and architectural flaw prevention for the LNN Heat Index prediction project. Trigger whenever modifying, testing, or auditing STGNN models, LNN denoisers, telemetry ingestion, FastAPI routes, dataset paths, or CI pipelines in lnn-prediction-model.
---

# LNN Prediction Model - Audit Guard & Anti-Pattern Prevention

This skill documents critical bugs, architectural flaws, data leaks, and pipeline disconnects discovered during the deep codebase audit. Follow these rules to avoid repeating known mistakes.

## 1. Absolute Path Contamination
- **FLAW**: Hardcoded developer paths (`c:\Users\Jhonric Gorillo\Desktop\...`) were present across `storage_adapter.py`, `parse_dataset.py`, `eda_stats.py`, `test_deployment.py`, `test_ingestion.py`, and `test_stgnn_forecaster.py`.
- **GUARD RULE**: Always use project-relative paths using `os.path.dirname(__file__)` or `pathlib.Path(__file__).resolve().parents[...]`. Never commit machine-specific absolute paths.

## 2. Model Disconnect & Dummy Data Facade
- **FLAW**: `routes.py` instantiated `SpatialTemporalGNN` and passed `dummy_input = torch.randn(1, 7, 96, 5)` instead of actual station telemetry. The output was then discarded in favor of synthetic trigonometric sine curves.
- **GUARD RULE**: Connect real ingestion tensor arrays `[batch, nodes, seq_len, features]` directly into the model forward pass. Never replace model predictions with hardcoded `np.sin(...)` loops presented as model output.

## 3. Synchronous Network I/O in Async API
- **FLAW**: `load_real_openmeteo_telemetry()` called `urllib.request.urlopen()` synchronously inside route requests, blocking Uvicorn's event loop.
- **GUARD RULE**: Use `httpx.AsyncClient` or a background celery/apscheduler worker for external API polling. Keep route handlers asynchronous and non-blocking.

## 4. Unvectorized Station Time Loops
- **FLAW**: `lfm_denoiser.py` and `stgnn_forecaster.py` iterated step-by-step through `seq_len` (96 steps) using Python `for` loops instead of batched tensor operations.
- **GUARD RULE**: Vectorize temporal passes over tensors `[batch, nodes, seq_len, features]` using native PyTorch batch dimension operations.

## 5. Test Suite & Import Incompatibilities
- **FLAW**: Running `pytest` failed due to missing `PYTHONPATH=.` resolution and a `Starlette/FastAPI` version mismatch (`Router.__init__() got unexpected keyword argument 'on_startup'`).
- **GUARD RULE**: Ensure `pyproject.toml` defines `pythonpath = ["."]`. Keep `fastapi` and `starlette` dependencies pinned to compatible releases.

## 6. Untrained Model & Missing Checkpoint Guard
- **FLAW**: No training pipeline (`train.py`, loss functions, optimizers) or pre-trained weight files (`.pth`/`.pt`) exist in the repository. The model runs with default PyTorch random weight initialization.
- **GUARD RULE**: Always provide a explicit training script and checkpoint loader (`model.load_state_dict(torch.load(...))`) before deploying model inference in production routes.

