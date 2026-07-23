import os
import sys
import time
import logging
import argparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.run_agentic_loop import run_autonomous_loop
from src.models.checkpoint_manager import DEFAULT_CHECKPOINT_PATH

logger = logging.getLogger("ScheduledAutotuningService")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ScheduledAutotuning: %(message)s")

def execute_retraining_pass(max_iterations: int = 3, finetune_interval: int = 2) -> bool:
    """
    Executes a single scheduled retraining pass using LFM2.5-8B agentic loop over 12 Bataan weather stations.
    """
    logger.info("==========================================================================")
    logger.info("   SCHEDULED AUTONOMOUS RETRAINING & LFM QLORA UPDATE CYCLE               ")
    logger.info("==========================================================================")
    
    try:
        run_autonomous_loop(
            max_iterations=max_iterations,
            finetune_interval=finetune_interval,
            load_model=False
        )
        if os.path.exists(DEFAULT_CHECKPOINT_PATH):
            logger.info(f"[SUCCESS] Retraining pass complete. Active model checkpoint verified at '{DEFAULT_CHECKPOINT_PATH}'")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Retraining pass failed: {str(e)}")
        return False

def start_scheduled_service(
    interval_hours: float = 6.0,
    max_iterations: int = 3,
    finetune_interval: int = 2,
    run_once: bool = False
):
    """
    Service entrypoint for scheduled autotuning.
    """
    logger.info(f"Starting Scheduled Autotuning Service (interval={interval_hours}h, iterations={max_iterations}, run_once={run_once})")

    if run_once:
        execute_retraining_pass(max_iterations=max_iterations, finetune_interval=finetune_interval)
        logger.info("Single scheduled update pass completed.")
        return

    interval_seconds = int(interval_hours * 3600)
    cycle = 1
    while True:
        logger.info(f"\n--- Retraining Cycle #{cycle} ---")
        execute_retraining_pass(max_iterations=max_iterations, finetune_interval=finetune_interval)
        logger.info(f"Cycle #{cycle} complete. Sleeping for {interval_hours} hours ({interval_seconds}s)...")
        cycle += 1
        time.sleep(interval_seconds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scheduled Retraining & Weight Persistence Service")
    parser.add_argument("--interval-hours", type=float, default=6.0, help="Interval between retraining cycles in hours.")
    parser.add_argument("--max-iterations", type=int, default=3, help="Number of experiment iterations per scheduled pass.")
    parser.add_argument("--finetune-interval", type=int, default=2, help="Trigger QLoRA fine-tuning after N successful runs.")
    parser.add_argument("--run-once", action="store_true", help="Execute a single retraining pass and exit.")
    args = parser.parse_args()

    start_scheduled_service(
        interval_hours=args.interval_hours,
        max_iterations=args.max_iterations,
        finetune_interval=args.finetune_interval,
        run_once=args.run_once
    )
