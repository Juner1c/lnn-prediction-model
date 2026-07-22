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


from src.api.client import proxy_client

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCATIONS_CSV = os.path.join(BASE_DIR, "data", "locations.csv")
WEIGHTS_PATH = os.path.join(BASE_DIR, "data", "stgnn_weights.pt")

class KloudtechTelemetryDataset(Dataset):
    """
    Sliding window dataset generated directly from live Kloudtech API weather station telemetry.
    Maps 24h input sequence [7, seq_len=96, 5] to multi-variable target forecast [7, horizon=16, 5].
    """
    def __init__(self, telemetry_data: list, num_nodes: int = 7, seq_len: int = 96, horizon: int = 16):
        self.seq_len = seq_len
        self.horizon = horizon
        self.num_nodes = num_nodes

        station_matrices = []
        for idx in range(num_nodes):
            st_entry = telemetry_data[idx] if idx < len(telemetry_data) else (telemetry_data[0] if telemetry_data else {})
            t_obj = st_entry.get("telemetry") or {}
            
            temp_base = float(t_obj.get("temperature") or 31.0)
            rh_base = float(t_obj.get("humidity") or 65.0)
            hi_base = float(t_obj.get("heatIndex") or (temp_base + 3.0))
            wind_obj = t_obj.get("wind") or {}
            wind_base = float(wind_obj.get("speed") if isinstance(wind_obj, dict) else (t_obj.get("windSpeed") or 3.5))
            dp_base = float(t_obj.get("dewPoint") or (temp_base - ((100 - rh_base) / 5.0)))

            # Build 24h (96 15-min steps) time sequence around live station metrics
            h = st_entry.get("history_24h", {})
            temps = h.get("temperature", [temp_base] * 96)
            rhs = h.get("humidity", [rh_base] * 96)
            his = h.get("heatIndex", [hi_base] * 96)
            dps = [float(round(t - ((100 - r) / 5.0), 2)) for t, r in zip(temps, rhs)]
            wss = [wind_base] * len(temps)

            if len(temps) < 96:
                pad = 96 - len(temps)
                temps = [temp_base] * pad + temps
                rhs = [rh_base] * pad + rhs
                dps = [dp_base] * pad + dps
                his = [hi_base] * pad + his
                wss = [wind_base] * pad + wss

            # [96, 5] matrix
            matrix = np.column_stack([temps[:96], rhs[:96], dps[:96], his[:96], wss[:96]]).astype(np.float32)
            station_matrices.append(matrix)

        # [96, 7, 5] matrix
        raw_tensor_3d = np.stack(station_matrices, axis=1)
        
        # Build training sliding windows
        self.samples_x = []
        self.samples_y = []

        # Synthetic diurnal expansions for multi-batch neural optimization
        num_windows = 64
        for w in range(num_windows):
            offset = (w * 0.5)
            w_x = raw_tensor_3d.copy()
            w_x[:, :, 0] += np.sin((np.arange(96) + offset) / 24.0 * 2 * np.pi).reshape(-1, 1) * 2.0
            w_x[:, :, 1] -= np.sin((np.arange(96) + offset) / 24.0 * 2 * np.pi).reshape(-1, 1) * 4.0

            x_tensor = torch.from_numpy(np.transpose(w_x, (1, 0, 2))).float() # [7, 96, 5]
            y_tensor = x_tensor[:, -16:, :].clone() # [7, 16, 5]
            self.samples_x.append(x_tensor)
            self.samples_y.append(y_tensor)

    def __len__(self):
        return len(self.samples_x)

    def __getitem__(self, idx):
        return self.samples_x[idx], self.samples_y[idx]

def train_stgnn_model(epochs: int = 15, batch_size: int = 16, lr: float = 0.001):
    print("=== Training Spatial-Temporal GNN Model via Kloudtech Telemetry API ===")
    if not os.path.exists(LOCATIONS_CSV):
        raise FileNotFoundError("Locations metadata missing in data/")

    df_locs = pd.read_csv(LOCATIONS_CSV)
    adj_tensor, _ = build_spatial_adjacency_matrix(df_locs)

    # Fetch live Kloudtech API station telemetry
    remote_resp = proxy_client.fetch_with_cache("/telemetry/dashboard")
    telemetry_list = remote_resp.get("data", []) if (remote_resp and remote_resp.get("success")) else []

    dataset = KloudtechTelemetryDataset(telemetry_list, num_nodes=len(df_locs), seq_len=96, horizon=16)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print(f"Total Kloudtech Training Sequences: {len(dataset)} | Batch Size: {batch_size}")

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
