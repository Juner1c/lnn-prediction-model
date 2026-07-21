# Implementation Plan 012: Fix Graph Nowcasting/Forecasting Inaccuracies & Eliminate Fake Sine Wave Facades

> **Plan ID**: `012-fix-graph-accuracy-real-data`  
> **Status**: Completed  
> **Author**: Senior AI Systems & ML Advisor (`/improve`, `/ponytail`, `/impl-validator`)  
> **Dependencies**: `010-comprehensive-codebase-audit`, `011-fix-all-codebase-flaws`  

---

## 1. Root Cause Audit & Flaw Analysis

A rigorous deep-audit of `src/api/routes.py` and `static/app.js` identified 4 major root causes responsible for the inaccurate, synthetic-looking graph in the UI:

### Root Cause 1: `Math.sin((i / 96) * Math.PI * 4)` Fallback in `app.js`
- **Location**: `static/app.js` lines 451–454.
- **Flaw**: When `updateChart()` renders before `fetchStationForecast()` completes downloading station forecast data, `fc` is `undefined`. `app.js` falls back to `Math.sin((i / 96) * Math.PI * 4) * 3.5`, generating **2.5 synthetic sine-wave cycles in 24 hours** (3 artificial sharp peaks).
- **Fix**: Wait for `fetchStationForecast()` or use real telemetry history cached from `/telemetry/dashboard` instead of generating artificial sine waves.

### Root Cause 2: 2024-vs-2026 Timestamp Shift in Telemetry Ingestion
- **Location**: `src/api/routes.py` lines 146–189.
- **Flaw**: The CSV dataset `data/timeseries_15min_clean.csv` ends on July 31, 2024. When `routes.py` reads the last 96 rows, `latest_ts` is set to `2024-07-31T23:45:00+0800`. When Chart.js receives timestamps from 2024 while the system clock is 2026, the 24h history timeline and 30-day forecast horizon desynchronize from the present date.
- **Fix**: In `routes.py`, shift the 96 historical 15-minute time steps so that the 96th step (`lastDate`) aligns continuously with the current local Manila timestamp (`pd.Timestamp.now(tz="Asia/Manila")`).

### Root Cause 3: Artificial Sine-Wave Overlays in API Forecast Generation
- **Location**: `src/api/routes.py` lines 308–325.
- **Flaw**: The 30-day forecast generator computes `offset_hi` by adding multi-frequency `np.sin()` wave terms (`diurnal * 3.2 + synoptic_3d + synoptic_7d`). This creates rigid, repeating sine wave oscillations instead of using physical baseline autoregression + neural network weights.
- **Fix**: Remove artificial sine-wave formulas. Drive short-term nowcast/forecast (0–12 hours) using raw `SpatialTemporalGNN` multi-node predictions and extend extended-horizon forecasts (12h–30d) using physical diurnal solar radiation models ($T_{\text{max}}$ at 14:00, $T_{\text{min}}$ at 04:00) scaled to actual station baselines.

### Root Cause 4: Multi-Metric Forecast Contamination Rule Violation
- **Location**: `static/app.js` line 496.
- **Flaw**: When switching metric tabs (Temperature, Relative Humidity), `app.js` multiplied diurnal sine waves by arbitrary constants (`currentMetric === 'humidity' ? -6.0 : 3.0`) instead of loading actual historical and predicted metric values from `fc.history_24h[currentMetric]` and `fc.forecast_30day[currentMetric]`.
- **Fix**: Strictly pass metric-specific historical and forecast arrays for Temperature (°C), Humidity (%), and Heat Index (°C) from `fc`.

---

## 2. Proposed Structural Changes

### Component 1: FastAPI API Routes (`src/api/routes.py`)
- Shift CSV history timestamps to end exactly at current local time (`now_pht`).
- Compute real `history_24h` arrays for `temperature`, `humidity`, and `heatIndex` for all 7 stations.
- Pass real 96-step history tensor `[1, 7, 96, 5]` into trained `SpatialTemporalGNN` model.
- Use `SpatialTemporalGNN` predictions directly for the 16-step (4-hour) nowcast horizon and expand cleanly into 30-day forecasts without arbitrary sine-wave scaling.

### Component 2: Frontend Dashboard Script (`static/app.js`)
- Ensure `fetchStationForecast()` completes before initial chart render so `fc` is never `undefined`.
- Eliminate `Math.sin((i / 96) * Math.PI * 4)` fallback. Use real station history points directly.
- Support metric tab switching (Heat Index, Air Temperature, Relative Humidity) by binding exact metric-specific arrays.

---

## 3. Verification Plan

### Automated Tests
- Run `pytest -v` to ensure all 34 tests pass.
- Verify `test_api.py` returns valid non-empty `history_24h` and `forecast_30day` objects.

### Manual & Visual Verification
- Run `python scripts/deploy.py` to confirm server health.
- Inspect `http://127.0.0.1:8000/` chart output to verify:
  1. 24h History line matches real 24-hour diurnal profile (1 daily peak, 1 daily trough).
  2. No 3-peak synthetic sine waves or artificial noise spikes.
  3. Forecast starts continuously at $h=0$ ($C^0$ continuity) from the latest 24h reading.
