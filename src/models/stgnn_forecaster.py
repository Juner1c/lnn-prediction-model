import torch
import torch.nn as nn
from typing import Optional
from src.models.lfm_denoiser import LiquidDenoisingService

class SpatialGraphConv(nn.Module):
    """
    Spatial Graph Convolution layer.
    Computes H^(l+1) = ReLU(A * H^(l) * W)
    Where A is the normalized spatial adjacency matrix [num_nodes, num_nodes].
    """
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Linear(in_features, out_features)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x shape: [batch_size, num_nodes, in_features] or [batch_size, num_nodes, seq_len, in_features]
        adj shape: [num_nodes, num_nodes]
        Returns: [batch_size, num_nodes, out_features] or [batch_size, num_nodes, seq_len, out_features]
        """
        if x.dim() == 4:
            # Aggregate spatial neighbors across all time steps simultaneously: A * x
            spatial_agg = torch.einsum("ij,bitf->bjtf", adj, x)
        else:
            spatial_agg = torch.einsum("ij,bjk->bik", adj, x)
        out = self.weight(spatial_agg)
        return self.relu(out)

class SpatialTemporalGNN(nn.Module):
    """
    Spatial-Temporal Graph Neural Network (STGNN) Forecasting Model.
    Ingests 7 weather stations' multi-channel 15-minute time-series [batch, 7, seq_len=96, in_channels=5],
    denoises each station via continuous-time LNN, applies Spatial Graph Convolutions across station neighbors,
    and forecasts future Heat Index trajectory [batch, 7, horizon=16].
    """
    def __init__(self, num_nodes: int = 7, in_channels: int = 5, hidden_dim: int = 32, forecast_horizon: int = 16):
        super().__init__()
        self.num_nodes = num_nodes
        self.in_channels = in_channels
        self.hidden_dim = hidden_dim
        self.forecast_horizon = forecast_horizon

        # 1. Temporal LNN Denoising Module
        self.lfm_denoiser = LiquidDenoisingService(input_size=in_channels, hidden_size=hidden_dim, output_size=in_channels)

        # 2. Spatial Graph Convolutional Layers
        self.gcn1 = SpatialGraphConv(in_channels, hidden_dim)
        self.gcn2 = SpatialGraphConv(hidden_dim, hidden_dim)

        # 3. Multi-Variable Temporal Output Head (5 weather channels: temp, rh, dew_point, heat_index, wind_speed)
        self.forecast_head = nn.Sequential(
            nn.Linear(hidden_dim * 96, 128),
            nn.ReLU(),
            nn.Linear(128, forecast_horizon * in_channels)
        )

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x shape: [batch_size, num_nodes=7, seq_len=96, in_channels=5]
        adj shape: [7, 7]
        Returns: [batch_size, num_nodes=7, forecast_horizon=16, in_channels=5] or [batch_size, num_nodes=7, forecast_horizon=16] if single metric.
        """
        batch_size, num_nodes, seq_len, in_channels = x.size()

        # Step 1: Reshape for parallel station LNN denoising: [batch * num_nodes, seq_len, in_channels]
        x_flat = x.view(batch_size * num_nodes, seq_len, in_channels)
        denoised_flat = self.lfm_denoiser(x_flat)  # [batch * num_nodes, seq_len, in_channels]

        # Step 2: Parallelized Spatial Graph Convolutions across spatial & temporal dimensions
        denoised = denoised_flat.view(batch_size, num_nodes, seq_len, in_channels)
        h1 = self.gcn1(denoised, adj)    # [batch, 7, 96, 32]
        st_features = self.gcn2(h1, adj) # [batch, 7, 96, 32]

        # Step 3: Multi-Variable Forecast Head per station node
        st_flat = st_features.view(batch_size * num_nodes, seq_len * self.hidden_dim) # [batch * 7, 96 * 32]
        forecasts_flat = self.forecast_head(st_flat) # [batch * 7, forecast_horizon * in_channels]

        forecasts_5d = forecasts_flat.view(batch_size, num_nodes, self.forecast_horizon, self.in_channels)
        return forecasts_5d

    def predict_autoregressive_rollout(self, x: torch.Tensor, adj: torch.Tensor, steps: int = 384) -> torch.Tensor:
        """
        Multi-step autoregressive rolling forecast using STGNN spatial-temporal multi-variable neural predictions.
        x shape: [batch_size=1, num_nodes=7, seq_len=96, in_channels=5]
        Returns: [batch_size=1, num_nodes=7, steps=384] (Heat Index forecasts)
        """
        curr_x = x.clone()
        hi_rollout_predictions = []

        iterations = (steps + self.forecast_horizon - 1) // self.forecast_horizon
        for _ in range(iterations):
            preds_5d = self.forward(curr_x, adj) # [1, 7, 16, 5]
            hi_preds = preds_5d[:, :, :, 3] # Extract predicted Heat Index channel (index 3)
            hi_rollout_predictions.append(hi_preds)

            # Update input sequence sliding window directly with neural multi-variable prediction tensor [1, 7, 16, 5]
            curr_x = torch.cat([curr_x[:, :, 16:, :], preds_5d], dim=2) # Maintain 96 window

        full_rollout = torch.cat(hi_rollout_predictions, dim=2)[:, :, :steps] # [1, 7, steps]
        return full_rollout


