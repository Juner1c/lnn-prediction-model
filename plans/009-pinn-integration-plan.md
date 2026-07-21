# Phase 9: Physics-Informed Neural Network (PINN) Integration Plan

## Overview
This plan specifies the architecture and mathematical formulation for integrating Physics-Informed Neural Networks (PINN) into `lnn-prediction-model`. The goal is to enforce thermodynamic conservation laws, psychrometric constraints, and spatial advection-diffusion differential equations across the Liquid Neural Network (LNN) denoiser and Spatial-Temporal Graph Neural Network (STGNN) forecaster.

---

## 1. Mathematical Formulation & Physics Constraints

### 1.1 Loss Function Decomposition
The PINN training objective augments the data-driven forecasting loss with physics-informed penalty terms:

$$\mathcal{L}_{\text{PINN}} = \mathcal{L}_{\text{MSE}}(\hat{y}, y) + \lambda_{\text{thermo}} \mathcal{L}_{\text{thermo}} + \lambda_{\text{dew}} \mathcal{L}_{\text{dew}} + \lambda_{\text{advection}} \mathcal{L}_{\text{advection}}$$

Where:
1. **Thermodynamic Heat Index Consistency Loss ($\mathcal{L}_{\text{thermo}}$)**:
   Ensures predicted Heat Index $\widehat{HI}$ matches Rothfusz/Lu & Romps physics from predicted $\hat{T}$ and $\widehat{RH}$:
   $$\mathcal{L}_{\text{thermo}} = \frac{1}{N} \sum_{i} \left| \widehat{HI}_i - \text{Rothfusz}(\hat{T}_i, \widehat{RH}_i) \right|^2$$

2. **Dew Point & Physical Bound Inequality Loss ($\mathcal{L}_{\text{dew}}$)**:
   Enforces physical bounds ($T \ge T_d$, $0 \le RH \le 100$):
   $$\mathcal{L}_{\text{dew}} = \frac{1}{N} \sum_{i} \left( \text{ReLU}(T_{d,i} - T_i)^2 + \text{ReLU}(-RH_i)^2 + \text{ReLU}(RH_i - 100)^2 \right)$$

3. **Spatial Advection-Diffusion Differential Equation Residual ($\mathcal{L}_{\text{advection}}$)**:
   Models spatial heat transport across graph edge distances $d_{ij}$ and wind vectors $\mathbf{u}_i$:
   $$\frac{\partial T_i}{\partial t} + \mathbf{u}_i \cdot \nabla_{G} T_i - \kappa \nabla_{G}^2 T_i = 0$$
   where graph spatial gradients use normalized graph Laplacian $L_{\text{norm}} = I - D^{-1/2} A D^{-1/2}$.

---

## 2. Proposed Component Modifications

### 2.1 [NEW] Physics Loss Module (`src/models/pinn_loss.py`)
- Standard PyTorch `nn.Module` computing $\mathcal{L}_{\text{thermo}}$, $\mathcal{L}_{\text{dew}}$, and spatial Laplacian advection residuals.
- Vectorized differentiable Rothfusz & Tetens vapor pressure formulation.

### 2.2 [MODIFY] STGNN Forecaster (`src/models/stgnn_forecaster.py`)
- Add physics-informed loss computation interface during forward/training pass.
- Optional multi-head forecast output emitting $[\hat{T}, \widehat{RH}, \widehat{HI}]$ for joint thermodynamic enforcement.

### 2.3 [NEW] PINN Physics Validator & Unit Tests (`tests/test_pinn_loss.py`)
- Verify zero loss when telemetry perfectly satisfies physical laws.
- Verify gradient flow through physics penalty terms.

---

## 3. Verification Plan

### Automated Tests
```bash
pytest tests/test_pinn_loss.py -v
pytest tests/ -v
```

### SLA & Latency Compliance
```bash
python -m src.models.benchmark_lfm
```
Ensure inference P99 latency remains $< 50$ ms.
