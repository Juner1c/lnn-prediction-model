import os
import json
from typing import Dict, Any, List

class LocalStorageAdapter:
    """
    Partitioned local storage adapter for raw telemetry JSON files.
    Partitions files by date: data/raw/YYYY-MM-DD/station_{station_id}.json
    """
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
        self.base_dir = base_dir


    def save_reading(self, station_id: str, date_str: str, reading: Dict[str, Any]) -> str:
        date_partition = date_str.split("T")[0] if "T" in date_str else date_str
        target_dir = os.path.join(self.base_dir, date_partition)
        os.makedirs(target_dir, exist_ok=True)

        target_file = os.path.join(target_dir, f"station_{station_id}.jsonl")
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(reading) + "\n")

        return target_file


class S3StorageAdapter:
    """
    Amazon S3 storage adapter for raw telemetry bucket uploads.
    Bucket: s3://weather-telemetry-raw/
    """
    def __init__(self, bucket_name: str = "weather-telemetry-raw"):
        self.bucket_name = bucket_name
        self.s3_client = None
        try:
            import boto3
            self.s3_client = boto3.client('s3')
        except Exception:
            self.s3_client = None

    def upload_telemetry_batch(self, station_id: str, date_str: str, readings: List[Dict[str, Any]]) -> str:
        date_partition = date_str.split("T")[0] if "T" in date_str else date_str
        s3_key = f"raw/{date_partition}/station_{station_id}.json"
        
        if self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=json.dumps(readings),
                    ContentType="application/json"
                )
            except Exception:
                pass

        return f"s3://{self.bucket_name}/{s3_key}"

