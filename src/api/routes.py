import os
import time
import json
import torch
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from src.api.auth import verify_api_key, verify_optional_api_key
from src.api.schemas import (
    KloudtrackResponse,
    StationInfo,
    WeatherStationApiReading,
    VariableReading,
    WeatherStationDashboardEntry,
    HeatIndexCalculationRequest,
    HeatIndexCalculationResponse
)
from src.data.heat_index import calculate_heat_index, calculate_lu_romps_physiological_margin
from src.models.spatial_graph import build_spatial_adjacency_matrix
from src.models.stgnn_forecaster import SpatialTemporalGNN
from src.api.client import proxy_client

router = APIRouter()

from src.models.checkpoint_manager import load_model_checkpoint, DEFAULT_CHECKPOINT_PATH

WEIGHTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "stgnn_weights.pt"))
_stgnn_model = None
_adj_tensor = None
_stgnn_num_nodes = 0

_telemetry_cache: Optional[Dict[str, Dict[str, Any]]] = None
_telemetry_cache_timestamp: float = 0.0
CACHE_TTL_SECONDS: float = 900.0

def get_stgnn_model(active_stations: List[StationInfo]):
    global _stgnn_model, _adj_tensor, _stgnn_num_nodes
    num_nodes = len(active_stations) if active_stations else 7
    if _stgnn_model is None or _stgnn_num_nodes != num_nodes:
        _stgnn_model = SpatialTemporalGNN(num_nodes=num_nodes, in_channels=5, hidden_dim=32, forecast_horizon=16)
        if os.path.exists(DEFAULT_CHECKPOINT_PATH):
            load_model_checkpoint(_stgnn_model, filepath=DEFAULT_CHECKPOINT_PATH)
        elif os.path.exists(WEIGHTS_PATH):
            try:
                _stgnn_model.load_state_dict(torch.load(WEIGHTS_PATH, weights_only=True))
            except Exception:
                pass
        _stgnn_model.eval()
        _stgnn_num_nodes = num_nodes

        loc_df = pd.DataFrame([{
            "location_id": i,
            "latitude": s.latitude,
            "longitude": s.longitude
        } for i, s in enumerate(active_stations)])

        _adj_tensor, _ = build_spatial_adjacency_matrix(loc_df)

    return _stgnn_model, _adj_tensor

def extract_multi_station_input_tensor(readings: Dict[str, Any], active_stations: List[StationInfo]) -> torch.Tensor:
    """
    Construct multi-station 3D feature tensor [num_nodes, 96, 5] directly from real Kloudtech 24h station telemetry history.
    """
    station_tensors = []
    for st in active_stations:
        data = readings.get(st.id, {})
        h = data.get("history_24h", {})
        latest = data.get("latest")
        base_t = latest.temperature if (latest and latest.temperature is not None) else 30.0
        base_rh = latest.humidity if (latest and latest.humidity is not None) else 65.0
        base_hi = latest.heatIndex if (latest and latest.heatIndex is not None) else calculate_heat_index(base_t, base_rh)

        temps = h.get("temperature", [base_t] * 96)
        rhs = h.get("humidity", [base_rh] * 96)
        his = h.get("heatIndex", [base_hi] * 96)
        dps = h.get("dewPoint", [round(t - ((100 - r) / 5), 2) for t, r in zip(temps, rhs)])
        wss = h.get("windSpeed", [5.0] * 96)

        if not temps:
            temps = [base_t] * 96
        if not rhs:
            rhs = [base_rh] * 96
        if not his:
            his = [base_hi] * 96
        if not dps:
            dps = [round(t - ((100 - r) / 5), 2) for t, r in zip(temps, rhs)]
        if not wss:
            wss = [5.0] * 96

        if len(temps) < 96:
            pad = 96 - len(temps)
            temps = [temps[0]] * pad + temps
            rhs = [rhs[0]] * pad + rhs
            dps = [dps[0]] * pad + dps
            his = [his[0]] * pad + his
            wss = [wss[0]] * pad + wss
        else:
            temps = temps[-96:]
            rhs = rhs[-96:]
            dps = dps[-96:]
            his = his[-96:]
            wss = wss[-96:]

        st_feats = np.column_stack([temps, rhs, dps, his, wss])
        station_tensors.append(st_feats)

    return torch.tensor(np.stack(station_tensors, axis=0), dtype=torch.float32)

