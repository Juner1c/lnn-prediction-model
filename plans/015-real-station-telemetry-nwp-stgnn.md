# Implementation Plan 015: Connect Real Per-Station Telemetry & Physical NWP to STGNN/LNN Forecast Engine

> **Plan ID**: `015-real-station-telemetry-nwp-stgnn`  
> **Status**: In Progress  
> **Author**: Senior AI Systems, ML & Bio-Meteorology Advisor (`/improve`, `/ponytail`, `/impl-validator`, `/antidoom`)  
> **Dependencies**: `010-comprehensive-codebase-audit`, `011-fix-all-codebase-flaws`, `012-fix-graph-accuracy-real-data`, `013-liquid-ai-pinn-heat-hotspot-engine`, `014-deep-system-audit-and-flaw-ledger`  

---

## 1. Root Cause Analysis of Identical Station Forecast Curves

Visual inspection of UI station cards (Coastal Station 0, Subic Station 1, Bataan Station 2) revealed that all stations were displaying **100% identical forecast curve shapes**.

Deep audit of `src/api/routes.py` uncovered two primary root causes:

### Cause 1: Station 0 Copy-Paste Fallback (`+ 0.3 * idx`)
- **Location**: `src/api/routes.py` lines 88–112.
- **Flaw**: `load_real_openmeteo_telemetry()` fetched Open-Meteo telemetry *only* for `MOCK_STATIONS[0]` (Coastal Station 0). For stations 1 through 6, it copied Station 0's readings and added `idx * 0.3` to temperature and `idx * 0.5` to humidity.
- **Fix**: Query Open-Meteo independently for all 7 station coordinates (`lat`, `lon`), capturing real distinct micro-climate telemetry and physical numerical weather predictions (NWP).

### Cause 2: Hardcoded Analytical Sine Wave Overlay Formula
- **Location**: `src/api/routes.py` lines 308–324.
- **Flaw**: `get_station_forecast()` computed station offsets using a hardcoded trigonometric formula:
  $$3.2 \sin\left(\frac{h-8}{24} 2\pi\right) + 1.8 \sin\left(\frac{h}{3.5 \cdot 24} 2\pi\right) + 2.2 \sin\left(\frac{h}{7 \cdot 24} 2\pi\right)$$
  Because this analytical formula was identical for all nodes, every station produced the exact same 3-peak wave shape.
- **Fix**: Eliminate hardcoded sine wave additions. Drive short-term nowcasts (0–16 steps) directly via `SpatialTemporalGNN` predictions and extend long-range horizons using real per-station NWP physical forecast tensors.

---

## 2. Proposed Changes & Architecture

### Component 1: Multi-Station Ingestion (`src/api/routes.py`)
- Update `load_real_openmeteo_telemetry()` to query Open-Meteo for all 7 stations' exact coordinates.
- Return distinct historical and 16-day physical forecast arrays per station node.

### Component 2: Physics-GNN Forecast Blending (`src/api/routes.py`)
- Pass distinct 96-step 5-feature history tensors into `SpatialTemporalGNN` + `LiquidDenoisingService`.
- Combine STGNN short-term spatial predictions with station-specific physical NWP forecast baselines, applying $C^0$ continuity smoothing at $h=0$.

---

## 3. Verification Plan

### Automated Tests
- Run `pytest -v` to confirm all 36 unit tests pass.
- Add test verifying that station forecasts for Coastal Station 0 and Nueva Ecija Station 4 return distinct, non-identical forecast trajectory arrays.

### Manual & Visual Verification
- Deploy local dev server (`python -m uvicorn src.api.main:app`).
- Verify station cards and Chart.js forecast curves show distinct physical trajectories per station.
