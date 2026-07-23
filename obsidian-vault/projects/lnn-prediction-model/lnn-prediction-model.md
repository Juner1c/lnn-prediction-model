---
title: LNN Prediction Model Project
category: project
tags: [weather, lnn, gnn, lfm, qlora, spatial-graph, outage-mitigation]
source_path: LNN/SYSTEM ARCHITECTURE.htm
created: 2026-07-20T10:40:00Z
updated: 2026-07-23T09:50:00Z
---

# LNN Prediction Model Project

This project implements a multi-station weather forecasting system predicting short-term and multi-horizon temperature, relative humidity, air pressure, wind speed, and heat-index values across 12 Automated Weather Stations in Bataan, Philippines. The system leverages spatial relationships among stations using a hybrid architecture consisting of Liquid Neural Networks (LNN) for continuous temporal denoising, Spatial-Temporal Graph Neural Networks (STGNN) for spatial message passing, and **LFM2.5-8B-A1B** as an autonomous data science meta-controller.

## Key Sub-components

- [[concepts/system-architecture]] — Detailed layout of the 8-layer technology stack (IoT, pre-processing, ML inference, orchestration, visualization).
- [[concepts/spatial-graph-outage-mitigation]] — Haversine distance spatial graph convolution ($A_{\text{norm}} \cdot H$) for dynamic missing node feature reconstruction during station dropouts.
- [[concepts/autonomous-lfm-meta-controller]] — 4-bit NF4 LFM2.5-8B meta-controller running QLoRA fine-tuning on winning experiment trajectories.
- [[concepts/scheduled-autotuning-service]] — Background daemon (`scripts/schedule_autotuning.py`) executing 6-hour retraining cycles and checkpoint updates (`data/stgnn_bataan_12nodes.pt`).
- [[references/project-timeline]] — Project lifecycle milestones across multi-year data integration and production deployment.

## Empirical Metrics (2025–2026 Multi-Year Dataset)

- **Dataset Scope**: 1.6+ Years (118,846 total records across 12 Bataan weather stations, 13,674 timesteps).
- **Temperature Validation RMSE**: **`3.2219 °C`** (Validation MAE: `2.3788 °C`).
- **Heat Index Validation RMSE**: **`4.9579 °C`**.
- **Station Outage Resilience**: Evaluated under 20% simulated station dropouts with $\le 0.05^\circ\text{C}$ performance variance.