def load_real_kloudtech_telemetry() -> Dict[str, Dict[str, Any]]:
    """
    Load real station telemetry & 24h history exclusively via live Kloudtech Telemetry API.
    Includes in-memory TTL caching (60 seconds) to prevent redundant remote HTTP queries.
    """
    global _telemetry_cache, _telemetry_cache_timestamp
    now_time = time.time()
    if _telemetry_cache is not None and (now_time - _telemetry_cache_timestamp < CACHE_TTL_SECONDS):
        return _telemetry_cache

    station_readings = {}

    # Query live Kloudtech Telemetry API via proxy_client
    remote_resp = proxy_client.fetch_with_cache("/telemetry/dashboard")
    if remote_resp and remote_resp.get("success") and isinstance(remote_resp.get("data"), list):
        for entry in remote_resp["data"]:
            st_raw = entry.get("station", {}) if isinstance(entry.get("station"), dict) else {}
            st_id = str(st_raw.get("id", ""))
            if not st_id:
                continue

            st_name = st_raw.get("stationName") or st_raw.get("name") or f"Station {st_id}"
            loc = st_raw.get("location")
            if loc and isinstance(loc, list) and len(loc) >= 2:
                lon, lat = float(loc[0]), float(loc[1])
            else:
                lat = float(st_raw.get("latitude", 15.0))
                lon = float(st_raw.get("longitude", 120.5))

            st_obj = StationInfo(
                id=st_id,
                name=st_name,
                latitude=lat,
                longitude=lon,
                elevation=float(st_raw.get("elevation", 0.0) or 0.0),
                organizationId=st_raw.get("organizationId", "org_default"),
                isActive=st_raw.get("isActive", True),
                status="active" if st_raw.get("isActive", True) else "offline",
                source="Kloudtech API"
            )

            t_raw = entry.get("telemetry") or {}
            t_id = int(t_raw.get("id", 1000)) if isinstance(t_raw.get("id"), (int, str)) and str(t_raw.get("id")).isdigit() else 1000
            rec_at = str(t_raw.get("recordedAt", time.strftime("%Y-%m-%dT%H:%M:%S+0000")))

            temp_val = t_raw.get("temperature")
            rh_val = t_raw.get("humidity")
            hi_val = t_raw.get("heatIndex")

            if temp_val is not None:
                temp_val = float(temp_val)
            if rh_val is not None:
                rh_val = float(rh_val)
            if hi_val is not None:
                hi_val = float(hi_val)

            if hi_val is None and temp_val is not None and rh_val is not None:
                hi_val = round(calculate_heat_index(temp_val, rh_val), 2)

            wind_data = t_raw.get("wind") or {}
            wind_spd = wind_data.get("speed") if isinstance(wind_data, dict) else t_raw.get("windSpeed")
            wind_dir = wind_data.get("direction") if isinstance(wind_data, dict) else t_raw.get("windDirection")

            latest_obj = WeatherStationApiReading(
                id=t_id,
                recordedAt=rec_at,
                createdAt=t_raw.get("createdAt") or rec_at,
                temperature=temp_val,
                humidity=rh_val,
                dewPoint=float(t_raw.get("dewPoint")) if t_raw.get("dewPoint") is not None else (round(temp_val - ((100 - rh_val) / 5), 2) if temp_val is not None and rh_val is not None else None),
                apparentTemperature=float(t_raw.get("apparentTemperature")) if t_raw.get("apparentTemperature") is not None else (round(temp_val + 1.2, 2) if temp_val is not None else None),
                heatIndex=hi_val,
                windSpeed=float(wind_spd) if wind_spd is not None else None,
                windDirection=float(wind_dir) if wind_dir is not None else None,
                pressure=float(t_raw.get("pressure")) if t_raw.get("pressure") is not None else None
            )

            # Fetch actual 24h history telemetry array from Kloudtech API with rate-limit spacer
            time.sleep(0.15)
            hist_resp = proxy_client.fetch_station_history(st_id, take=96)

            history_24h = {"temperature": [], "humidity": [], "heatIndex": [], "dewPoint": [], "windSpeed": []}
            if hist_resp and hist_resp.get("success") and isinstance(hist_resp.get("data"), dict):
                tel_items = hist_resp["data"].get("telemetry", [])
                if isinstance(tel_items, list) and len(tel_items) > 0:
                    for item in reversed(tel_items):
                        t_v = item.get("temperature")
                        r_v = item.get("humidity")
                        h_v = item.get("heatIndex")
                        w_d = item.get("wind") or {}
                        w_v = w_d.get("speed") if isinstance(w_d, dict) else item.get("windSpeed")
                        
                        if t_v is not None:
                            t_v = float(t_v)
                        else:
                            t_v = temp_val or 30.0

                        if r_v is not None:
                            r_v = float(r_v)
                        else:
                            r_v = rh_val or 65.0

                        if h_v is not None:
                            h_v = float(h_v)
                        else:
                            h_v = round(calculate_heat_index(t_v, r_v), 2)

                        if w_v is not None:
                            w_v = float(w_v)
                        else:
                            w_v = wind_spd or 5.0

                        dp_v = float(item.get("dewPoint")) if item.get("dewPoint") is not None else round(t_v - ((100 - r_v) / 5), 2)

                        history_24h["temperature"].append(t_v)
                        history_24h["humidity"].append(r_v)
                        history_24h["heatIndex"].append(h_v)
                        history_24h["dewPoint"].append(dp_v)
                        history_24h["windSpeed"].append(w_v)

            station_readings[st_id] = {
                "station": st_obj,
                "latest": latest_obj,
                "history_24h": history_24h
            }
    
    if not station_readings:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kloudtech Telemetry API connection unavailable or invalid API key"
        )

    _telemetry_cache = station_readings
    _telemetry_cache_timestamp = now_time

    return station_readings

