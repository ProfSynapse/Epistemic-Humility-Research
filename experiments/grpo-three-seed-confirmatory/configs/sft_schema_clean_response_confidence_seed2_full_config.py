"""SFT clean response-confidence seed-2 full local config.

Restored working format: train_sft.py's `--config` flag imports this file as a
Python module via importlib and calls `Config()` (see train_sft.py:590-597).
The archived `.yaml` "auto-converted" sibling
(archive/experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_full.yaml)
does NOT load through the current --config path — confirmed by a direct failed
launch (AttributeError: 'NoneType' object has no attribute 'loader', because
importlib.util.spec_from_file_location cannot build a loader for a non-Python
file). The original working `_config.py` file for seed 1 was deleted in commit
aa11b49e ("Amendment J") as part of an unrelated PR's "config-format
uniformity" conversion and replaced with the untested `.yaml` version. This
file is restored from `git show aa11b49e^:experiment/phase1/grpo/configs/
sft_schema_clean_response_confidence_seed1_full_config.py`, with only seed,
lora.random_state, and training.output_dir changed for seed 2. Every other
value is carried unchanged from seed-1 evidence, matching cell.yaml's frozen
hyperparameters exactly.

lora.random_state: 2 per lead ruling 2026-07-31 (NOTEBOOK.md "LEAD RULING:
lora.random_state mirrors the seed number") — mirrors seed: 2.
"""

from __future__ import annotations

from configs.config_loader import load_config


def Config():  # noqa: N802 - train_sft.py expects this exact symbol.
    config = load_config()

    config.model.model_name = "unsloth/Qwen3-4B-bnb-4bit"
    config.model.max_seq_length = 2048
    config.model.load_in_4bit = True

    config.dataset.dataset_name = None
    config.dataset.dataset_file = None
    config.dataset.local_file = (
        "scratch/schema_response_confidence/qwen3-4b-instruct/"
        "sft_response_confidence_train_clean.jsonl"
    )
    config.dataset.num_proc = 1
    config.dataset.test_size = 0.0
    config.dataset.split_dataset = False
    config.dataset.filter_desirable = False

    config.training.output_dir = "scratch/schema_response_confidence/runs/sft_schema_clean_seed2_full"
    config.training.per_device_train_batch_size = 10
    config.training.gradient_accumulation_steps = 1
    config.training.learning_rate = 2.0e-4
    config.training.max_grad_norm = 1.0
    config.training.lr_scheduler_type = "linear"
    config.training.max_seq_length = 2048
    config.training.packing = False
    config.training.completion_only_loss = True
    config.training.assistant_only_loss = False
    config.training.gradient_checkpointing = True
    config.training.optim = "adamw_8bit"
    config.training.fp16 = False
    config.training.bf16 = True
    config.training.num_train_epochs = 1
    config.training.warmup_ratio = 0.03
    config.training.logging_steps = 25
    config.training.save_steps = 500
    config.training.save_total_limit = 2
    config.training.dataloader_num_workers = 0
    config.training.dataloader_pin_memory = True
    config.training.group_by_length = False
    config.training.eval_strategy = "no"
    config.training.eval_steps = 500
    config.training.chat_template_kwargs = {"enable_thinking": False}

    config.lora.r = 32
    config.lora.lora_alpha = 64
    config.lora.lora_dropout = 0.05
    config.lora.bias = "none"
    config.lora.target_modules = [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ]
    config.lora.use_gradient_checkpointing = "unsloth"
    config.lora.random_state = 2
    config.lora.use_rslora = False
    config.lora.use_dora = False

    config.wandb.enabled = False
    config.evolutionary.enabled = False
    config.seed = 2
    return config
