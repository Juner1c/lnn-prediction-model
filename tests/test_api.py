import unittest
from fastapi.testclient import TestClient
from src.api.main import app

from src.api.config import settings

from src.api.client import proxy_client

class TestKloudtechAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Seed proxy client cache with realistic Kloudtech API response structure
        import time
        now = time.time() + 99999.0
        sample_dash = {
            "success": True,
            "message": "Realtime telemetry retrieved",
            "data": [
                {
                    "station": {
                        "id": "Rjz2dbXW",
                        "stationName": "Popolon AWS - Palayan City",
                        "location": [121.05767, 15.53683],
                        "organizationId": 1,
                        "isActive": True
                    },
                    "telemetry": {
                        "id": 4779714,
                        "recordedAt": "2026-07-22T05:46:56.000Z",
                        "temperature": 34.93,
                        "humidity": 79.87,
                        "heatIndex": 56.15,
                        "wind": {"speed": 1.78, "direction": 144.7}
                    }
                },
                {
                    "station": {
                        "id": "4VAl2p9k",
                        "stationName": "Cabanatuan AWS",
                        "location": [120.96802, 15.48621],
                        "organizationId": 1,
                        "isActive": True
                    },
                    "telemetry": {
                        "id": 4779715,
                        "recordedAt": "2026-07-22T05:46:56.000Z",
                        "temperature": 32.5,
                        "humidity": 68.0,
                        "heatIndex": 38.5,
                        "wind": {"speed": 3.2, "direction": 90.0}
                    }
                }
            ]
        }
        sample_hist = {
            "success": True,
            "data": {
                "station": sample_dash["data"][0]["station"],
                "telemetry": [
                    {"id": 100, "recordedAt": "2026-07-22T05:00:00Z", "temperature": 34.0, "humidity": 75.0, "heatIndex": 50.0, "wind": {"speed": 2.0}}
                    for _ in range(96)
                ]
            }
        }
        proxy_client._cache["/telemetry/dashboard:"] = {"timestamp": now, "data": sample_dash}
        proxy_client._cache["/telemetry/station/Rjz2dbXW/history:[('take', 96)]"] = {"timestamp": now, "data": sample_hist}
        proxy_client._cache["/telemetry/station/4VAl2p9k/history:[('take', 96)]"] = {"timestamp": now, "data": sample_hist}

    def setUp(self):
        self.client = TestClient(app)
        self.valid_headers = {"x-kloudtrack-key": settings.API_KEY}



    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_calculate_unauthorized(self):
        payload = {"temperature": 32.0, "humidity": 70.0}
        response = self.client.post("/api/v1/heat-index/calculate", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing or Invalid API key", response.json()["detail"])

    def test_dashboard_success(self):
        response = self.client.get("/telemetry/dashboard", headers=self.valid_headers)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertGreater(len(json_data["data"]), 0)

    def test_station_current_success(self):
        dash_res = self.client.get("/telemetry/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        stations = dash_res.json()["data"]
        st_id = stations[0]["station"]["id"]

        response = self.client.get(f"/telemetry/station/{st_id}/current", headers=self.valid_headers)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["data"]["station"]["id"], st_id)

    def test_station_current_not_found(self):
        response = self.client.get("/telemetry/station/non_existent_station_999/current", headers=self.valid_headers)
        self.assertEqual(response.status_code, 404)

    def test_telemetry_record_by_id(self):
        dash_res = self.client.get("/telemetry/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        stations = dash_res.json()["data"]
        rec_id = stations[0]["telemetry"]["id"]

        response = self.client.get(f"/telemetry/record/{rec_id}", headers=self.valid_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["telemetry"]["id"], rec_id)

    def test_variable_history_invalid_name(self):
        dash_res = self.client.get("/telemetry/dashboard")
        st_id = dash_res.json()["data"][0]["station"]["id"]
        response = self.client.get(f"/telemetry/station/{st_id}/history/invalid_variable", headers=self.valid_headers)
        self.assertEqual(response.status_code, 400)

    def test_heat_index_calculation_endpoint(self):
        payload = {"temperature": 32.0, "humidity": 70.0}
        response = self.client.post("/api/v1/heat-index/calculate", json=payload, headers=self.valid_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertGreaterEqual(data["heatIndex"], 39.0)
        self.assertEqual(data["riskLevel"], "Extreme Caution")

    def test_proxy_client_config(self):
        from src.api.client import proxy_client
        self.assertEqual(proxy_client.base_url, "https://api.kloudtechsea.com/api/v1")
        self.assertEqual(proxy_client.cache_ttl, 60)

    def test_station_forecast_curves_are_distinct(self):
        dash_res = self.client.get("/telemetry/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        stations = dash_res.json()["data"]
        st0_id = stations[0]["station"]["id"]
        st1_id = stations[1]["station"]["id"] if len(stations) > 1 else st0_id

        res0 = self.client.get(f"/telemetry/station/{st0_id}/forecast", headers=self.valid_headers)
        res1 = self.client.get(f"/telemetry/station/{st1_id}/forecast", headers=self.valid_headers)
        self.assertEqual(res0.status_code, 200)
        self.assertEqual(res1.status_code, 200)

        fc0 = res0.json()["data"]["forecast_30day"]["heatIndex"]["mean"]
        fc1 = res1.json()["data"]["forecast_30day"]["heatIndex"]["mean"]


        # Shift values by baseline to compare raw shape variations
        shape0 = [v - fc0[0] for v in fc0]
        shape1 = [v - fc1[0] for v in fc1]

        # Verify that station 0 (Coastal) and station 3 (Pampanga) do NOT have identical forecast curve shapes
        diffs = [abs(s0 - s1) for s0, s1 in zip(shape0, shape1)]
        max_diff = max(diffs)
        self.assertGreater(max_diff, 0.1, f"Forecast curves across different micro-climates must be distinct! Max diff: {max_diff}")

if __name__ == "__main__":
    unittest.main()