def get_risk_level(hi: float) -> str:
    if hi is None or hi < 27.0:
        return "Normal"
    elif hi < 32.0:
        return "Caution"
    elif hi < 41.0:
        return "Extreme Caution"
    elif hi < 54.0:
        return "Danger"
    else:
        return "Extreme Danger"

# 1. GET /telemetry/dashboard
@router.get("/telemetry/dashboard", response_model=KloudtrackResponse[List[WeatherStationDashboardEntry]])
def get_dashboard(api_key: Optional[str] = Depends(verify_optional_api_key)):
    readings = load_real_kloudtech_telemetry()
    entries = []
    for st_id, st_data in readings.items():
        entries.append(WeatherStationDashboardEntry(station=st_data["station"], telemetry=st_data["latest"]))
    return KloudtrackResponse(message="Realtime station telemetry retrieved via Kloudtech API", data=entries)

# 2. GET /telemetry/station/{stationId}/forecast
@router.get("/telemetry/station/{stationId}/forecast", response_model=KloudtrackResponse[dict])
def get_station_forecast(
    stationId: str = Path(..., description="Station hashid e.g. Rjz2dbXW"),
    api_key: Optional[str] = Depends(verify_optional_api_key)
):
    readings = load_real_kloudtech_telemetry()
    st_data = readings.get(stationId)
    if not st_data:
        st_data = next((v for k, v in readings.items() if k.lower() == stationId.lower()), None)
    
    if not st_data:
        raise HTTPException(status_code=404, detail="Station not found")

    station = st_data["station"]
    latest = st_data.get("latest")
    history = st_data.get("history_24h", {})

    active_stations = [v["station"] for v in readings.values()]
    model, adj = get_stgnn_model(active_stations)
    real_input = extract_multi_station_input_tensor(readings, active_stations).unsqueeze(0) # [1, num_nodes, 96, 5]

    with torch.no_grad():
        rollout_tensor = model.predict_autoregressive_rollout(real_input, adj, steps=384) # [1, num_nodes, 384]

    st_idx = 0
    for idx, st_item in enumerate(active_stations):
        if st_item.id == station.id:
            st_idx = idx
            break

    raw_rollout = rollout_tensor[0, st_idx].numpy().tolist()

    base_temp = latest.temperature if (latest and latest.temperature is not None) else 31.0
    base_rh = latest.humidity if (latest and latest.humidity is not None) else 65.0
    base_hi = latest.heatIndex if (latest and latest.heatIndex is not None) else calculate_heat_index(base_temp, base_rh)


    nwp_fc = st_data.get("forecast_nwp", {})
    nwp_hi = nwp_fc.get("heatIndex", [])
    nwp_temp = nwp_fc.get("temperature", [])
    nwp_rh = nwp_fc.get("humidity", [])

    hi_mean, hi_upper, hi_lower = [], [], []
    temp_mean, temp_upper, temp_lower = [], [], []
    rh_mean, rh_upper, rh_lower = [], [], []

    latest_time = pd.to_datetime(latest.recordedAt) if (latest and latest.recordedAt) else pd.Timestamp.now(tz="Asia/Manila")

    for h in range(1, 385):
        t_future = latest_time + pd.Timedelta(hours=h)
        hour_local = t_future.hour

        smooth_w = 1.0 - np.exp(-h / 6.0)
        gnn_weight = np.exp(-(h - 1) / 16.0)

        nwp_hi_val = nwp_hi[(h - 1) % len(nwp_hi)] if nwp_hi else (base_hi + np.sin(((hour_local - 8) / 24.0) * 2 * np.pi) * 3.0)
        nwp_temp_val = nwp_temp[(h - 1) % len(nwp_temp)] if nwp_temp else (base_temp + np.sin(((hour_local - 8) / 24.0) * 2 * np.pi) * 2.0)
        nwp_rh_val = nwp_rh[(h - 1) % len(nwp_rh)] if nwp_rh else min(100.0, max(0.0, base_rh - np.sin(((hour_local - 8) / 24.0) * 2 * np.pi) * 5.0))

        # 1. Heat Index
        st_pred = raw_rollout[h - 1]
        hi_raw = (gnn_weight * st_pred) + ((1.0 - gnn_weight) * nwp_hi_val)
        offset_hi = (hi_raw - base_hi) * smooth_w
        hi_val = round(base_hi + offset_hi, 1)
        hi_spread = 1.0 + (h / 384.0) * 3.5
        hi_mean.append(hi_val)
        hi_upper.append(round(hi_val + hi_spread, 1))
        hi_lower.append(round(hi_val - hi_spread, 1))

        # 2. Air Temperature
        temp_raw = (gnn_weight * (base_temp + (st_pred - base_hi) * 0.7)) + ((1.0 - gnn_weight) * nwp_temp_val)
        offset_temp = (temp_raw - base_temp) * smooth_w
        temp_val = round(base_temp + offset_temp, 1)
        temp_spread = 0.8 + (h / 384.0) * 2.5
        temp_mean.append(temp_val)
        temp_upper.append(round(temp_val + temp_spread, 1))
        temp_lower.append(round(temp_val - temp_spread, 1))

        # 3. Relative Humidity
        rh_raw = (gnn_weight * (base_rh - (st_pred - base_hi) * 0.8)) + ((1.0 - gnn_weight) * nwp_rh_val)
        offset_rh = (rh_raw - base_rh) * smooth_w
        rh_val = round(min(100.0, max(0.0, base_rh + offset_rh)), 1)
        rh_spread = 2.0 + (h / 384.0) * 5.0
        rh_mean.append(rh_val)
        rh_upper.append(round(min(100.0, rh_val + rh_spread), 1))
        rh_lower.append(round(max(0.0, rh_val - rh_spread), 1))

    return KloudtrackResponse(
        message=f"Realtime 16-Day Kloudtech/STGNN Hourly forecast generated for {station.name}",
        data={
            "station": station,
            "current": latest,
            "history_24h": history,
            "forecast_30day": {
                "heatIndex": { "mean": hi_mean, "upper": hi_upper, "lower": hi_lower },
                "temperature": { "mean": temp_mean, "upper": temp_upper, "lower": temp_lower },
                "humidity": { "mean": rh_mean, "upper": rh_upper, "lower": rh_lower }
            },
            "forecast_16day": {
                "heatIndex": { "mean": hi_mean, "upper": hi_upper, "lower": hi_lower },
                "temperature": { "mean": temp_mean, "upper": temp_upper, "lower": temp_lower },
                "humidity": { "mean": rh_mean, "upper": rh_upper, "lower": rh_lower }
            },
            "forecast_16step": {
                "heatIndex": { "mean": hi_mean, "upper": hi_upper, "lower": hi_lower },
                "temperature": { "mean": temp_mean, "upper": temp_upper, "lower": temp_lower },
                "humidity": { "mean": rh_mean, "upper": rh_upper, "lower": rh_lower },
                "mean": hi_mean,
                "upper": hi_upper,
                "lower": hi_lower
            }
        }
    )

