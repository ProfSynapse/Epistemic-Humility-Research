#!/usr/bin/env python3
"""Sample GRPO rollouts and inspect reward variance before training.

This is a preflight diagnostic for Amendment B GRPO/RLVR. It intentionally does
not train. It loads a GRPO YAML config, samples multiple completions per prompt
under the intended generation settings, scores those completions with the
configured reward stack, and writes raw completions plus per-prompt variance.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
GRPO_TRAINER_DIR = REPO_ROOT / "synaptic-tuner" / "Trainers" / "grpo"
sys.path.insert(0, str(GRPO_TRAINER_DIR / "src"))
sys.path.insert(0, str(GRPO_TRAINER_DIR.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _init_trainer_env() -> None:
    from shared.env_bootstrap import init_trainer_env, suppress_transformers_logging

    init_trainer_env(apply_windows_patches=False)
    suppress_transformers_logging()
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


def _detect_chat_template(model_name: str) -> str:
    name = model_name.lower()
    if "qwen" in name:
        return "chatml"
    if "llama" in name:
        return "llama-3"
    if "mistral" in name:
        return "mistral"
    if "gemma" in name:
        return "gemma"
    if "phi" in name:
        return "phi-3"
    if "deepseek" in name:
        return "chatml"
    return "chatml"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _resolve_path(value: str | None, *, base: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def _format_prompt(tokenizer: Any, prompt_value: Any, chat_template_kwargs: dict[str, Any]) -> str:
    if isinstance(prompt_value, str):
        return prompt_value
    return tokenizer.apply_chat_template(
        prompt_value,
        tokenize=False,
        add_generation_prompt=True,
        **chat_template_kwargs,
    )


def _label_plan(rows: list[dict[str, Any]], max_rows: int) -> list[dict[str, Any]]:
    known = [row for row in rows if str(row.get("label", "")).lower() == "known"]
    unknown = [row for row in rows if str(row.get("label", "")).lower() == "unknown"]
    half = max(1, max_rows // 2)
    selected = known[:half] + unknown[: max_rows - len(known[:half])]
    if len(selected) < max_rows:
        selected.extend(row for row in rows if row not in selected)
    return selected[:max_rows]


def _build_reward_fn(config: dict[str, Any]):
    from rewards import build_combined_reward_function

    reward_fn, reward_plan = build_combined_reward_function(
        rewards_config=config.get("rewards", {}),
        base_dir=GRPO_TRAINER_DIR,
    )
    return reward_fn, reward_plan


def _load_model_and_tokenizer(config: dict[str, Any], *, apply_training_lora: bool):
    from model_loader import (
        apply_lora_adapters,
        get_text_tokenizer,
        load_from_sft_checkpoint,
        load_model_and_tokenizer,
    )
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template

    model_cfg = config["model"]
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
    lora_path = model_cfg.get("lora_path")
    if lora_path:
        model, tokenizer_or_processor, _is_vl = load_from_sft_checkpoint(
            base_model_name=model_cfg["model_name"],
            lora_path=str(_resolve_path(lora_path, base=REPO_ROOT)),
            max_seq_length=model_cfg["max_seq_length"],
            dtype=model_cfg.get("dtype"),
            load_in_4bit=model_cfg.get("load_in_4bit", True),
            hf_token=hf_token,
        )
    else:
        model, tokenizer_or_processor, _is_vl = load_model_and_tokenizer(
            model_name=model_cfg["model_name"],
            max_seq_length=model_cfg["max_seq_length"],
            dtype=model_cfg.get("dtype"),
            load_in_4bit=model_cfg.get("load_in_4bit", True),
            hf_token=hf_token,
        )

    tokenizer = get_text_tokenizer(tokenizer_or_processor)
    chat_template_name = model_cfg.get("chat_template") or _detect_chat_template(model_cfg["model_name"])
    if str(chat_template_name).lower() not in {"native", "tokenizer"}:
        tokenizer = get_chat_template(tokenizer, chat_template=chat_template_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    if apply_training_lora:
        lora_cfg = config["lora"]
        model = apply_lora_adapters(
            model=model,
            is_vision_model=False,
            r=lora_cfg["r"],
            lora_alpha=lora_cfg["lora_alpha"],
            lora_dropout=lora_cfg["lora_dropout"],
            bias=lora_cfg["bias"],
            target_modules=lora_cfg["target_modules"],
            use_gradient_checkpointing=lora_cfg["use_gradient_checkpointing"],
            random_state=lora_cfg["random_state"],
            use_rslora=lora_cfg.get("use_rslora", False),
            use_dora=lora_cfg.get("use_dora", False),
        )
    FastLanguageModel.for_inference(model)
    return model, tokenizer, chat_template_name


def _truncate_prompt(inputs: dict[str, Any], max_prompt_length: int) -> dict[str, Any]:
    if max_prompt_length <= 0:
        return inputs
    for key in ("input_ids", "attention_mask"):
        tensor = inputs.get(key)
        if tensor is not None and tensor.shape[-1] > max_prompt_length:
            inputs[key] = tensor[:, -max_prompt_length:]
    return inputs


def _score_group(
    reward_fn,
    completions: list[str],
    row: dict[str, Any],
    prompt_text: str,
) -> tuple[list[float], list[dict[str, Any]]]:
    rewards = reward_fn(
        completions,
        prompts=[prompt_text] * len(completions),
        label=[row.get("label")] * len(completions),
        aliases=[row.get("aliases", [])] * len(completions),
    )
    import humility_reward as hr

    parsed = []
    for completion, reward in zip(completions, rewards):
        p = hr.parse_completion(completion)
        parsed.append(
            {
                "reward": float(reward),
                "valid_json": bool(p.valid_json),
                "answer_text": p.answer_text,
                "confidence": p.stated_confidence,
                "is_refusal": hr.is_refusal(p.answer_text),
                "completion": completion,
            }
        )
    return [float(r) for r in rewards], parsed


def run_diagnostic(args: argparse.Namespace) -> dict[str, Any]:
    _init_trainer_env()
    import torch

    config_path = Path(args.config).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    training = config["training"]
    dataset_cfg = config["dataset"]

    dataset_file = _resolve_path(dataset_cfg.get("local_file"), base=REPO_ROOT)
    if dataset_file is None or not dataset_file.exists():
        raise FileNotFoundError(f"dataset local_file not found: {dataset_file}")

    rows = _label_plan(_read_jsonl(dataset_file), max_rows=args.max_rows)
    model, tokenizer, chat_template_name = _load_model_and_tokenizer(
        config,
        apply_training_lora=not args.no_training_lora,
    )
    reward_fn, reward_plan = _build_reward_fn(config)

    max_completion_length = args.max_completion_length or int(training["max_completion_length"])
    temperature = args.temperature if args.temperature is not None else float(training["temperature"])
    num_rollouts = args.num_rollouts or int(training["num_generations"])
    max_prompt_length = int(training.get("max_prompt_length", 0))
    chat_template_kwargs = dict(training.get("chat_template_kwargs") or {})

    out_dir = Path(args.output_dir) if args.output_dir else (
        REPO_ROOT
        / "scratch"
        / "grpo_bootstrap"
        / "diagnostics"
        / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "rollouts.jsonl"

    groups: list[dict[str, Any]] = []
    with raw_path.open("w", encoding="utf-8") as handle:
        for row_index, row in enumerate(rows):
            prompt_text = _format_prompt(
                tokenizer,
                row[dataset_cfg.get("prompt_column", "prompt")],
                chat_template_kwargs=chat_template_kwargs,
            )
            inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
            inputs = _truncate_prompt(inputs, max_prompt_length=max_prompt_length)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    do_sample=True,
                    temperature=temperature,
                    top_p=float(args.top_p),
                    max_new_tokens=max_completion_length,
                    num_return_sequences=num_rollouts,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )

            prompt_tokens = inputs["input_ids"].shape[-1]
            completions = [
                tokenizer.decode(output[prompt_tokens:], skip_special_tokens=True).strip()
                for output in outputs
            ]
            rewards, parsed = _score_group(reward_fn, completions, row, prompt_text)
            std = pstdev(rewards) if len(rewards) > 1 else 0.0
            group = {
                "row_index": row_index,
                "id": row.get("id"),
                "question_id": row.get("question_id"),
                "label": row.get("label"),
                "question": row.get("prompt", [{}, {"content": ""}])[-1].get("content", ""),
                "aliases": row.get("aliases", []),
                "reward_mean": mean(rewards),
                "reward_std": std,
                "reward_min": min(rewards),
                "reward_max": max(rewards),
                "valid_json_rate": sum(1 for item in parsed if item["valid_json"]) / len(parsed),
                "clipped_rate": sum(
                    1
                    for completion in completions
                    if len(tokenizer(completion, add_special_tokens=False)["input_ids"]) >= max_completion_length
                )
                / len(completions),
                "rollouts": parsed,
            }
            groups.append(group)
            handle.write(json.dumps(group, ensure_ascii=False) + "\n")
            handle.flush()

    per_prompt_stds = [group["reward_std"] for group in groups]
    summary = {
        "status": "ok",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path),
        "dataset_file": str(dataset_file),
        "output_dir": str(out_dir),
        "raw_rollouts": str(raw_path),
        "model_name": config["model"].get("model_name"),
        "lora_path": config["model"].get("lora_path"),
        "chat_template": chat_template_name,
        "applied_training_lora": not args.no_training_lora,
        "num_prompts": len(groups),
        "num_rollouts": num_rollouts,
        "temperature": temperature,
        "top_p": float(args.top_p),
        "max_prompt_length": max_prompt_length,
        "max_completion_length": max_completion_length,
        "chat_template_kwargs": chat_template_kwargs,
        "reward_plan": reward_plan,
        "mean_reward_std": mean(per_prompt_stds) if per_prompt_stds else math.nan,
        "max_reward_std": max(per_prompt_stds) if per_prompt_stds else math.nan,
        "zero_std_prompt_rate": (
            sum(1 for value in per_prompt_stds if value == 0.0) / len(per_prompt_stds)
            if per_prompt_stds
            else math.nan
        ),
        "mean_valid_json_rate": mean(group["valid_json_rate"] for group in groups) if groups else math.nan,
        "mean_clipped_rate": mean(group["clipped_rate"] for group in groups) if groups else math.nan,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="GRPO YAML config path")
    parser.add_argument("--output-dir", help="Directory for summary.json and rollouts.jsonl")
    parser.add_argument("--max-rows", type=int, default=4, help="Number of prompts to sample")
    parser.add_argument("--num-rollouts", type=int, help="Rollouts per prompt; defaults to config training.num_generations")
    parser.add_argument("--max-completion-length", type=int, help="Override max new tokens")
    parser.add_argument("--temperature", type=float, help="Override sampling temperature")
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument(
        "--no-training-lora",
        action="store_true",
        help="Skip applying the train-time GRPO LoRA wrapper before sampling.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    run_diagnostic(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
