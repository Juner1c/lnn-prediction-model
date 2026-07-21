import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.data.heat_index import calculate_lu_romps_physiological_margin

client = TestClient(app)
API_KEY = "kloudtrack_secret_key_123"
HEADERS = {"x-kloudtrack-key": API_KEY}

def test_lu_romps_physiological_margin_baseline():
    res = calculate_lu_romps_physiological_margin(temperature_c=32.0, relative_humidity=70.0, wind_speed_kmh=10.0)
    assert "apparent_temperature_c" in res
    assert "wet_bulb_c" in res
    assert "cooling_reserve_margin_pct" in res
    assert "hyperthermia_risk" in res
    assert 0.0 <= res["cooling_reserve_margin_pct"] <= 100.0

def test_hotspot_detection_endpoint():
    response = client.get("/telemetry/hotspots/detect", headers=HEADERS)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "primary_hotspot" in json_data["data"]
    assert "all_hotspots" in json_data["data"]
    assert len(json_data["data"]["all_hotspots"]) == 7

    primary = json_data["data"]["primary_hotspot"]
    assert "anomalyScore" in primary
    assert "liquid_ai_root_cause_driver" in primary
    assert "lu_romps_physiology" in primary