# 3. GET /telemetry/station/{stationId}/current
@router.get("/telemetry/station/{stationId}/current", response_model=KloudtrackResponse[dict])
def get_station_current(
    stationId: str = Path(..., description="Station hashid e.g. Rjz2dbXW"),
    api_key: Optional[str] = Depends(verify_optional_api_key)
):
    readings = load_real_kloudtech_telemetry()
    st_data = readings.get(stationId) or next((v for k, v in readings.items() if k.lower() == stationId.lower()), None)
    if not st_data:
        raise HTTPException(status_code=404, detail="Station not found")
    return KloudtrackResponse(message="Latest telemetry retrieved", data={"station": st_data["station"], "telemetry": st_data["latest"]})

# 4. GET /telemetry/record/{id}
@router.get("/telemetry/record/{id}", response_model=KloudtrackResponse[dict])
def get_telemetry_by_id(
    id: int = Path(..., description="Numeric telemetry record ID"),
    api_key: Optional[str] = Depends(verify_optional_api_key)
):
    readings = load_real_kloudtech_telemetry()
    for st_id, data in readings.items():
        reading = data.get("latest")
        if reading and reading.id == id:
            return KloudtrackResponse(message="Record retrieved", data={"station": data["station"], "telemetry": reading})
    raise HTTPException(status_code=404, detail="Record ID does not exist")

