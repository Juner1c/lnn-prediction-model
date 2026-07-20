# Implementation Plan: Phase 7 (Dashboard & Visualization)

Phase 7 implements the **Real-Time Heat-Index Monitoring Dashboard** applying the **`frontend-design`** skill. The dashboard provides live telemetry visualization, interactive station maps, 16-day LNN/STGNN Heat Index forecast charts, and automated thermal risk alerts connected to our FastAPI microservice endpoints.

---

## Objectives of Phase 7 (Utilizing `frontend-design` Skill)

1. **Aesthetic Identity & Direction**:
   - **Persona**: Atmospheric Command Center / Deep Meteorological Station UI.
   - **Color Palette**: `#0A0E1A` (Midnight Navy base), `#151C2E` (Glassmorphic Card Surface), `#00F2FE` (Cyan Telemetry Pulse), `#FF4E50` (Extreme Danger Alert Gradient), `#F7B731` (Caution Gold).
   - **Typography**: Google Fonts `Outfit` (Headings & Big Stats) and `Inter` (Body & Data Tables).
2. **Interactive Station Map**:
   - Leaflet.js interactive map marking all 7 weather stations across Central Luzon (Coastal 0, Subic 1, Bataan 2, Pampanga 3, Nueva Ecija 4, Central Plain 5, San Fernando 6) with color-coded heat risk markers.
3. **Live Telemetry & Forecast Charts**:
   - Chart.js 24-hour historical telemetry curves (Temperature, Humidity, Heat Index) + 16-step ahead LNN/STGNN forecasts.
4. **Calculators & API Controls**:
   - Direct integration with `/telemetry/dashboard` and `/api/v1/heat-index/calculate` endpoints.
5. **Dashboard Files**:
   - `static/index.html` (Full HTML5 Dashboard structure)
   - `static/style.css` (Vanilla CSS styling with glassmorphism, glowing risk indicators, responsive grid)
   - `static/app.js` (JavaScript logic for API polling, Leaflet map rendering, Chart.js updates, interactive heat index calculator)
6. **FastAPI Static File Serving (`src/api/main.py`)**:
   - Mount `/static` and serve `index.html` on root `/`.

---

## Verification Plan

### Automated Verification
- Run `python -m unittest discover tests` (ensure API and model tests remain 100% PASS).
- Verify static route in `src/api/main.py`.

### Knowledge Vault Update
- Create `obsidian-vault/concepts/dashboard-visualization.md`.
- Update `index.md`, `log.md`, and `hot.md`.
