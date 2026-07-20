---
title: Spatial-Temporal GNN Forecasting Engine Architecture
category: concept
tags: [gnn, stgnn, spatial-graph, haversine, adjacency-matrix, forecast, lnn, heat-index]
sources: [src/models/spatial_graph.py, src/models/stgnn_forecaster.py, tests/test_stgnn_forecaster.py]
created: 2026-07-20T12:25:00Z
updated: 2026-07-20T12:25:00Z
---

# Spatial-Temporal GNN Forecasting Engine Architecture

This concept note documents the architecture, spatial adjacency construction, and multi-step forecast generation of the **Spatial-Temporal Graph Neural Network (STGNN) Core** implemented in Phase 6.

---

## 1. Spatial Graph Construction (`src/models/spatial_graph.py`)

* **Spatial Nodes ($N=7$)**: The 7 Central Luzon Automated Weather (AW) stations (`st_0` through `st_6`).
* **Haversine Distance**: Computes great-circle pairwise geographical distance $d_{ij}$ (km) between station coordinates.
* **Gaussian Thresholded Adjacency Matrix**:

$$A_{ij} = \begin{cases} 1.0 & \text{if } i = j \text{ (self-loop)} \\ \exp\left(-\frac{d_{ij}^2}{\sigma^2}\right) & \text{if } d_{ij} \le d_{\text{max}} \\ 0 & \text{otherwise} \end{cases}$$

* **Symmetric Degree Normalization**: $\tilde{A} = D^{-1/2} A D^{-1/2}$, where $D_{ii} = \sum_j A_{ij}$.

---

## 2. Model Architecture (`src/models/stgnn_forecaster.py`)

$$\text{Input: } [B, N=7, L=96, C=5] \xrightarrow{\quad \text{LNN Denoising} \quad} \text{Cleaned } [B \cdot N, L, C] \xrightarrow{\quad \text{Spatial GCN} \quad} H^{(l+1)} = \text{ReLU}(\tilde{A} H^{(l)} W) \xrightarrow{\quad \text{Forecast Head} \quad} \text{Output: } [B, N=7, 16]$$

1. **Continuous-Time LNN Denoising**: Filters raw multi-station input streams in parallel.
2. **Spatial Graph Convolutions**: Propagates spatial thermal signals across neighboring weather stations using normalized adjacency $\tilde{A}$.
3. **Multi-Step Forecast Head**: Generates 16-step ahead Heat Index predictions for all 7 weather stations simultaneously.

---

## Related
- [[concepts/spatial-temporal-gnn]]
- [[concepts/lfm-denoiser-service]]
- [[concepts/heat-index-calculator-module]]
- [[concepts/system-architecture]]
