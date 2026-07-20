---
title: Wiki Index
---

# Wiki Index

*This index is automatically maintained. Last updated: 2026-07-20T10:40:00Z*

## Concepts
- [[concepts/system-architecture|System Architecture (LNN)]] — The 8-layer tech stack and operational considerations for the LNN forecast model ( #architecture #tech-stack #weather)
- [[concepts/telemetry-logging|Telemetry Logging (LNN)]] — Structured telemetry logs schema and error tracking for forecast model validation ( #telemetry #logging #observability)
- [[concepts/dashboard-features|Dashboard Features (LNN)]] — Interactive components, analytical tools, and GIS overlays for the forecast dashboard ( #dashboard #visualization #ui)
- [[concepts/liquid-neural-networks|Liquid Neural Networks (LTC, CfC, & LFM)]] — Continuous-time neural network architectures and ODE dynamics for time-series denoising ( #lnn #ltc #cfc #ode)
- [[concepts/spatial-temporal-gnn|Spatial-Temporal Graph Neural Networks (STGNN)]] — Spatial graph convolutions and adjacency matrix construction for AW station networks ( #gnn #stgcn #graphsage #gat)
- [[concepts/lfm-vs-baseline-comparison|LFM / LNN vs. Baseline Encoders Comparison]] — Contested trade-off analysis comparing CfC/LNN vs LSTM, Transformers, and GNNs ( #comparison #trade-offs #benchmarks)
- [[concepts/lfm-denoiser-service|Denoising LNN Service Specification & Latency Benchmark]] — CfC continuous-time preprocessor specification and < 50 ms SLA latency benchmark results ( #lnn #denoiser #cfc #pytroch #ncps #benchmark)
- [[concepts/heat-index-calculator-module|Deterministic Heat-Index & Thermal Comfort Calculator Module]] — Mathematical equations for NWS Rothfusz, Lu & Romps apparent temp, Stull wet-bulb, and vectorized batching ( #heat-index #rothfusz #lu-romps #stull #wet-bulb #deterministic)
- [[concepts/stgnn-forecast-engine|Spatial-Temporal GNN Forecasting Engine Architecture]] — Haversine spatial distance adjacency matrix construction and joint Spatial GCN + LNN multi-step forecasting ( #gnn #stgnn #spatial-graph #haversine #adjacency-matrix #forecast)
- [[concepts/dashboard-visualization|Real-Time Heat-Index Dashboard & UI/UX Architecture]] — Aesthetic identity, Leaflet map, Chart.js 16-step LNN/STGNN forecast curves, and FastAPI static serving ( #dashboard #frontend-design #ui-ux #leaflet #chartjs #telemetry #fastapi)

## Entities
- [[entities/antidoom|Antidoom (FTPO Preference & Anti-Loop Framework)]] — Final Token Preference Optimization and anti-repetition loop guard integration ( #antidoom #ftpo #anti-loop #liquidai)

## Skills

## References
- [[references/project-timeline|Project Timeline (LNN)]] — The milestones and deliverables across the 8-phase development lifecycle ( #timeline #milestones #planning)
- [[references/heat-index-dataset-variables|Heat Index Dataset Variables]] — Essential and secondary weather variables for accurate Heat Index & thermal comfort calculations ( #heat-index #datasets #variables #open-meteo)
- [[references/open-meteo-3month-dataset|Open-Meteo 3-Month Heat Index Dataset Analysis]] — Statistical breakdown, spatial metadata, and risk distribution of the 60,340-row 15-minute telemetry dataset ( #eda #dataset #open-meteo #heat-index)
- [[references/kloudtech-api-specification|Kloudtech Telemetry & Heat Index API Specification]] — REST endpoint definitions, x-kloudtrack-key authorization, response shapes, and FastAPI route implementations ( #api #openapi #kloudtech #telemetry #auth)
- [[references/data-ingestion-architecture|Data Ingestion & Quality Validation Architecture]] — Physical bounds validation rules, quality flags, and local/S3 partitioned storage adapters ( #ingestion #telemetry #validation #storage #s3)
- [[references/deployment-pipeline-automation|Deployment & CI/CD Pipeline Automation Specification]] — Multi-stage Docker build, docker-compose orchestration, GitHub Actions CI/CD workflows, and deployment verification ( #deployment #docker #docker-compose #github-actions #ci-cd)

## Projects
- [[projects/lnn-prediction-model/lnn-prediction-model|LNN Prediction Model Project]] — Project overview of the multi-modal forecast system using GNN and Liquid Neural Networks ( #weather #lnn #gnn)

## Synthesis

## Journal
