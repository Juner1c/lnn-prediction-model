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

        self.w_f = nn.Linear(input_size + hidden_size, hidden_size)
        self.w_g = nn.Linear(input_size + hidden_size, hidden_size)
        self.w_h = nn.Linear(input_size + hidden_size, hidden_size)

    def forward(self, input_tensor: torch.Tensor, hx: torch.Tensor) -> torch.Tensor:
        combined = torch.cat((input_tensor, hx), dim=-1)
        f = torch.sigmoid(-self.w_f(combined))
        g = torch.tanh(self.w_g(combined))
        h = torch.tanh(self.w_h(combined))

        new_h = f * g + (1.0 - f) * h
        return new_h

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
            batch_size, seq_len, _ = x.size()
            hx = torch.zeros(batch_size, self.hidden_size, device=x.device)
            outputs = []
            for t in range(seq_len):
                hx = self.cell(x[:, t, :], hx)
                outputs.append(self.head(hx).unsqueeze(1))
            filtered = torch.cat(outputs, dim=1)

        return filtered
