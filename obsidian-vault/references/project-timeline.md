---
title: Project Timeline & Milestones
category: reference
tags: [timeline, milestones, planning, phases]
sources: [LNN/SYSTEM ARCHITECTURE.htm]
created: 2026-07-20T10:40:00Z
updated: 2026-07-20T10:40:00Z
---

# Project Timeline & Milestones

The project development lifecycle spans 8 distinct phases, moving from initial research to prototyping, individual service implementation, integration, and final review.

---

## Development Phases

### Phase 1: Research & Tool Selection
- **Milestone**: Technical stack finalization.
- **Deliverables**: 
  - Review LFM2 (Liquid Foundation Model 2) papers.
  - Compare LFM2 with other encoders (e.g., GraphSAGE, GAT).
  - Finalize core tech stack (PyTorch, LFM, FastAPI, Docker).

### Phase 2: API Design & Authentication
- **Milestone**: API spec and gateway authorization.
- **Deliverables**:
  - Draft OpenAPI specification.
  - Implement mutual TLS (mTLS) for secure communication.
  - Set up API Gateway routing.

### Phase 3: Data Ingestion Prototype
- **Milestone**: Raw telemetry flow validation.
- **Deliverables**:
  - Implement sensor client.
  - Ingest and store the first 2 days of raw sensor data in Amazon S3.
  - Configure AWS Lambda trigger for basic telemetry validation.

### Phase 4: Denoising LNN Service
- **Milestone**: LFM Pre-processing component deployment.
- **Deliverables**:
  - Fine-tune LFM encoder on cleaned historical data.
  - Benchmark performance: verify latency remains under 50 ms per weather station.

### Phase 5: Heat‑Index Module
- **Milestone**: Deterministic calculator integration.
- **Deliverables**:
  - Implement Lu & Romps apparent temperature calculation algorithm.
  - Conduct unit testing with known baseline inputs (e.g., verifying 30 °C temp / 25 °C dew point resolves to ~33 °C).

### Phase 6: GNN Forecast Engine
- **Milestone**: Predictive model training.
- **Deliverables**:
  - Build spatial graph structure linking multiple AW stations.
  - Run model training on historical weather datasets.
  - Generate 24-hour temperature and heat-index forecasts for a target test station.

### Phase 7: Integration & End‑to‑End Demo
- **Milestone**: Full pipeline assembly.
- **Deliverables**:
  - Connect all services: API Gateway $\rightarrow$ Denoising LNN $\rightarrow$ Heat-Index Module $\rightarrow$ GNN Forecasting $\rightarrow$ Dashboard.
  - Record live system demo video.
  - Complete README and LFM model documentation.

### Phase 8: Review & Iterate
- **Milestone**: Project completion.
- **Deliverables**:
  - Incorporate user and stakeholder feedback.
  - Address bug fixes and optimize bottlenecks.
  - Prepare the final project report and IaC/deployment scripts.

---

## Operational Baseline
All codebase files live in a single Git repository protected by branch protection rules. Continuous Integration (CI) automatically runs unit and integration tests on all PR branches.

---

## Related
- [[concepts/system-architecture]]
