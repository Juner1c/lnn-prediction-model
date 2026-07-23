import os
import sys
import pytest
import torch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.models.stgnn_forecaster import SpatialTemporalGNN
from src.models.checkpoint_manager import save_model_checkpoint, load_model_checkpoint, DEFAULT_CHECKPOINT_PATH
from scripts.schedule_autotuning import execute_retraining_pass, start_scheduled_service

def test_checkpoint_manager_save_and_load(tmp_path):
    checkpoint_file = os.path.join(tmp_path, "test_stgnn.pt")
    model = SpatialTemporalGNN(num_nodes=12, in_channels=5, hidden_dim=16, forecast_horizon=16)
    
    meta = {
        "val_temp_rmse": 3.15,
        "val_hi_rmse": 4.80,
        "val_mae": 2.20,
        "hyperparameters": {"lr": 0.001}
    }
    
    saved_path = save_model_checkpoint(model, filepath=checkpoint_file, metadata=meta)
    assert os.path.exists(saved_path)
    
    # Load into fresh model
    new_model = SpatialTemporalGNN(num_nodes=12, in_channels=5, hidden_dim=16, forecast_horizon=16)
    success, loaded_meta = load_model_checkpoint(new_model, filepath=checkpoint_file)
    
    assert success is True
    assert loaded_meta.get("val_temp_rmse") == 3.15
    assert loaded_meta.get("val_hi_rmse") == 4.80

def test_scheduled_autotuning_run_once():
    # Test run_once execution pass
    start_scheduled_service(interval_hours=1.0, max_iterations=1, finetune_interval=1, run_once=True)
    assert os.path.exists(DEFAULT_CHECKPOINT_PATH)
