import os
import sys
import json
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("LFMAgentController")
logging.basicConfig(level=logging.INFO)

DEFAULT_MODEL_ID = os.getenv("LFM_MODEL_ID", "LiquidAI/LFM2.5-8B-A1B")

class LFMAgentController:
    """
    Controller for LFM2.5-8B-A1B Hugging Face model loaded locally via 4-bit NF4 quantization.
    Acts as the Meta-Controller & Experiment Optimizer that drives the autonomous data science loop.
    """
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        use_4bit: bool = True,
        load_model: bool = False,
        adapter_path: Optional[str] = None
    ):
        self.model_id = model_id
        self.use_4bit = use_4bit
        self.adapter_path = adapter_path
        self.tokenizer = None
        self.model = None
        self.is_loaded = False

        if load_model:
            self._load_huggingface_model()

    def _load_huggingface_model(self):
        """
        Loads LFM2.5-8B-A1B base model and optional LoRA adapters using 4-bit NF4 quantization.
        """
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

            logger.info(f"Loading Hugging Face model '{self.model_id}' (4-bit={self.use_4bit})...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            quantization_config = None
            if self.use_4bit and torch.cuda.is_available():
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True
                )

            device_map = "auto" if torch.cuda.is_available() else "cpu"
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config=quantization_config,
                device_map=device_map,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True
            )

            if self.adapter_path and os.path.exists(self.adapter_path):
                from peft import PeftModel
                logger.info(f"Attaching fine-tuned QLoRA adapter from '{self.adapter_path}'...")
                self.model = PeftModel.from_pretrained(self.model, self.adapter_path)

            self.is_loaded = True
            logger.info("LFM2.5-8B-A1B model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load Hugging Face model '{self.model_id}': {str(e)}. Operating in fallback heuristic agent mode.")
            self.is_loaded = False

    def build_system_prompt(self, history_summary: List[Dict[str, Any]]) -> str:
        """
        Constructs structured prompt with past experiment trajectories across 12 Bataan weather stations.
        """
        history_str = ""
        if not history_summary:
            history_str = "No previous experiments executed yet. This is the baseline initialization run."
        else:
            recent_logs = history_summary[-5:]
            for idx, item in enumerate(recent_logs, 1):
                params = item.get("chosen_params", {})
                rmse = item.get("validation_rmse", "N/A")
                mae = item.get("validation_mae", "N/A")
                delta = item.get("improvement_delta", 0.0)
                status = "IMPROVED" if delta > 0 else "NO_IMPROVEMENT"
                history_str += f"\nExp {idx}: params={json.dumps(params)} => Val RMSE: {rmse} °C | Status: {status}"

        prompt = f"""You are the LFM2.5-8B Autonomous Data Science Meta-Controller for a 12-Station Bataan LNN + Spatial-Temporal GNN Weather Forecasting System.
Your goal is to optimize multi-variable forecast accuracy (temperature, humidity, air pressure, wind speed, heat index) under real-world sensor misreadings, zero-values, and missing/down stations (e.g., Limay or Quinawan offline).

### Past Experiment Trajectory History:
{history_str}

### Instructions:
Propose the NEXT hyperparameter experiment hypothesis to evaluate. You must output ONLY a valid JSON object matching this exact schema:
{{
  "hypothesis": "<Short clear explanation of why you chose these parameters for dirty data & station outage recovery>",
  "parameters": {{
    "lr": <float between 0.0001 and 0.01>,
    "batch_size": <int: 8, 16, 32, or 64>,
    "epochs": <int between 5 and 30>,
    "hidden_dim": <int: 32, 64, 128, or 256>,
    "recon_weight": <float between 0.01 and 0.5>,
    "outage_mask_ratio": <float between 0.0 and 0.35>
  }}
}}
Do NOT include any extra conversational markdown text outside the raw JSON object.
"""
        return prompt

    def generate_experiment_proposal(self, history_summary: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates next experiment proposal dictionary using LFM2.5-8B model inference, with JSON parsing & fallback bounds.
        """
        prompt = self.build_system_prompt(history_summary)

        if self.is_loaded and self.model is not None and self.tokenizer is not None:
            try:
                import torch
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=256,
                        temperature=0.7,
                        top_p=0.9,
                        do_sample=True,
                        pad_token_id=self.tokenizer.pad_token_id
                    )
                generated_text = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
                parsed = self.parse_json_response(generated_text)
                if parsed:
                    return self.validate_and_clamp_params(parsed)
            except Exception as e:
                logger.error(f"Inference error during LFM generation: {str(e)}. Utilizing fallback proposal generator.")

        # Fallback deterministic heuristic generator if offline or model uninitialized
        return self._heuristic_fallback_proposal(history_summary)

    def parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extracts and parses JSON object from model output text.
        """
        try:
            # Match first JSON block in text
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
        return None

    def validate_and_clamp_params(self, raw_proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures model hyperparameter proposals stay strictly within physically safe and valid bounds ("no going off the rails").
        """
        hypothesis = raw_proposal.get("hypothesis", "Exploring hyperparameter adjustments.")
        params = raw_proposal.get("parameters", {})

        lr = float(params.get("lr", 0.001))
        lr = max(0.0001, min(0.01, lr))

        batch_size = int(params.get("batch_size", 16))
        batch_size = 16 if batch_size not in [8, 16, 32, 64] else batch_size

        epochs = int(params.get("epochs", 15))
        epochs = max(5, min(30, epochs))

        hidden_dim = int(params.get("hidden_dim", 32))
        hidden_dim = 32 if hidden_dim not in [16, 32, 64, 128] else hidden_dim

        recon_weight = float(params.get("recon_weight", 0.1))
        recon_weight = max(0.01, min(0.5, recon_weight))

        return {
            "hypothesis": hypothesis,
            "parameters": {
                "lr": round(lr, 5),
                "batch_size": batch_size,
                "epochs": epochs,
                "hidden_dim": hidden_dim,
                "recon_weight": round(recon_weight, 3)
            }
        }

    def _heuristic_fallback_proposal(self, history_summary: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Heuristic exploration strategy when running offline or without local GPU VRAM.
        """
        num_exps = len(history_summary)
        
        # Grid/Search variations for autonomous loop exploration
        variations = [
            {"lr": 0.001, "batch_size": 16, "epochs": 10, "hidden_dim": 32, "recon_weight": 0.1, "hyp": "Baseline initialization search."},
            {"lr": 0.0005, "batch_size": 16, "epochs": 15, "hidden_dim": 64, "recon_weight": 0.15, "hyp": "Lower learning rate with expanded STGNN hidden capacity."},
            {"lr": 0.002, "batch_size": 32, "epochs": 12, "hidden_dim": 32, "recon_weight": 0.05, "hyp": "Higher learning rate with larger batch batch size and lighter LNN denoising loss."},
            {"lr": 0.0008, "batch_size": 16, "epochs": 20, "hidden_dim": 64, "recon_weight": 0.2, "hyp": "Extended training epochs with stronger LNN reconstruction penalty."},
            {"lr": 0.0003, "batch_size": 8, "epochs": 15, "hidden_dim": 128, "recon_weight": 0.1, "hyp": "Deep STGNN capacity with fine-grained mini-batch updates."}
        ]

        choice = variations[num_exps % len(variations)]
        return {
            "hypothesis": choice["hyp"],
            "parameters": {
                "lr": choice["lr"],
                "batch_size": choice["batch_size"],
                "epochs": choice["epochs"],
                "hidden_dim": choice["hidden_dim"],
                "recon_weight": choice["recon_weight"]
            }
        }
