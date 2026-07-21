import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from src.models.spatial_graph import build_spatial_adjacency_matrix
from src.models.stgnn_forecaster import SpatialTemporalGNN
from src.data.heat_index import calculate_heat_index_batch


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATASET_CSV = os.path.join(BASE_DIR, "data", "timeseries_15min_clean.csv")
LOCATIONS_CSV = os.path.join(BASE_DIR, "data", "locations.csv")
WEIGHTS_PATH = os.path.join(BASE_DIR, "data", "stgnn_weights.pt")

class WeatherTimeSeriesDataset(Dataset):
    """
    Sliding window time-series dataset for 7 Central Luzon weather stations.
    Maps input sequence [7, seq_len=96, 5] to target Heat Index forecast [7, horizon=16].
    """
    def __init__(self, df: pd.DataFrame, num_nodes: int = 7, seq_len: int = 96, horizon: int = 16):
        self.seq_len = seq_len
        self.horizon = horizon
        self.num_nodes = num_nodes

        # Clean column names
        df = df.copy()
        df.columns = [c.encode('ascii', 'ignore').decode('ascii').strip() for c in df.columns]

        temp_col = [c for c in df.columns if 'temperature_2m' in c][0]
        rh_col = [c for c in df.columns if 'relative_humidity_2m' in c][0]
        dew_col = [c for c in df.columns if 'dew_point_2m' in c][0]
        app_col = [c for c in df.columns if 'apparent_temperature' in c][0]
        wind_col = [c for c in df.columns if 'wind_speed' in c][0]

        # Pivot to 3D matrix: [time_steps, num_nodes, 5_features]
        pivot_data = []
        for loc_id in range(num_nodes):
            loc_df = df[df["location_id"] == loc_id].sort_values("time")
            feats = loc_df[[temp_col, rh_col, dew_col, app_col, wind_col]].values.astype(np.float32)
            pivot_data.append(feats)

        # Truncate to min shared length across stations
        min_len = min(len(p) for p in pivot_data)
        station_matrices = [p[:min_len] for p in pivot_data]
        self.data = np.stack(station_matrices, axis=1) # [min_len, 7, 5]

        self.num_samples = min_len - (seq_len + horizon) + 1

    def __len__(self):
        return max(0, self.num_samples)

    def __getitem__(self, idx):
        # x: [7, 96, 5]
        x_seq = self.data[idx : idx + self.seq_len] # [96, 7, 5]
        x_tensor = torch.from_numpy(np.transpose(x_seq, (1, 0, 2))).float()

        # y: [7, 16, 5] - full 5-channel physical target tensor
        y_seq = self.data[idx + self.seq_len : idx + self.seq_len + self.horizon] # [16, 7, 5]
        y_tensor = torch.from_numpy(np.transpose(y_seq, (1, 0, 2))).float()

        return x_tensor, y_tensor

def train_stgnn_model(epochs: int = 10, batch_size: int = 32, lr: float = 0.001):
    print("=== Training Spatial-Temporal GNN Heat Index Forecasting Model ===")
    if not os.path.exists(DATASET_CSV) or not os.path.exists(LOCATIONS_CSV):
        raise FileNotFoundError("Cleaned timeseries CSV or locations metadata missing in data/")

    df_locs = pd.read_csv(LOCATIONS_CSV)
    adj_tensor, _ = build_spatial_adjacency_matrix(df_locs)

    df_ts = pd.read_csv(DATASET_CSV)
    dataset = WeatherTimeSeriesDataset(df_ts, num_nodes=len(df_locs), seq_len=96, horizon=16)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print(f"Total Training Sequences: {len(dataset)} | Batch Size: {batch_size}")

    model = SpatialTemporalGNN(num_nodes=len(df_locs), in_channels=5, hidden_dim=32, forecast_horizon=16)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        for x_b, y_b in dataloader:
            optimizer.zero_grad()
            
            # Inject Gaussian noise into input sequence for explicit LNN denoising autoencoder training
            noisy_x = x_b + torch.randn_like(x_b) * 0.05
            batch_size, num_nodes, seq_len, in_channels = noisy_x.size()
            
            # Compute denoised features and forecast predictions
            x_flat = noisy_x.view(batch_size * num_nodes, seq_len, in_channels)
            denoised_flat = model.lfm_denoiser(x_flat)
            denoised_x = denoised_flat.view(batch_size, num_nodes, seq_len, in_channels)
            
            preds = model(noisy_x, adj_tensor) # [batch, 7, 16]
            
            # Multi-task Loss: Forecast MSE + 0.1 * Denoising Reconstruction MSE
            loss_forecast = criterion(preds, y_b)
            loss_recon = criterion(denoised_x, x_b)
            loss = loss_forecast + 0.1 * loss_recon
            
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(x_b)

        epoch_loss = total_loss / len(dataset)
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Multi-Task Loss: {epoch_loss:.4f} | RMSE: {np.sqrt(epoch_loss):.4f} °C")


    # Save model weights
    os.makedirs(os.path.dirname(WEIGHTS_PATH), exist_ok=True)
    torch.save(model.state_dict(), WEIGHTS_PATH)
    print(f"[SUCCESS] Trained model weights saved to {WEIGHTS_PATH}")

if __name__ == "__main__":
    train_stgnn_model()