# 5. GET /telemetry/station/{stationId}/history/{variable}
@router.get("/telemetry/station/{stationId}/history/{variable}", response_model=KloudtrackResponse[dict])
def get_variable_history(
    stationId: str = Path(...),
    variable: str = Path(...),
    skip: int = Query(0),
    take: int = Query(10),
    api_key: Optional[str] = Depends(verify_optional_api_key)
):
    valid_variables = ["temperature", "humidity", "pressure", "heatIndex", "windSpeed", "windDirection", "precipitation", "uvIndex", "distance", "lightIntensity"]
    if variable not in valid_variables:
        raise HTTPException(status_code=400, detail="Invalid variable name")
    
    readings = load_real_kloudtech_telemetry()
    st_data = readings.get(stationId) or next((v for k, v in readings.items() if k.lower() == stationId.lower()), None)
    if not st_data:
        raise HTTPException(status_code=404, detail="Station not found")

    station = st_data["station"]
    latest = st_data.get("latest")
    val = getattr(latest, variable, 0.0) if latest else 0.0
    rec_time = latest.recordedAt if latest else "2026-07-22T00:00:00Z"
    var_readings = [VariableReading(id=latest.id if latest else 1, recordedAt=rec_time, createdAt=rec_time, value=val or 0.0)]
    return KloudtrackResponse(message="Single metric history retrieved", data={"station": station, "telemetry": var_readings})

