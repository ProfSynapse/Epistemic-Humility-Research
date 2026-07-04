#!/usr/bin/env python3
"""Amendment AI — launch one PAR GRPO arm (TRUE or PERMUTED) on the local GPU.

Reuses the schema_clean_sft_grpo_v2 machinery (synaptic-tuner Trainers/grpo) so the
recipe is byte-cloned and ONLY the reward is swapped. Concretely it reuses
train_grpo's own building blocks (model_loader, data_loader, GRPOConfig) rather
than forking run(), then adds the two things the reference entrypoint can't:

  1. wires the live policy model into amendment_ai_par_reward (MODEL/TOKENIZER/
     PROBE/BASELINE_SYSTEM/LOG_PATH/PERMUTATION) at on_train_begin, so the reward
     reads p from the model the trainer is optimizing;
  2. attaches AmendmentAITripwireCallback (prereg §1.5).

The reward function TRL sees is amendment_ai_par_reward.par_reward. The recipe
(steps/LR/seed/G/max_len/beta/LoRA) comes from the arm's config YAML, which is a
clone of grpo_schema_clean_sft_merged_seed1_v2_full.yaml with the reward + data +
output_dir swapped.

PERMUTED arm (--arm permuted): builds a FIXED within-gold-class row_key->row_key
permutation over the full training pool (seed 0), persists it (gitignored) + its
SHA in the run manifest, and sets par.PERMUTATION. Marginals preserved, row-level
coupling destroyed.

CONDUCT: launch, run to completion or tripwire HALT. --max-steps caps for the
launch-verification smoke (first ~10 steps); the real arm omits it. Writes a run
record (recipe echo + reward/permutation provenance) to <run_dir>/amendment_ai_run.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
GRPO_SRC = CANONICAL / "synaptic-tuner/Trainers/grpo"
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
GRPO_ROOT = CANONICAL / "experiment/phase1/grpo"
REFIT = PROBE_ROOT / "analysis/par_sensor_refit"
TRAIN_DIR = PROBE_ROOT / "analysis/amendment_ai/train"
SENSOR_V2 = REFIT / "probes_v2/probe_L24_cleansft4bit.joblib"

for _p in (str(GRPO_SRC), str(GRPO_ROOT), str(PROBE_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def load_jsonl(p: Path):
    return [json.loads(l) for l in Path(p).open(encoding="utf-8") if l.strip()]


def build_permutation(train_rows, seed=0):
    """Within-gold-class row_key permutation (marginals preserved)."""
    rng = random.Random(seed)
    mapping = {}
    for label in ("known", "unknown"):
        keys = sorted(r["row_key"] for r in train_rows if r["label"] == label)
        shuffled = list(keys)
        # derangement-ish: shuffle until not identity (best effort for small classes)
        rng.shuffle(shuffled)
        for a, b in zip(keys, shuffled):
            mapping[a] = b
    return mapping


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, choices=["true", "permuted"])
    ap.add_argument("--config", required=True, help="arm config YAML")
    ap.add_argument("--max-steps", type=int, default=0,
                    help="cap steps for launch-verification (0 = full run)")
    args = ap.parse_args()

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    # import the reference machinery (patches transformers via unsloth on import)
    import train_grpo as tg
    import torch  # noqa: F401
    from trl import GRPOTrainer
    import joblib
    from transformers import TrainerCallback

    import amendment_ai_par_reward as par
    from amendment_ai_tripwire_callback import AmendmentAITripwireCallback
    sys.path.insert(0, str(PROBE_ROOT))
    from amendment_ah_stage0_extract import load_baseline_system_prompt

    config = tg.load_config(args.config)
    model_cfg, training_cfg = config["model"], config["training"]
    dataset_cfg, lora_cfg = config["dataset"], config["lora"]
    if args.max_steps:
        training_cfg["max_steps"] = args.max_steps
        training_cfg["save_steps"] = max(args.max_steps, 1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(training_cfg["output_dir"]) / timestamp
    checkpoints_dir = run_dir / "checkpoints"
    logs_dir = run_dir / "logs"
    for d in (checkpoints_dir, logs_dir):
        d.mkdir(parents=True, exist_ok=True)
    reward_log = logs_dir / "par_reward_steps.jsonl"
    print(f"[ai/arm={args.arm}] run_dir={run_dir}", flush=True)

    # ---- model (byte-clone of the v2 recipe load) ----
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
    model, tok_or_proc, is_vl = tg.load_model_and_tokenizer(
        model_name=model_cfg["model_name"],
        max_seq_length=model_cfg["max_seq_length"], dtype=model_cfg.get("dtype"),
        load_in_4bit=model_cfg.get("load_in_4bit", True), hf_token=hf_token)
    tokenizer = tg.get_text_tokenizer(tok_or_proc)
    # native chat template (config: chat_template=native) — preserve tokenizer's
    model = tg.apply_lora_adapters(
        model=model, is_vision_model=is_vl, r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"], lora_dropout=lora_cfg["lora_dropout"],
        bias=lora_cfg["bias"], target_modules=lora_cfg["target_modules"],
        use_gradient_checkpointing=lora_cfg["use_gradient_checkpointing"],
        random_state=lora_cfg["random_state"])
    tg.check_gpu_memory()

    # ---- data ----
    raw = tg.load_raw_dataset(local_file=dataset_cfg["local_file"],
                              num_proc=dataset_cfg.get("num_proc", 1))
    formatted = tg.format_dataset_for_grpo(
        raw, tokenizer=tokenizer,
        prompt_column=dataset_cfg.get("prompt_column", "prompt"),
        num_proc=dataset_cfg.get("num_proc", 1),
        chat_template_kwargs=training_cfg.get("chat_template_kwargs"))

    # ---- wire the PAR reward globals ----
    par.PROBE = joblib.load(SENSOR_V2)
    par.TOKENIZER = tokenizer
    par.BASELINE_SYSTEM = load_baseline_system_prompt()
    par.LOG_PATH = str(reward_log)
    par.MODEL = None    # set at on_train_begin (live policy)

    perm_sha = None
    train_rows = load_jsonl(dataset_cfg["local_file"])
    if args.arm == "permuted":
        perm = build_permutation(train_rows, seed=0)
        par.PERMUTATION = perm
        perm_path = run_dir / "permutation.json"        # gitignored (row_keys)
        perm_path.write_text(json.dumps(perm, indent=2))
        perm_sha = hashlib.sha256(
            json.dumps(perm, sort_keys=True).encode()).hexdigest()
        print(f"[ai/arm=permuted] permutation n={len(perm)} sha={perm_sha[:12]}",
              flush=True)
    else:
        par.PERMUTATION = None

    class WireModelCallback(TrainerCallback):
        def on_train_begin(self, a, s, c, model=None, **kw):
            par.MODEL = model
            print(f"[ai/arm={args.arm}] PAR reward wired to live policy "
                  f"({type(model).__name__})", flush=True)
            return c

    tripwire = AmendmentAITripwireCallback(
        run_dir=run_dir, audit_path=TRAIN_DIR / "audit_set.jsonl",
        reward_log_path=reward_log)

    training_args = tg._build_grpo_config(config, checkpoints_dir=checkpoints_dir)

    trainer = GRPOTrainer(
        model=model, processing_class=tokenizer,
        reward_funcs=par.par_reward, args=training_args,
        train_dataset=formatted, callbacks=[WireModelCallback(), tripwire])

    # ---- run record ----
    run_record = {
        "amendment": "AI", "arm": args.arm, "timestamp": timestamp,
        "config_file": str(Path(args.config).resolve()),
        "recipe": {k: training_cfg.get(k) for k in
                   ("learning_rate", "num_generations", "per_device_train_batch_size",
                    "gradient_accumulation_steps", "beta", "max_prompt_length",
                    "max_completion_length", "temperature", "num_train_epochs",
                    "max_steps", "lr_scheduler_type", "optim")},
        "seed": config.get("seed"),
        "lora": {k: lora_cfg.get(k) for k in ("r", "lora_alpha", "lora_dropout",
                                              "bias", "random_state")},
        "sensor": str(SENSOR_V2), "reward": "amendment_ai_par_reward.par_reward",
        "reward_constants": {"w_c": par.W_C, "w_a": par.W_A,
                             "format_gate": par.FORMAT_GATE},
        "data_file": dataset_cfg["local_file"], "n_train": len(train_rows),
        "permutation_seed": (0 if args.arm == "permuted" else None),
        "permutation_sha": perm_sha,
        "tripwires": {"sensor_halt": 0.8, "abstain_band": [0.1, 0.9],
                      "degeneracy_halt": 0.1, "check_every": 100},
        "reward_log": str(reward_log), "run_dir": str(run_dir),
        "max_steps_override": args.max_steps or None,
    }
    (run_dir / "amendment_ai_run.json").write_text(json.dumps(run_record, indent=2))
    print(json.dumps({k: run_record[k] for k in ("arm", "recipe", "seed",
          "permutation_sha", "n_train")}, indent=2), flush=True)

    print("[ai/arm] starting training ...", flush=True)
    trainer.train()

    final = run_dir / "final_model"
    final.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final))
    try:
        tokenizer.save_pretrained(str(final))
    except Exception:
        pass
    halted = (run_dir / "HALT.json").exists()
    print(f"[ai/arm={args.arm}] DONE halted={halted} run_dir={run_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
