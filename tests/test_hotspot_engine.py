import unittest
from fastapi.testclient import TestClient
from src.api.main import app
from src.data.heat_index import calculate_lu_romps_physiological_margin

client = TestClient(app)
API_KEY = "kloudtrack_secret_key_123"
HEADERS = {"x-kloudtrack-key": API_KEY}

class TestHotspotEngine(unittest.TestCase):
    def test_lu_romps_physiological_margin_baseline(self):
        res = calculate_lu_romps_physiological_margin(temperature_c=32.0, relative_humidity=70.0, wind_speed_kmh=10.0)
        self.assertIn("apparent_temperature_c", res)
        self.assertIn("wet_bulb_c", res)
        self.assertIn("cooling_reserve_margin_pct", res)
        self.assertIn("hyperthermia_risk", res)
        self.assertTrue(0.0 <= res["cooling_reserve_margin_pct"] <= 100.0)

    def test_hotspot_detection_endpoint(self):
        response = client.get("/telemetry/hotspots/detect", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertIn("primary_hotspot", json_data["data"])
        self.assertIn("all_hotspots", json_data["data"])
        self.assertEqual(len(json_data["data"]["all_hotspots"]), 7)

        primary = json_data["data"]["primary_hotspot"]
        self.assertIn("anomalyScore", primary)
        self.assertIn("liquid_ai_root_cause_driver", primary)
        self.assertIn("lu_romps_physiology", primary)

if __name__ == "__main__":
    unittest.main()

