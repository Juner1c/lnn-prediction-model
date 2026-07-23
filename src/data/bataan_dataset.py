import os
import glob
from typing import Tuple, Dict, List, Optional
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
import logging

logger = logging.getLogger("BataanDataset")
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

BATAAN_STATIONS_METADATA = [
    {"id": "st_01", "name": "1Bataan Command Center", "lat": 14.678, "lon": 120.542},
    {"id": "st_02", "name": "BPSU - Bagac Campus", "lat": 14.603, "lon": 120.392},
    {"id": "st_03", "name": "BPSU Dinalupihan Campus", "lat": 14.867, "lon": 120.463},
    {"id": "st_04", "name": "Hermosa Municipal Hall", "lat": 14.832, "lon": 120.505},
    {"id": "st_05", "name": "Kanawan Integrated School", "lat": 14.685, "lon": 120.312},
    {"id": "st_06", "name": "Limay Physical Therapy Center", "lat": 14.561, "lon": 120.598},
    {"id": "st_07", "name": "Mariveles Municipal Hall", "lat": 14.434, "lon": 120.485},
    {"id": "st_08", "name": "Old Cabcaben Pier", "lat": 14.448, "lon": 120.589},
    {"id": "st_09", "name": "Pag-asa Elementary School", "lat": 14.802, "lon": 120.537},
    {"id": "st_10", "name": "Quinawan Integrated School", "lat": 14.538, "lon": 120.362},
    {"id": "st_11", "name": "Sabang Fish Landing", "lat": 14.681, "lon": 120.278},
    {"id": "st_12", "name": "Tanato Elementary School", "lat": 14.662, "lon": 120.489}
]

