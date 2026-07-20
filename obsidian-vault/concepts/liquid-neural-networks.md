---
title: Liquid Neural Networks (LTC, CfC, & LFM)
category: concept
tags: [lnn, ltc, cfc, ode, continuous-time, machine-learning]
sources: [arXiv:2006.04439, arXiv:2106.13898, Nature Machine Intelligence 2022]
created: 2026-07-20T11:38:00Z
updated: 2026-07-20T11:38:00Z
---

# Liquid Neural Networks (LTC, CfC, & LFM)

**Liquid Neural Networks (LNNs)** represent a class of continuous-time recurrent neural architectures inspired by biological nervous systems (specifically *C. elegans*). Developed by Hasani et al. and Lechner et al. (MIT CSAIL / Liquid AI), LNNs adapt their internal dynamics dynamically during inference based on incoming input streams.

---

## 1. Core Architectures: LTC vs. CfC

### Liquid Time-Constant (LTC) Networks (arXiv:2006.04439)
LTCs model hidden state transitions using ordinary differential equations (ODEs) where both the hidden state $x(t)$ and the time-constant $\tau_i(x, t, I)$ adapt dynamically to input signals $I(t)$:

$$\frac{dx_i(t)}{dt} = -\left[ \frac{1}{\tau_i} + f_i(x(t), I(t)) \right] x_i(t) + f_i(x(t), I(t)) A_i$$

* **Strengths**: Expressive continuous-time modeling, highly robust to irregular temporal intervals and noise.
* **Limitations**: Requires numerical ODE solvers (e.g., Runge-Kutta 4th order or Dormand-Prince), making training computationally expensive ($O(K)$ solver steps per sample).

### Closed-form Continuous-time (CfC) Networks (arXiv:2106.13898)
CfCs replace numerical ODE integration with a closed-form analytical approximation of the LTC differential equation:

$$x(t) \approx \sigma(-f(x_0, I, t)) \odot g(x_0, I, t) + (1 - \sigma(-f(x_0, I, t))) \odot h(x_0, I, t)$$

* **Strengths**: Eliminates numerical DE solvers entirely, accelerating inference and training speed by 1 to 5 orders of magnitude while preserving continuous-time dynamics.
* **Key Advantage**: Exact state evaluation at arbitrary time steps $t$, making it immune to missing observations or uneven sampling intervals (e.g., sensor telemetry dropouts).

---

## 2. Relevance to Weather Telemetry Pre-processing

In weather forecasting pipelines, sensor data from Automated Weather (AW) stations suffers from three major artifacts:
1. **Irregular Sampling**: Communication delays causing fluctuating transmission intervals (e.g., 5 min vs 17 min).
2. **Noise & Spikes**: Transducer drift, radio frequency interference, or rain droplets hitting sensors.
3. **Sensor Dropouts**: Intermittent connectivity loss resulting in missing time slices.

LNNs (specifically CfC layers) serve as an adaptive **Denoising & Feature Extraction Service** preceding spatial Graph Neural Networks (GNNs), filtering high-frequency noise and projecting non-stationary weather series into a continuous latent state.

---

## Related
- [[concepts/spatial-temporal-gnn]]
- [[concepts/lfm-vs-baseline-comparison]]
- [[concepts/system-architecture]]
