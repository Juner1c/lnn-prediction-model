import os
import sys
import json
import pytest
import tempfile

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.agent.lfm_agent import LFMAgentController
from src.agent.trajectory_memory import TrajectoryMemory
from src.agent.experiment_runner import ExperimentRunner
from scripts.finetune_lfm_agent import finetune_lfm_qlora
from scripts.run_agentic_loop import run_autonomous_loop

def test_lfm_agent_controller_prompt_and_clamping():
    agent = LFMAgentController(load_model=False)
    
    history = [
        {
            "chosen_params": {"lr": 0.001, "batch_size": 16, "epochs": 10},
            "validation_rmse": 1.25,
            "validation_mae": 0.95,
            "improvement_delta": 0.05
        }
    ]
    prompt = agent.build_system_prompt(history)
    assert "LFM2.5-8B" in prompt
    assert "Exp 1:" in prompt

    raw_proposal = {
        "hypothesis": "Test out extreme parameters",
        "parameters": {
            "lr": 0.5, # Out of bounds -> should clamp to 0.01
            "batch_size": 99, # Invalid -> should fallback to 16
            "epochs": 100, # Out of bounds -> should clamp to 30
            "hidden_dim": 64,
            "recon_weight": 0.1
        }
    }
    clamped = agent.validate_and_clamp_params(raw_proposal)
    params = clamped["parameters"]
    assert params["lr"] <= 0.01
    assert params["batch_size"] == 16
    assert params["epochs"] <= 30
    assert params["hidden_dim"] == 64

def test_trajectory_memory_logging():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_json = os.path.join(tmp_dir, "test_trajectories.json")
        memory = TrajectoryMemory(storage_path=tmp_json)

        assert memory.get_best_rmse() is None

        # Run 1
        record1 = memory.record_experiment(
            hypothesis="Baseline test",
            chosen_params={"lr": 0.001, "batch_size": 16},
            train_loss=0.50,
            validation_rmse=1.50,
            validation_mae=1.20,
            prompt="Prompt 1"
        )
        assert record1["status"] == "IMPROVED"
        assert memory.get_best_rmse() == 1.50

        # Run 2 - Better RMSE
        record2 = memory.record_experiment(
            hypothesis="Tuned test",
            chosen_params={"lr": 0.0005, "batch_size": 16},
            train_loss=0.40,
            validation_rmse=1.20,
            validation_mae=0.90,
            prompt="Prompt 2"
        )
        assert record2["status"] == "IMPROVED"
        assert record2["improvement_delta"] == 0.30
        assert memory.get_best_rmse() == 1.20

        # Export QLoRA dataset
        qlora_export_path = os.path.join(tmp_dir, "qlora_dataset.json")
        pairs = memory.export_qlora_dataset(output_path=qlora_export_path)
        assert len(pairs) == 2
        assert os.path.exists(qlora_export_path)

def test_experiment_runner_execution():
    runner = ExperimentRunner()
    params = {"lr": 0.001, "batch_size": 16, "epochs": 1, "hidden_dim": 16, "recon_weight": 0.1}
    train_loss, val_rmse, val_mae = runner.run_experiment(params)

    assert isinstance(train_loss, float)
    assert isinstance(val_rmse, float)
    assert isinstance(val_mae, float)
    assert val_rmse > 0.0
    assert val_mae > 0.0

def test_autonomous_loop_execution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_json = os.path.join(tmp_dir, "trajectories.json")
        # Run 1 iteration of agentic loop
        run_autonomous_loop(max_iterations=1, finetune_interval=1, load_model=False)
