import os
import sys
import json
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("TrajectoryMemory")
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_STORAGE_PATH = os.path.join(BASE_DIR, "data", "experiment_trajectories.json")

class TrajectoryMemory:
    """
    Manages persistent experiment trajectory history and prepares training datasets for periodic QLoRA fine-tuning.
    """
    def __init__(self, storage_path: str = DEFAULT_STORAGE_PATH):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.trajectories: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                logger.warning(f"Error reading trajectory history from {self.storage_path}: {str(e)}")
        return []

    def save_history(self, max_entries: int = 100):
        try:
            if len(self.trajectories) > max_entries:
                # Keep top entries sorted by best validation_rmse
                self.trajectories = sorted(
                    self.trajectories,
                    key=lambda t: t.get("validation_rmse", float("inf"))
                )[:max_entries]

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.trajectories, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save trajectory history to {self.storage_path}: {str(e)}")

    def get_best_rmse(self) -> Optional[float]:
        """
        Returns the lowest validation RMSE recorded across all completed trajectories.
        """
        val_rmses = [t.get("validation_rmse") for t in self.trajectories if t.get("validation_rmse") is not None]
        return min(val_rmses) if val_rmses else None

    def record_experiment(
        self,
        hypothesis: str,
        chosen_params: Dict[str, Any],
        train_loss: float,
        validation_rmse: float,
        validation_mae: float,
        prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Logs a completed experiment run, computes metric improvement delta relative to best past run, and persists log.
        """
        prev_best = self.get_best_rmse()
        improvement_delta = 0.0
        if prev_best is not None:
            improvement_delta = prev_best - validation_rmse # Positive means RMSE decreased (improved)
        else:
            improvement_delta = 0.0 # Initial baseline run

        status = "IMPROVED" if (prev_best is None or validation_rmse < prev_best) else "SUBOPTIMAL"

        exp_id = f"exp_{len(self.trajectories) + 1:04d}_{int(time.time())}"
        record = {
            "experiment_id": exp_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "prompt": prompt,
            "hypothesis": hypothesis,
            "chosen_params": chosen_params,
            "train_loss": round(float(train_loss), 4),
            "validation_rmse": round(float(validation_rmse), 4),
            "validation_mae": round(float(validation_mae), 4),
            "improvement_delta": round(float(improvement_delta), 4),
            "status": status
        }

        self.trajectories.append(record)
        self.save_history()
        logger.info(f"Recorded Experiment '{exp_id}' | Val RMSE: {validation_rmse:.4f} °C | Status: {status}")
        return record

    def get_successful_trajectories(self, min_improvement: float = 0.0) -> List[Dict[str, Any]]:
        """
        Filters trajectories that yielded improvement over baseline or previous iterations.
        """
        return [t for t in self.trajectories if t.get("status") == "IMPROVED" or t.get("improvement_delta", 0.0) >= min_improvement]

    def export_qlora_dataset(self, output_path: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Converts successful experiment trajectories into instruction dataset pairs (prompt -> optimal JSON decision)
        ready for Hugging Face TRL / SFTTrainer QLoRA fine-tuning.
        """
        successful = self.get_successful_trajectories()
        dataset_records = []

        for item in successful:
            prompt = item.get("prompt")
            params = item.get("chosen_params")
            hyp = item.get("hypothesis")
            if not prompt or not params:
                continue

            completion = json.dumps({
                "hypothesis": hyp,
                "parameters": params
            }, indent=2)

            dataset_records.append({
                "prompt": prompt,
                "completion": completion,
                "text": f"<s>[INST] {prompt} [/INST] {completion}</s>"
            })

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(dataset_records, f, indent=2)
            logger.info(f"Exported {len(dataset_records)} QLoRA training pairs to {output_path}")

        return dataset_records
