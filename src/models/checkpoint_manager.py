import os
import sys
import time
import logging
import torch
import torch.nn as nn
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("CheckpointManager")
logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_CHECKPOINT_PATH = os.path.join(BASE_DIR, "data", "stgnn_bataan_12nodes.pt")

def save_model_checkpoint(
    model: nn.Module,
    filepath: str = DEFAULT_CHECKPOINT_PATH,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Saves model state dictionary and training metadata to disk.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    payload = {
        "model_state": model.state_dict(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metadata": metadata or {}
    }
    torch.save(payload, filepath)
    logger.info(f"[CHECKPOINT] Model weights saved to '{filepath}'")
    return filepath

def load_model_checkpoint(
    model: nn.Module,
    filepath: str = DEFAULT_CHECKPOINT_PATH,
    device: Optional[torch.device] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Loads model state dictionary and returns metadata dictionary.
    """
    if not os.path.exists(filepath):
        logger.warning(f"Checkpoint file '{filepath}' does not exist. Model weights unchanged.")
        return False, {}

    try:
        map_loc = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        payload = torch.load(filepath, map_location=map_loc)
        
        if isinstance(payload, dict) and "model_state" in payload:
            model.load_state_dict(payload["model_state"])
            meta = payload.get("metadata", {})
            logger.info(f"[CHECKPOINT] Successfully loaded weights from '{filepath}' (Saved at {payload.get('timestamp')})")
            return True, meta
        elif isinstance(payload, dict):
            model.load_state_dict(payload)
            logger.info(f"[CHECKPOINT] Loaded state dict from '{filepath}'")
            return True, {}
    except Exception as e:
        logger.error(f"Error loading checkpoint from '{filepath}': {str(e)}")
    return False, {}
