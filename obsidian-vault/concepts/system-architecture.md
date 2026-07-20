---
title: System Architecture
category: concept
tags: [architecture, tech-stack, lnn, gnn]
sources: [LNN/SYSTEM ARCHITECTURE.htm]
created: 2026-07-20T10:40:00Z
updated: 2026-07-20T10:40:00Z
---

# System Architecture

The weather forecasting system uses an 8-layer technology stack designed for low-latency, spatial-temporal data ingestion, processing, and prediction. It is designed to capture telemetry from remote Automated Weather (AW) stations, clean it using Liquid Neural Networks, calculate heat-indexes, forecast using Graph Neural Networks, and display results on an interactive dashboard.

---

## 8-Layer Component Breakdown & Technology Stack

| Layer | Component & Role | Recommended Tech | Rationale / Why |
|---|---|---|---|
| **1** | **Sensors & Connectivity**<br>Collects temperature, humidity, wind, pressure, solar radiation, GPS, etc. | LoRaWAN / ESP32 | Low power, long‑range, suitable for remote AW stations. |
| **2** | **API Gateway**<br>Exposes a secure REST/GraphQL endpoint, handles auth, rate‑limiting, and request routing. | Kloudtech AWS API | Central entry point, easy versioning. |
| **3** | **Denoising LNN Service**<br>Applies learned filters, outlier removal, and feature engineering before feeding the GNN. | PyTorch + Liquid Foundation Model (LFM) | LFM provides state‑of‑the‑art efficiency; encoder‑decoder blocks can be adapted for preprocessing. |
| **4** | **Heat‑Index Calculation**<br>Computes apparent temperature. | Pure Python (NumPy) or JAX | Simple deterministic function using Lu & Romps equations (or NWS formula); no ML needed. |
| **5** | **AI Forecasting Engine (GNN)**<br>Multi‑modal graph neural network that ingests cleaned time‑series + spatial relationships. | PyTorch Geometric + LFM2 backbone | GNN captures spatial dependencies (between stations); LFM backbone gives strong inductive bias. |
| **6** | **Persistence & Orchestration**<br>Stores raw telemetry, manages batch jobs, schedules retraining. | Amazon S3 (raw), Amazon Aurora (time‑series), Apache Airflow (ETL) | Reliable, scalable storage & workflow. |
| **7** | **CI/CD & IaC**<br>Automates builds, tests, and deployments. | GitHub Actions / GitLab CI, Terraform, Helm charts | Enables reproducible, repeatable deployments. |
| **8** | **Dashboard**<br>Visualizes current conditions, forecasts, uncertainty intervals, and alerts. | React + D3.js / Plotly, Grafana | Real‑time UI for operators. |

---

## Operational Considerations

### Network Latency
Edge‑to‑gateway messages are cached locally (e.g., Redis) and processed in batches every 5 minutes to mitigate communication overhead.

### Data Drift
Daily statistical profiling (measuring skewness, autocorrelation) triggers automatic model‑retraining if drift thresholds are breached.

### Security
Strict device certificates, VPC private endpoints, encrypted S3 buckets, and IAM least‑privilege policies are applied at all layers.

### Scalability
The Denoising LNN service is horizontally scaled using AWS Fargate. The GNN forecasting engine is served behind an Auto‑Scaling Group using an Application Load Balancer.

### Observability
CloudWatch metrics are configured for each microservice, feeding into Grafana dashboards displaying latency, error rates, and forecast confidence intervals.

---

## Related
- [[concepts/telemetry-logging]]
- [[concepts/dashboard-features]]
- [[references/project-timeline]]
