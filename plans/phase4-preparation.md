# Implementation Plan: Phase 4 (Denoising LNN Service)

Phase 4 implements the **Denoising Liquid Neural Network (LNN) Service** using Closed-form Continuous-time (CfC) networks (`ncps.torch.CfC`) to preprocess, filter high-frequency sensor noise, and handle missing telemetry time slices before spatial GNN forecasting.

---

## Objectives of Phase 4

1. **LNN Denoising Module (`src/models/lfm_denoiser.py`)**: PyTorch + `ncps` CfC neural model that ingests 5 feature channels (`temperature`, `humidity`, `dewPoint`, `apparentTemperature`, `windSpeed`) and outputs continuous-time filtered latent state representations.
2. **Latency Benchmarking (`src/models/benchmark_lfm.py`)**: Benchmark script measuring per-station inference latency to guarantee performance remains under our **50 ms SLA target** (achieving < 5 ms in closed-form).
3. **Automated Unit Tests (`tests/test_lfm_denoiser.py`)**: `unittest` suite testing LNN forward passes, output shape validation, batch processing, and latency thresholds.
4. **Knowledge Vault Preservation**: Document LNN denoiser deployment in `obsidian-vault/concepts/lfm-denoiser-service.md` and update vault index & logs.

---

## Component Details

### `src/models/lfm_denoiser.py`
- Inherits from `torch.nn.Module`.
- Uses `ncps.torch.CfC` or PyTorch continuous-time linear recurrent blocks.
- Accepts tensor shape `[batch_size, seq_len, input_features]` and returns `[batch_size, seq_len, output_dim]`.

### `src/models/benchmark_lfm.py`
- Runs 1,000 forward passes on 15-minute time-series sequences.
- Measures mean latency, std, and 99th percentile latency in milliseconds.

### `tests/test_lfm_denoiser.py`
- Verifies forward pass execution, tensor dimensions, and latency bounds.

---

## Verification Plan

### Automated Verification
- Run `python -m unittest discover tests` (100% test pass rate).
- Run `python src/models/benchmark_lfm.py` to verify latency < 50 ms per station.

### Knowledge Vault Update
- Create `obsidian-vault/concepts/lfm-denoiser-service.md`.
- Update `obsidian-vault/index.md`, `log.md`, and `hot.md`.
