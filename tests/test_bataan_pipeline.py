import os
import sys
import pytest
import numpy as np
import torch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data.bataan_dataset import load_and_clean_bataan_telemetry, BataanMultiStationDataset, BATAAN_STATIONS_METADATA
from src.models.spatial_graph import build_spatial_adjacency_matrix
from src.models.stgnn_forecaster import SpatialTemporalGNN
from src.agent.experiment_runner import ExperimentRunner

def test_bataan_dataset_loading_and_cleaning():
    tensor_3d, mask_2d, df_locs = load_and_clean_bataan_telemetry()
    
    assert len(df_locs) == 12
    assert tensor_3d.shape[1] == 12
    assert tensor_3d.shape[2] == 5 # temp, humidity, pressure, wind_speed, heat_index
    assert mask_2d.shape[0] == tensor_3d.shape[0]
    
    # Range check - physical temperatures must be bounded
    temps = tensor_3d[:, :, 0]
    assert np.all(temps >= 5.0) and np.all(temps <= 50.0)

def test_bataan_spatial_adjacency_matrix():
    _, _, df_locs = load_and_clean_bataan_telemetry()
    adj, dist = build_spatial_adjacency_matrix(df_locs, sigma=15.0, max_dist=80.0)
    
    assert adj.shape == (12, 12)
    assert dist.shape == (12, 12)
    # Self-loops must be non-zero
    for i in range(12):
        assert adj[i, i] > 0.0

def test_bataan_outage_dataset_windowing():
    tensor_3d, mask_2d, df_locs = load_and_clean_bataan_telemetry()
    dataset = BataanMultiStationDataset(tensor_3d[:500], mask_2d[:500], seq_len=96, horizon=16, outage_mask_ratio=0.25)
    
    assert len(dataset) > 0
    x, y, mask = dataset[0]
    
    assert x.shape == (12, 96, 5)
    assert y.shape == (12, 16, 5)
    assert mask.shape == (12, 96)

def test_bataan_stgnn_imputation_forward_pass():
    model = SpatialTemporalGNN(num_nodes=12, in_channels=5, hidden_dim=32, forecast_horizon=16)
    adj = torch.eye(12)
    
    x = torch.randn(2, 12, 96, 5)
    mask = torch.ones(2, 12, 96)
    # Mask 3 stations to 0 (simulating down stations)
    x[:, [3, 5, 9], :, :] = 0.0
    mask[:, [3, 5, 9], :] = 0.0
    
    preds = model(x, adj, mask)
    assert preds.shape == (2, 12, 16, 5)
    assert not torch.isnan(preds).any()