def load_and_clean_bataan_telemetry() -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Loads, cleans, and aligns 1.6+ years (2025-2026) worth of multi-variable weather data for 12 Bataan stations.
    Returns:
      tensor_4d: [total_steps, 12_nodes, 5_features] (temp, humidity, pressure, wind_speed, heat_index)
      mask_2d: [total_steps, 12_nodes] (1 for live sensor, 0 for down station / major gap)
      df_stations: metadata DataFrame
    """
    full_timeline = pd.date_range(start="2024-12-31 16:00:00", end="2026-07-23 09:00:00", freq="1h")
    total_steps = len(full_timeline)
    num_nodes = len(BATAAN_STATIONS_METADATA)

    # 3D Tensor: [total_steps, 12_nodes, 5_features]
    tensor_3d = np.zeros((total_steps, num_nodes, 5), dtype=np.float32)
    mask_2d = np.ones((total_steps, num_nodes), dtype=np.float32)

    for idx, st_meta in enumerate(BATAAN_STATIONS_METADATA):
        st_name = st_meta["name"]
        matches = glob.glob(os.path.join(DATA_DIR, f"{st_name}*.csv"))
        if not matches:
            logger.warning(f"No CSV file found for station '{st_name}'. Marking node as down.")
            mask_2d[:, idx] = 0.0
            continue

        dfs = [pd.read_csv(m) for m in matches]
        df = pd.concat(dfs, ignore_index=True)
        df["dt"] = pd.to_datetime(df["recordedAt"], format="mixed", errors="coerce")
        df = df.dropna(subset=["dt"]).sort_values("dt").drop_duplicates("dt")

        # Physical range validation - replace unphysical misreadings with NaN
        df.loc[(df["temperature"] <= 5.0) | (df["temperature"] >= 50.0), "temperature"] = np.nan
        df.loc[(df["humidity"] <= 5.0) | (df["humidity"] > 100.0), "humidity"] = np.nan
        if "airPressure" in df.columns:
            df.loc[(df["airPressure"] < 800.0) | (df["airPressure"] > 1150.0), "airPressure"] = np.nan
        else:
            df["airPressure"] = np.nan

        if "windSpeed" in df.columns:
            df.loc[df["windSpeed"] < 0.0, "windSpeed"] = 0.0
        else:
            df["windSpeed"] = np.nan

        if "heatIndex" in df.columns:
            df.loc[(df["heatIndex"] <= 5.0) | (df["heatIndex"] >= 75.0), "heatIndex"] = np.nan
        else:
            df["heatIndex"] = np.nan

        # Reindex to master annual hourly timeline
        df = df.set_index("dt").reindex(full_timeline)

        # Track down station periods (where temperature is missing)
        node_missing_mask = df["temperature"].isna()
        mask_2d[:, idx] = (~node_missing_mask).astype(np.float32)

        # Select numeric feature columns and interpolate short gaps
        num_cols = ["temperature", "humidity", "airPressure", "windSpeed", "heatIndex"]
        for c in num_cols:
            if c not in df.columns:
                df[c] = np.nan
            else:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        df_num = df[num_cols].interpolate(method="time", limit=6)

        node_matrix = np.column_stack([
            df_num["temperature"].values,
            df_num["humidity"].values,
            df_num["airPressure"].values,
            df_num["windSpeed"].values,
            df_num["heatIndex"].values
        ])
        tensor_3d[:, idx, :] = node_matrix.astype(np.float32)

    # Perform spatial node mean across active neighbors to impute multi-month offline gaps
    active_spatial_mean = np.nanmean(tensor_3d, axis=1, keepdims=True) # [total_steps, 1, 5]
    spatial_filled_tensor = np.where(np.isnan(tensor_3d), active_spatial_mean, tensor_3d)

    # Final baseline fallback for remaining NaNs
    fallback_defaults = np.array([28.5, 72.0, 1008.0, 3.5, 31.5], dtype=np.float32)
    for c_idx in range(5):
        spatial_filled_tensor[:, :, c_idx] = np.nan_to_num(spatial_filled_tensor[:, :, c_idx], nan=fallback_defaults[c_idx])

    tensor_3d = spatial_filled_tensor

    df_locs = pd.DataFrame(BATAAN_STATIONS_METADATA)
    logger.info(f"Loaded Bataan 12-Station Dataset | Timesteps: {total_steps} | Active Ratio: {np.mean(mask_2d)*100:.2f}%")
    return tensor_3d, mask_2d, df_locs

class BataanMultiStationDataset(Dataset):
    """
    Sliding window dataset over Bataan 12 weather stations with artificial node outage masking.
    Maps input sequences [seq_len=96, 12, 5] to multi-variable target forecast [horizon=16, 12, 5].
    """
    def __init__(
        self,
        tensor_3d: np.ndarray,
        mask_2d: np.ndarray,
        seq_len: int = 96,
        horizon: int = 16,
        outage_mask_ratio: float = 0.15
    ):
        self.seq_len = seq_len
        self.horizon = horizon
        self.outage_mask_ratio = outage_mask_ratio
        
        self.samples_x = []
        self.samples_y = []
        self.samples_mask = []

        total_steps, num_nodes, num_features = tensor_3d.shape

        # Build sliding windows
        stride = 24
        for start_idx in range(0, total_steps - seq_len - horizon + 1, stride):
            x_window = tensor_3d[start_idx : start_idx + seq_len].copy() # [96, 12, 5]
            y_window = tensor_3d[start_idx + seq_len : start_idx + seq_len + horizon].copy() # [16, 12, 5]
            m_window = mask_2d[start_idx : start_idx + seq_len].copy() # [96, 12]

            # Reorder to [12, 96, 5] for PyTorch STGNN node format
            x_tensor = torch.from_numpy(np.transpose(x_window, (1, 0, 2))).float()
            y_tensor = torch.from_numpy(np.transpose(y_window, (1, 0, 2))).float()
            m_tensor = torch.from_numpy(m_window.T).float() # [12, 96]

            self.samples_x.append(x_tensor)
            self.samples_y.append(y_tensor)
            self.samples_mask.append(m_tensor)

    def __len__(self):
        return len(self.samples_x)

    def __getitem__(self, idx):
        x = self.samples_x[idx].clone()
        y = self.samples_y[idx]
        mask = self.samples_mask[idx].clone()

        # Simulate artificial station dropouts during training if requested
        if self.outage_mask_ratio > 0.0:
            num_nodes = x.size(0)
            num_drop = int(num_nodes * self.outage_mask_ratio)
            if num_drop > 0:
                drop_nodes = np.random.choice(num_nodes, size=num_drop, replace=False)
                for node_idx in drop_nodes:
                    x[node_idx, :, :] = 0.0 # Zero out features for down station
                    mask[node_idx, :] = 0.0 # Set mask to 0 for down station

        return x, y, mask
