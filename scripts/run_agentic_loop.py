import os
import sys
import time
import logging
import argparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.agent.lfm_agent import LFMAgentController
from src.agent.trajectory_memory import TrajectoryMemory
from src.agent.experiment_runner import ExperimentRunner
from scripts.finetune_lfm_agent import finetune_lfm_qlora, LORA_OUTPUT_DIR

logger = logging.getLogger("AutonomousAgenticLoop")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def run_autonomous_loop(
    max_iterations: int = 5,
    finetune_interval: int = 3,
    load_model: bool = False
):
    """
    Master long-running autonomous loop for LFM2.5-8B-A1B self-improving predictive modeling.
    """
    logger.info("==========================================================================")
    logger.info("   LFM2.5-8B-A1B AUTONOMOUS DATA SCIENCE EXPERIMENT & FINE-TUNING LOOP    ")
    logger.info("==========================================================================")
    logger.info(f"Configuration: max_iterations={max_iterations}, finetune_interval={finetune_interval}, load_model={load_model}")

    memory = TrajectoryMemory()
    runner = ExperimentRunner()
    
    adapter_path = LORA_OUTPUT_DIR if os.path.exists(LORA_OUTPUT_DIR) else None
    agent = LFMAgentController(load_model=load_model, adapter_path=adapter_path)

    successful_count = len(memory.get_successful_trajectories())

    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n>>> ITERATION {iteration}/{max_iterations} <<<")
        
        # 1. Fetch past history summary
        history = memory.trajectories
        prompt = agent.build_system_prompt(history)

        # 2. Agent generates hypothesis & hyperparameter proposal
        proposal = agent.generate_experiment_proposal(history)
        hypothesis = proposal.get("hypothesis", "")
        params = proposal.get("parameters", {})

        logger.info(f"Agent Hypothesis: '{hypothesis}'")
        logger.info(f"Proposed Hyperparameters: {params}")

        # 3. Execute experiment training & validation run
        try:
            train_loss, val_rmse, val_mae = runner.run_experiment(params)
        except Exception as e:
            logger.error(f"Experiment execution error: {str(e)}")
            continue

        # 4. Record trajectory in memory
        record = memory.record_experiment(
            hypothesis=hypothesis,
            chosen_params=params,
            train_loss=train_loss,
            validation_rmse=val_rmse,
            validation_mae=val_mae,
            prompt=prompt
        )

        if record.get("status") == "IMPROVED":
            successful_count += 1
            logger.info(f"New Best Model Found! Validation RMSE improved by {record.get('improvement_delta')} °C")

        # 5. Trigger periodic QLoRA fine-tuning update
        if successful_count > 0 and successful_count % finetune_interval == 0:
            logger.info(f"\n--- Triggering Periodic QLoRA Fine-Tuning (Threshold of {finetune_interval} improvements reached) ---")
            updated = finetune_lfm_qlora()
            if updated and load_model:
                # Reload agent with updated adapter weights
                agent = LFMAgentController(load_model=True, adapter_path=LORA_OUTPUT_DIR)

        time.sleep(1)

    logger.info("\n==========================================================================")
    logger.info("   AUTONOMOUS EXPERIMENT LOOP COMPLETE                                     ")
    logger.info(f"Total Runs Logged: {len(memory.trajectories)} | Best RMSE: {memory.get_best_rmse()} °C")
    logger.info("==========================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run autonomous LFM2.5-8B experiment & fine-tuning loop.")
    parser.add_argument("--max-iterations", type=int, default=3, help="Number of experiment iterations to run.")
    parser.add_argument("--finetune-interval", type=int, default=2, help="Trigger QLoRA fine-tuning after N successful runs.")
    parser.add_argument("--load-model", action="store_true", help="Load full Hugging Face LFM2.5-8B weights into memory.")
    args = parser.parse_args()

    run_autonomous_loop(
        max_iterations=args.max_iterations,
        finetune_interval=args.finetune_interval,
        load_model=args.load_model
    )
