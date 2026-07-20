---
title: Denoising LNN Service Specification & Latency Benchmark
category: concept
tags: [lnn, denoiser, cfc, pytorch, ncps, benchmark, latency, sla]
sources: [src/models/lfm_denoiser.py, src/models/benchmark_lfm.py]
created: 2026-07-20T12:15:00Z
updated: 2026-07-20T12:15:00Z
---

# Denoising LNN Service Specification & Latency Benchmark

The **Denoising Liquid Neural Network (LNN) Service** processes raw 15-minute telemetry streams to filter high-frequency sensor noise, handle missing time slices, and extract smooth latent state vectors before feeding the spatial Graph Neural Network (GNN).

---

## 1. Network Architecture (`src/models/lfm_denoiser.py`)

* **Core Layer**: `ncps.torch.CfC` (Closed-form Continuous-time Network) with `LiquidTimeConstantCell` fallback.
* **Input Tensor Shape**: `[batch_size, seq_len=96, input_features=5]`
  * Features: `temperature`, `humidity`, `dewPoint`, `apparentTemperature`, `windSpeed`.
* **Output Tensor Shape**: `[batch_size, seq_len=96, output_size=5]` (Filtered continuous feature vectors).
* **State Evolution**: Closed-form analytical ODE approximation $x(t) = \sigma(-f(x_0, I, t)) \odot g(x_0, I, t) + (1 - \sigma(-f(x_0, I, t))) \odot h(x_0, I, t)$.

---

## 2. Latency Benchmark & SLA Compliance (`src/models/benchmark_lfm.py`)

| Benchmark Parameter | Value |
|---|---|
| **Batch Size** | 1 station |
| **Sequence Length** | 96 steps (24 hours at 15-min intervals) |
| **Iterations** | 1,000 runs |
| **Mean Latency** | **~12.5 ms** |
| **P99 Latency** | **~18.5 ms** |
| **Max Latency** | **~20.3 ms** |
| **SLA Target Threshold** | **< 50.0 ms** |
| **Compliance Verdict** | **PASSED (COMPLIANT)** |

---

## Related
- [[concepts/liquid-neural-networks]]
- [[concepts/lfm-vs-baseline-comparison]]
- [[concepts/system-architecture]]
