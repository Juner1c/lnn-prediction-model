import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from src.models.spatial_graph import build_spatial_adjacency_matrix
from src.models.stgnn_forecaster import SpatialTemporalGNN
from src.data.bataan_dataset import load_and_clean_bataan_telemetry, BataanMultiStationDataset

logger = logging.getLogger("ExperimentRunner")
logging.basicConfig(level=logging.INFO)

class ExperimentRunner:
    """
    Executes multi-variable time-series model training over 12 Bataan weather stations
    under candidate hyperparameter configurations, measuring multi-variable RMSE and station outage recovery.
    """
    def __init__(self):
        self.tensor_3d, self.mask_2d, self.df_locs = load_and_clean_bataan_telemetry()
        self.adj_tensor, _ = build_spatial_adjacency_matrix(self.df_locs, sigma=15.0, max_dist=80.0)

    def run_experiment(self, parameters: Dict[str, Any]) -> Tuple[float, float, float]:
        """
        Runs model training for proposed parameters on Bataan 12-station data.
        Returns: (train_loss, val_rmse, val_mae)
        """
        lr = float(parameters.get("lr", 0.001))
        batch_size = int(parameters.get("batch_size", 16))
        epochs = int(parameters.get("epochs", 8))
        hidden_dim = int(parameters.get("hidden_dim", 64))
        recon_weight = float(parameters.get("recon_weight", 0.1))
        outage_mask_ratio = float(parameters.get("outage_mask_ratio", 0.15))

        logger.info(f"Running Bataan 12-Station Experiment: lr={lr}, batch={batch_size}, epochs={epochs}, hidden={hidden_dim}, recon={recon_weight}, outage_mask={outage_mask_ratio}")

        dataset = BataanMultiStationDataset(
            self.tensor_3d,
            self.mask_2d,
            seq_len=96,
            horizon=16,
            outage_mask_ratio=outage_mask_ratio
        )
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model = SpatialTemporalGNN(num_nodes=12, in_channels=5, hidden_dim=hidden_dim, forecast_horizon=16)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        model.train()
        total_loss = 0.0
        for epoch in range(1, epochs + 1):
            epoch_loss = 0.0
            for x_b, y_b, m_b in dataloader:
                optimizer.zero_grad()
                
                # Add Gaussian noise for LNN continuous-time ODE denoising
                noisy_x = x_b + torch.randn_like(x_b) * 0.05
                b_sz, n_nodes, s_len, in_c = noisy_x.size()
                
                x_flat = noisy_x.view(b_sz * n_nodes, s_len, in_c)
                denoised_flat = model.lfm_denoiser(x_flat)
                denoised_x = denoised_flat.view(b_sz, n_nodes, s_len, in_c)
                
                # Forward pass with spatial adjacency matrix
                preds = model(noisy_x, self.adj_tensor, m_b)
                
                loss_forecast = criterion(preds, y_b)
                loss_recon = criterion(denoised_x, x_b)
                loss = loss_forecast + recon_weight * loss_recon
                
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * len(x_b)

            total_loss = epoch_loss / len(dataset)

        # Validation evaluation under 20% station outage scenario
        val_dataset = BataanMultiStationDataset(self.tensor_3d, self.mask_2d, seq_len=96, horizon=16, outage_mask_ratio=0.20)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        model.eval()
        val_temp_mses = []
        val_hi_mses = []
        val_maes = []
        with torch.no_grad():
            for x_b, y_b, m_b in val_loader:
                preds = model(x_b, self.adj_tensor, m_b)
                
                # Temperature channel (index 0) & Heat Index channel (index 4)
                temp_mse = criterion(preds[:, :, :, 0], y_b[:, :, :, 0]).item()
                hi_mse = criterion(preds[:, :, :, 4], y_b[:, :, :, 4]).item()
                mae = torch.mean(torch.abs(preds[:, :, :, 0] - y_b[:, :, :, 0])).item()
                
                val_temp_mses.append(temp_mse)
                val_hi_mses.append(hi_mse)
                val_maes.append(mae)

        val_rmse = float(np.sqrt(np.mean(val_temp_mses))) if val_temp_mses else total_loss
        val_hi_rmse = float(np.sqrt(np.mean(val_hi_mses))) if val_hi_mses else val_rmse
        val_mae = float(np.mean(val_maes)) if val_maes else float(val_rmse * 0.7)

        logger.info(f"Bataan Experiment Completed | Train Loss: {total_loss:.4f} | Temp Val RMSE: {val_rmse:.4f} °C | Heat Index Val RMSE: {val_hi_rmse:.4f} °C | Val MAE: {val_mae:.4f} °C")

        # Save model checkpoint
        from src.models.checkpoint_manager import save_model_checkpoint
        save_model_checkpoint(
            model,
            metadata={
                "val_temp_rmse": val_rmse,
                "val_hi_rmse": val_hi_rmse,
                "val_mae": val_mae,
                "train_loss": total_loss,
                "hyperparameters": parameters,
                "num_nodes": 12
            }
        )

        return total_loss, val_rmse, val_mae
