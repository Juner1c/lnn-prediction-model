---
title: Scheduled Autotuning Service
category: concept
tags: [service, daemon, scheduler, autotuning, checkpoint]
created: 2026-07-23T09:50:00Z
updated: 2026-07-23T09:50:00Z
---

# Scheduled Autotuning Service

The Scheduled Autotuning Service (`scripts/schedule_autotuning.py`) is a continuous background daemon that periodically wakes the **LFM2.5-8B Autonomous Loop** to ingest incoming station telemetry, optimize STGNN + LNN hyperparameters, evaluate accuracy under station dropouts, update production model weights (`data/stgnn_bataan_12nodes.pt`), and fine-tune the LFM meta-controller via 4-bit QLoRA.

## Core Operations

1. **Telemetry Ingestion**: Ingests newly accumulated CSV/telemetry files in `data/` and aligns 12 stations to a continuous hourly timeline.
2. **Experiment Execution**: Prompts `LFMAgentController` (with 4-bit NF4 quantization) to formulate hypotheses and test hyperparameter variations.
3. **Model Checkpointing**: If validation RMSE improves, saves state dictionary and metadata via `save_model_checkpoint()` to `data/stgnn_bataan_12nodes.pt`.
4. **QLoRA Fine-Tuning**: Triggers periodic 4-bit QLoRA SFT on winning experiment trajectories, updating adapter weights in `data/lfm_agent_lora/`.
