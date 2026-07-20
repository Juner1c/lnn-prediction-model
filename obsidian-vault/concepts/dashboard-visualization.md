---
title: Real-Time Heat-Index Dashboard & UI/UX Architecture
category: concept
tags: [dashboard, frontend-design, ui-ux, leaflet, chartjs, telemetry, fastapi, glassmorphism]
sources: [static/index.html, static/style.css, static/app.js, src/api/main.py]
created: 2026-07-20T12:28:00Z
updated: 2026-07-20T12:28:00Z
---

# Real-Time Heat-Index Dashboard & UI/UX Architecture

This concept note documents the web frontend architecture, visual design system, and microservice API integration built in Phase 7 applying the **`frontend-design`** skill.

---

## 1. Visual Identity & Aesthetic Direction

* **Design Persona**: Meteorological Command Center / Continuous-Time Observatory UI.
* **Palette Tokens (Mandatory Project Color Scheme: Yellow-Orange, Black, and White)**:
  * Pitch Black Base: `#000000` / `#0A0A0A`
  * Glass Dark Surface: `rgba(18, 18, 18, 0.85)` with `backdrop-filter: blur(16px)`
  * Pure White Text: `#FFFFFF`
  * Muted Silver Text: `#A1A1AA`
  * Primary Yellow-Orange Accents: `#FFD60A` (Warm Yellow), `#FF9F0A` (Solar Orange), `#FF4500` (Intense Heat Red-Orange)
* **Typography**: Google Fonts `Outfit` (Bold telemetry numbers & headers) and `Inter` (UI copy).

---

## 2. Integrated Visual Components

- **Realtime Telemetry Stream**: Auto-updates station cards, map markers, and banner metrics every 3 seconds.
- **Interactive Station Map**: Leaflet dark map with color-coded risk markers for all 7 weather stations.
- **Realtime Forecast Timeline & Prediction Confidence Range**: Chart.js 24h historical telemetry + 16-step ahead STGNN forecast trend with shaded upper/lower prediction bounds.
- **Interactive Action Controls**: Functional `Refresh Realtime Data` button and metric tab toggles (`Heat Index`, `Temperature`, `Humidity`).
- **Backend Calculation Integration**: Direct backend calculation via `/telemetry/dashboard` and `/api/v1/heat-index/calculate` microservice endpoints (frontend manual calculator removed per ponytail review).

---

## Related
- [[concepts/stgnn-forecast-engine]]
- [[concepts/lfm-denoiser-service]]
- [[references/kloudtech-api-specification]]
- [[entities/antidoom]]
