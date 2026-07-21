import unittest
import os
import shutil
from src.data.validator import TelemetryValidator
from src.data.storage_adapter import LocalStorageAdapter, S3StorageAdapter
from src.data.ingestion_client import TelemetryIngestionClient

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestDataIngestion(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(BASE_DIR, "data", "test_raw")
        self.local_storage = LocalStorageAdapter(base_dir=self.test_dir)
        self.s3_storage = S3StorageAdapter()
        self.ingestion_client = TelemetryIngestionClient(
            local_storage=self.local_storage,
            s3_storage=self.s3_storage
        )


    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_validator_valid_reading(self):
        reading = {"temperature": 32.0, "humidity": 70.0, "windSpeed": 12.5}
        result = TelemetryValidator.validate_reading(reading)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.quality_flag, "GOOD")

    def test_validator_out_of_bounds_temperature(self):
        reading = {"temperature": 75.0, "humidity": 50.0}
        result = TelemetryValidator.validate_reading(reading)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.quality_flag, "OUT_OF_BOUNDS")

    def test_validator_missing_field(self):
        reading = {"temperature": 30.0}
        result = TelemetryValidator.validate_reading(reading)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.quality_flag, "MISSING_FIELD")

    def test_local_storage_partitioning(self):
        reading = {"station_id": "0", "temperature": 31.5, "humidity": 70.0}
        filepath = self.local_storage.save_reading(
            station_id="0",
            date_str="2026-07-20T03:15:00",
            reading=reading
        )
        self.assertTrue(os.path.exists(filepath))
        self.assertIn("2026-07-20", filepath)

    def test_s3_storage_upload(self):
        readings = [{"temperature": 30.0, "humidity": 65.0}]
        s3_key = self.s3_storage.upload_telemetry_batch(
            station_id="st_0",
            date_str="2026-07-20",
            readings=readings
        )
        self.assertIn("s3://weather-telemetry-raw/raw/2026-07-20/station_st_0.json", s3_key)

    def test_csv_batch_ingestion(self):
        clean_csv = os.path.join(BASE_DIR, "data", "timeseries_15min_clean.csv")
        if os.path.exists(clean_csv):

            res = self.ingestion_client.process_csv_batch(clean_csv, limit=20)
            self.assertEqual(res["total_processed"], 20)
            self.assertEqual(res["valid_count"], 20)
            self.assertGreater(len(res["saved_partitions"]), 0)

if __name__ == "__main__":
    unittest.main()