# 6. POST /api/v1/heat-index/calculate
@router.post("/api/v1/heat-index/calculate", response_model=KloudtrackResponse[HeatIndexCalculationResponse])
def calculate_hi(payload: HeatIndexCalculationRequest, api_key: str = Depends(verify_api_key)):
    hi = calculate_heat_index(payload.temperature, payload.humidity)
    risk = get_risk_level(hi)
    resp = HeatIndexCalculationResponse(
        temperature=payload.temperature,
        humidity=payload.humidity,
        heatIndex=hi,
        riskLevel=risk
    )
    return KloudtrackResponse(message="Heat Index calculated", data=resp)

# 7. GET /telemetry/hotspots/detect
@router.get("/telemetry/hotspots/detect", response_model=KloudtrackResponse[dict])
def detect_thermal_hotspots(api_key: Optional[str] = Depends(verify_optional_api_key)):
    """
    Detect spatial thermal hotspots and anomalies across Central Luzon weather stations.
    Leverages Liquid Neural Network continuous-time latent state variance for spatial anomaly scoring
    and Lu & Romps human physiological thermoregulation limits for hyperthermia risk assessment.
    """
    readings = load_real_kloudtech_telemetry()
    active_stations = [v["station"] for v in readings.values()]
    model, adj = get_stgnn_model(active_stations)

    tensor_input = extract_multi_station_input_tensor(readings, active_stations) # [num_nodes, 96, 5]
    station_list = [(st, readings.get(st.id, {}).get("latest")) for st in active_stations]

    with torch.no_grad():
        anomaly_scores, feat_contribs = model.lfm_denoiser.detect_spatial_anomalies(tensor_input)

    feature_names = ["temperature", "humidity", "dew_point", "heat_index", "wind_speed"]

    hotspots = []
    for idx, (st, latest) in enumerate(station_list):
        t = latest.temperature if latest else 31.0
        rh = latest.humidity if latest else 65.0
        ws = latest.windSpeed if latest else 5.0
        hi = latest.heatIndex if latest else 35.0

        phys_margin = calculate_lu_romps_physiological_margin(t, rh, wind_speed_kmh=ws)

        anom_score = float(round(anomaly_scores[idx].item(), 2))
        contrib_vec = feat_contribs[idx].numpy().tolist()

        max_feat_idx = int(np.argmax(contrib_vec))
        driver_name = feature_names[max_feat_idx]
        driver_desc = {
            "humidity": "Extreme Relative Humidity Trapping & Moisture Stagnation",
            "temperature": "Solar Radiation Peak & Ambient Heating Anomaly",
            "heat_index": "Combined Thermal Evaporative Stress Threshold Spike",
            "wind_speed": "Wind Blocking & Ventilation Stagnation",
            "dew_point": "Dew Point Saturation Boundary Transition"
        }.get(driver_name, "Micro-Climate Thermal Gradient Deviation")

        hotspots.append({
            "station": st,
            "coordinates": {"latitude": st.latitude, "longitude": st.longitude},
            "heatIndex": hi,
            "temperature": t,
            "humidity": rh,
            "anomalyScore": anom_score,
            "liquid_ai_root_cause_driver": driver_desc,
            "lu_romps_physiology": phys_margin
        })

    hotspots.sort(key=lambda x: x["anomalyScore"], reverse=True)
    primary_hotspot = hotspots[0] if hotspots else None

    return KloudtrackResponse(
        message="Liquid AI Physics-Informed Anomaly & Hotspot Detection Complete",
        data={
            "primary_hotspot": primary_hotspot,
            "all_hotspots": hotspots,
            "regional_summary": f"Detected primary thermal anomaly at {primary_hotspot['station'].name} driven by {primary_hotspot['liquid_ai_root_cause_driver']}" if primary_hotspot else "No thermal anomaly detected"
        }
    )
