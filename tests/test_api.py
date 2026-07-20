import unittest
from fastapi.testclient import TestClient
from src.api.main import app

class TestKloudtechAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.valid_headers = {"x-kloudtrack-key": "kloudtrack_secret_key_123"}

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_dashboard_unauthorized(self):
        response = self.client.get("/telemetry/dashboard")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing or Invalid API key", response.json()["detail"])

    def test_dashboard_success(self):
        response = self.client.get("/telemetry/dashboard", headers=self.valid_headers)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertGreater(len(json_data["data"]), 0)

    def test_station_current_success(self):
        response = self.client.get("/telemetry/station/st_0/current", headers=self.valid_headers)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["data"]["station"]["id"], "st_0")

    def test_station_current_not_found(self):
        response = self.client.get("/telemetry/station/st_9999/current", headers=self.valid_headers)
        self.assertEqual(response.status_code, 404)

    def test_telemetry_record_by_id(self):
        response = self.client.get("/telemetry/record/98765", headers=self.valid_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["telemetry"]["id"], 98765)

    def test_variable_history_invalid_name(self):
        response = self.client.get("/telemetry/station/st_0/history/invalid_variable", headers=self.valid_headers)
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

    def test_root_serve_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("KLOUDTECH", response.text)

if __name__ == "__main__":
    unittest.main()
