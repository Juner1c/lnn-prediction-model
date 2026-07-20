import os
import pandas as pd
from typing import List, Dict, Any
from src.data.validator import TelemetryValidator, TelemetryValidationResult
from src.data.storage_adapter import LocalStorageAdapter, S3StorageAdapter

class TelemetryIngestionClient:
    """
    Ingestion client that processes telemetry from local batch CSVs or API endpoints,
    validates data quality, and persists readings to local & S3 storage adapters.
    """
    def __init__(self, local_storage: LocalStorageAdapter = None, s3_storage: S3StorageAdapter = None):
        self.local_storage = local_storage or LocalStorageAdapter()
        self.s3_storage = s3_storage or S3StorageAdapter()

    def process_csv_batch(self, csv_path: str, limit: int = 50) -> Dict[str, Any]:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Batch CSV file not found: {csv_path}")

        df = pd.read_csv(csv_path)
        # Clean column names
        df.columns = [c.encode('ascii', 'ignore').decode('ascii').strip() for c in df.columns]

        temp_col = [c for c in df.columns if 'temperature_2m' in c][0]
        rh_col = [c for c in df.columns if 'relative_humidity_2m' in c][0]
        dew_col = [c for c in df.columns if 'dew_point_2m' in c][0]
        app_col = [c for c in df.columns if 'apparent_temperature' in c][0]
        wind_col = [c for c in df.columns if 'wind_speed' in c][0]

        valid_count = 0
        rejected_count = 0
        saved_files = []

        sub_df = df.head(limit)
        for _, row in sub_df.iterrows():
            reading = {
                "station_id": str(int(row["location_id"])),
                "time": str(row["time"]),
                "temperature": row[temp_col],
                "humidity": row[rh_col],
                "dewPoint": row[dew_col],
                "apparentTemperature": row[app_col],
                "windSpeed": row[wind_col]
            }

            validation: TelemetryValidationResult = TelemetryValidator.validate_reading(reading)
            if validation.is_valid:
                valid_count += 1
                filepath = self.local_storage.save_reading(
                    station_id=reading["station_id"],
                    date_str=reading["time"],
                    reading=validation.cleaned_data
                )
                if filepath not in saved_files:
                    saved_files.append(filepath)
            else:
                rejected_count += 1

        return {
            "total_processed": len(sub_df),
            "valid_count": valid_count,
            "rejected_count": rejected_count,
            "saved_partitions": saved_files
        }
