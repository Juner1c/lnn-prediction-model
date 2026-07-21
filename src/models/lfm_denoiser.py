import torch
import torch.nn as nn
from typing import Tuple

try:
    from ncps.torch import CfC
    HAS_NCPS = True
except ImportError:
    HAS_NCPS = False

class LiquidTimeConstantCell(nn.Module):
    """
    Fallback PyTorch implementation of Closed-form Continuous-time (CfC) Liquid Cell
    when ncps package is not installed.
    Computes analytical state transition: x(t) = sigmoid(-f(x, I)) * g(x, I) + (1 - sigmoid(-f(x, I))) * h(x, I)
    """
    def __init__(self, input_size: int, hidden_size: int):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        self.w_in = nn.Linear(input_size, 3 * hidden_size)
        self.w_h = nn.Linear(hidden_size, 3 * hidden_size, bias=False)

    def forward(self, input_tensor: torch.Tensor, hx: torch.Tensor) -> torch.Tensor:
        in_proj = self.w_in(input_tensor) # [batch, 3 * hidden]
        h_proj = self.w_h(hx) # [batch, 3 * hidden]
        proj = in_proj + h_proj

        f_gate, g_gate, h_gate = torch.chunk(proj, 3, dim=-1)
        f = torch.sigmoid(-f_gate)
        g = torch.tanh(g_gate)
        h = torch.tanh(h_gate)

        new_h = f * g + (1.0 - f) * h
        return new_h

    def forward_sequence(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.size()
        in_proj = self.w_in(x) # Single batched matrix multiplication: [batch, seq_len, 3 * hidden]
        hx = torch.zeros(batch_size, self.hidden_size, device=x.device)
        hidden_states = []

        for t in range(seq_len):
            in_t = in_proj[:, t, :]
            h_proj = self.w_h(hx)
            proj = in_t + h_proj
            f_gate, g_gate, h_gate = torch.chunk(proj, 3, dim=-1)
            f = torch.sigmoid(-f_gate)
            g = torch.tanh(g_gate)
            h = torch.tanh(h_gate)
            hx = f * g + (1.0 - f) * h
            hidden_states.append(hx.unsqueeze(1))

        return torch.cat(hidden_states, dim=1)


class LiquidDenoisingService(nn.Module):
    """
    Liquid Neural Network Denoising Service.
    Applies continuous-time filtering over 15-minute weather telemetry sequences to produce
    cleaned latent state representations for spatial GNN forecasting.
    """
    def __init__(self, input_size: int = 5, hidden_size: int = 32, output_size: int = 5):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        if HAS_NCPS:
            self.cfc = CfC(input_size, hidden_size, return_sequences=True)
            self.head = nn.Linear(hidden_size, output_size)
        else:
            self.cell = LiquidTimeConstantCell(input_size, hidden_size)
            self.head = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x shape: [batch_size, seq_len, input_size]
        Returns: [batch_size, seq_len, output_size]
        """
        if HAS_NCPS:
            out, _ = self.cfc(x)
            filtered = self.head(out)
        else:
            full_hidden = self.cell.forward_sequence(x) # [batch, seq_len, hidden_size]
            filtered = self.head(full_hidden) # [batch, seq_len, output_size]

        return filtered

    def get_latent_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract latent continuous-time hidden state trajectories from Liquid Neural Network.
        x shape: [batch_size, seq_len, input_size]
        Returns: [batch_size, hidden_size] (latest hidden state)
        """
        if HAS_NCPS:
            out, _ = self.cfc(x) # [batch_size, seq_len, hidden_size]
            return out[:, -1, :]
        else:
            full_hidden = self.cell.forward_sequence(x)
            return full_hidden[:, -1, :]


    def detect_spatial_anomalies(self, station_tensors: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Computes continuous-time spatial anomaly z-scores across all stations based on LNN latent representations.
        station_tensors shape: [num_nodes, seq_len, input_size]
        Returns: (anomaly_scores [num_nodes], feature_contributions [num_nodes, input_size])
        """
        num_nodes, seq_len, num_features = station_tensors.size()
        latent_h = self.get_latent_features(station_tensors) # [num_nodes, hidden_size]

        # Spatial mean and std across station latent vectors
        h_mean = latent_h.mean(dim=0, keepdim=True)
        h_std = latent_h.std(dim=0, keepdim=True) + 1e-6
        latent_z = (latent_h - h_mean) / h_std
        anomaly_scores = torch.norm(latent_z, dim=1) # [num_nodes]

        # Feature contribution via input variance relative to regional mean
        feat_latest = station_tensors[:, -1, :] # [num_nodes, input_size]
        feat_mean = feat_latest.mean(dim=0, keepdim=True)
        feat_std = feat_latest.std(dim=0, keepdim=True) + 1e-6
        feature_contributions = torch.abs(feat_latest - feat_mean) / feat_std

        return anomaly_scores, feature_contributions

