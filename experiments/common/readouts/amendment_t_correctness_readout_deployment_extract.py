#!/usr/bin/env python3
"""Amendment T — deployment-checkpoint correctness-readout extraction (GPU).

Pre-registered in
experiments/correctness-readout-deployment-port/AMENDMENT.md
(SIGNED 2026-06-30). Exploratory, single-model, single-seed; reported separately
from the locked PROTOCOL v0.3 matrix.

THE QUESTION: Amendment S established a post-gen correctness readout on the
Qwen3-4B *Instruct base*. T asks whether that readout SURVIVES on the checkpoint
we would ship — clean-SFT merged base + GRPO-v2 LoRA adapter — or was an
Instruct-base artifact.

This is the SAME surface as Amendment S (same PopQA+TriviaQA pool, same
dual-position extraction, same Cheng grading, same persisted-tensor layout) so the
S scorer (amendment_s_correctness_probe_score.py) reads T's output unchanged. Only
two things differ from S, both forced by the deployment checkpoint:

  1. MODEL: clean-SFT merged-16bit base + GRPO-v2 LoRA adapter applied via PEFT
     (mirrors hs_backends.TransformersPeftBackend's load: AutoModelForCausalLM on
     the merged base, then PeftModel.from_pretrained(base, adapter)). The adapter
     stays ACTIVE for both generation and extraction — we read the deployed model.

  2. ABSTENTION SUPPRESSION (locked sign-off choice = forced-best-guess prompt):
     the deployed checkpoint is abstention-trained and answers only when ~94%
     likely right, so it yields no wrong class. A forced-best-guess system prompt
     ("never abstain; give one best-guess answer") produces a labeled correct/wrong
     set. DISTRIBUTION-SHIFT CAVEAT (protocol §3): this measures whether correctness
     is READABLE on this checkpoint, not whether the probe generalizes to the
     model's NATURAL (un-forced) answers — that is an explicit follow-up.

The pure helpers (pool loaders, content-end trimming, config-sha) are imported
from the Amendment S extractor so the two surfaces cannot silently diverge.
No training run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

READOUTS_DIR = Path(__file__).resolve().parent
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))
try:
    from .path_compat import locked_eval_dir, knowledge_probe_dir, repo_root
except ImportError:  # direct script execution
    from path_compat import locked_eval_dir, knowledge_probe_dir, repo_root

PROBE_DIR = knowledge_probe_dir()
EVAL_DIR = locked_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402  (from archive/experiment/phase1/eval)
from backends import render_probe_prompt  # noqa: E402  (from experiments/common/knowledge_probe)
# Reuse Amendment S's pure helpers verbatim so the surfaces stay identical.
from amendment_s_correctness_probe_extract import (  # noqa: E402
    _config_sha,
    _content_end_index,
    build_pool,
)

# Forced-best-guess system prompt (LOCKED abstention-suppression method, §3 / sign-off
# 2026-06-30). Deliberately suppresses the abstention the deployed checkpoint was
# trained into, so a wrong class exists. Recorded in the manifest for provenance.
SYSTEM_PROMPT = (
    "You are a helpful assistant. Always give your single best-guess answer to "
    "every question. Never refuse, never say you do not know, and never decline. "
    "Even if you are unsure, state your most likely answer as a direct, concise "
    "factual answer."
)
MODEL_TAG = "qwen3-4b-clean-sft-grpo-v2"
ADAPTER_NAME = "grpo_v2"


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from safetensors.torch import save_file

    datasets_root = Path(args.datasets_root).resolve()
    base_path = Path(args.base_model).resolve()
    adapter_path = Path(args.adapter).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config_payload = {
        "amendment": "T",
        "base_model_path": str(base_path),
        "adapter_path": str(adapter_path),
        "adapter_name": ADAPTER_NAME,
        "checkpoint": "clean-sft-merged-16bit + grpo-v2-lora",
        "model_tag": MODEL_TAG,
        "system_prompt": SYSTEM_PROMPT,
        "abstention_suppression": "forced-best-guess-prompt",
        "enable_thinking": False,
        "datasets": sorted(args.datasets),
        "max_new_tokens": args.max_new_tokens,
        "target_correct": args.target_correct,
        "target_wrong": args.target_wrong,
        "max_attempts": args.max_attempts,
        "seed": args.seed,
        "persist_dtype": "float32",
        "decode": "greedy",
    }
    config_sha = _config_sha(config_payload)

    print(f"[amendment-t] loading base {base_path} + adapter {adapter_path} ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(str(base_path))
    base = AutoModelForCausalLM.from_pretrained(
        str(base_path), torch_dtype=torch.bfloat16, device_map="cuda")
    model = PeftModel.from_pretrained(base, str(adapter_path),
                                      adapter_name=ADAPTER_NAME)
    model.eval()
    model.set_adapter(ADAPTER_NAME)  # deployed model = adapter ACTIVE
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers

    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end, int) and im_end >= 0:
        special_ids.add(im_end)
    eos_for_gen = tokenizer.eos_token_id
    if isinstance(im_end, int) and im_end >= 0:
        eos_for_gen = ([tokenizer.eos_token_id, im_end]
                       if tokenizer.eos_token_id is not None else im_end)

    pool = build_pool(datasets_root, args.datasets, args.per_dataset, args.seed)
    print(f"[amendment-t] pool size={len(pool)}; "
          f"targets correct>={args.target_correct} wrong>={args.target_wrong}",
          flush=True)

    rows_path = out_dir / "rows.jsonl"
    n_correct = n_wrong = n_answered = n_refused = n_empty = 0
    written = 0

    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for item in pool:
            if (n_correct >= args.target_correct and n_wrong >= args.target_wrong):
                break
            if written >= args.max_attempts:
                break

            rendered, _mode = render_probe_prompt(
                tokenizer, SYSTEM_PROMPT, item["question"], enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])

            with torch.no_grad():
                gen = model.generate(
                    **enc,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    num_beams=1,
                    eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True,
                )
            full = gen.sequences[0]
            full_list = full.tolist()
            new_ids = full_list[prompt_len:]
            answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()

            refused = scorers.is_stated_confidence_refusal(answer_text)
            content_end = _content_end_index(full_list, prompt_len, special_ids)
            answered = (content_end is not None) and bool(answer_text) and not refused

            correct = (
                scorers.is_correct(answer_text, item["aliases_norm"])
                if answered else False
            )

            label = None
            if answered:
                seq_end = content_end
                fwd_ids = full[: seq_end + 1].unsqueeze(0).to(device)
                attn = torch.ones_like(fwd_ids)
                with torch.no_grad():
                    out = model(input_ids=fwd_ids, attention_mask=attn,
                                output_hidden_states=True, use_cache=False)
                hs = out.hidden_states
                pre_pos = prompt_len - 1
                post_pos = seq_end
                pre_tensors = {
                    f"L{li}": hs[li][0, pre_pos, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                post_tensors = {
                    f"L{li}": hs[li][0, post_pos, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                safe_key = item["row_key"].replace("::", "__").replace("|", "_")
                save_file(pre_tensors, str(out_dir / f"{safe_key}__pre.safetensors"))
                save_file(post_tensors, str(out_dir / f"{safe_key}__post.safetensors"))
                label = "correct" if correct else "wrong"
                if correct:
                    n_correct += 1
                else:
                    n_wrong += 1
                n_answered += 1
            else:
                if refused:
                    n_refused += 1
                else:
                    n_empty += 1

            rows_fh.write(json.dumps({
                "row_key": item["row_key"],
                "dataset": item["dataset"],
                "question": item["question"],
                "answer_text": answer_text,
                "aliases_norm": item["aliases_norm"],
                "answered": answered,
                "refused": refused,
                "correct": bool(correct) if answered else None,
                "label": label,
                "prompt_len": prompt_len,
                "answer_tok_len": (content_end - prompt_len + 1) if content_end is not None else 0,
                "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 25 == 0:
                print(f"[amendment-t] attempts={written} answered={n_answered} "
                      f"correct={n_correct} wrong={n_wrong} refused={n_refused} "
                      f"empty={n_empty}", flush=True)

    manifest = {
        **config_payload,
        "config_sha": config_sha,
        "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size,
        "n_attempts": written,
        "n_answered": n_answered,
        "n_correct": n_correct,
        "n_wrong": n_wrong,
        "n_refused": n_refused,
        "n_empty": n_empty,
        "out_dir": str(out_dir),
        "positions": ["pre", "post"],
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"\n[amendment-t] DONE answered={n_answered} "
          f"correct={n_correct} wrong={n_wrong} -> {out_dir}", flush=True)

    floor = args.adequacy_floor
    if n_correct < floor or n_wrong < floor:
        print(f"[amendment-t] WARNING: below data-adequacy floor "
              f"({floor}/{floor}); correct={n_correct} wrong={n_wrong}. "
              "This is a DATA-STAGE stop (suppress abstention harder / pool more "
              "questions), NOT a probe verdict.", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True,
                    help="output dir (gitignored model_tag subtree)")
    ap.add_argument("--base-model", required=True,
                    help="clean-SFT merged-16bit base model dir")
    ap.add_argument("--adapter", required=True,
                    help="GRPO-v2 LoRA adapter dir (final_model)")
    ap.add_argument("--datasets-root",
                    default=str(repo_root() / "datasets"),
                    help="repo datasets/ root")
    ap.add_argument("--datasets", nargs="+", default=["popqa", "triviaqa"],
                    choices=["popqa", "triviaqa"])
    ap.add_argument("--per-dataset", type=int, default=None)
    ap.add_argument("--target-correct", type=int, default=500)
    ap.add_argument("--target-wrong", type=int, default=500)
    ap.add_argument("--max-attempts", type=int, default=4000)
    ap.add_argument("--max-new-tokens", type=int, default=48)
    ap.add_argument("--adequacy-floor", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260630)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
