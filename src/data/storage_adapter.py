import os
import json
from typing import Dict, Any, List

class LocalStorageAdapter:
    """
    Partitioned local storage adapter for raw telemetry JSON files.
    Partitions files by date: data/raw/YYYY-MM-DD/station_{station_id}.json
    """
    def __init__(self, base_dir: str = r"c:\Users\Jhonric Gorillo\Desktop\JHONRIC_FILES\OJT\LNN-Prediction-Model-Project\data\raw"):
        self.base_dir = base_dir

    def save_reading(self, station_id: str, date_str: str, reading: Dict[str, Any]) -> str:
        date_partition = date_str.split("T")[0] if "T" in date_str else date_str
        target_dir = os.path.join(self.base_dir, date_partition)
        os.makedirs(target_dir, exist_ok=True)

        target_file = os.path.join(target_dir, f"station_{station_id}.json")

        existing = []
        if os.path.exists(target_file):
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing.append(reading)

        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2)

        return target_file

class S3StorageAdapter:
    """
    Simulated / Amazon S3 storage adapter for raw telemetry bucket uploads.
    Bucket: s3://weather-telemetry-raw/
    """
    def __init__(self, bucket_name: str = "weather-telemetry-raw"):
        self.bucket_name = bucket_name

    def upload_telemetry_batch(self, station_id: str, date_str: str, readings: List[Dict[str, Any]]) -> str:
        date_partition = date_str.split("T")[0] if "T" in date_str else date_str
        s3_key = f"s3://{self.bucket_name}/raw/{date_partition}/station_{station_id}.json"
        # In production, boto3.client('s3').put_object(...) is called here
        return s3_key
