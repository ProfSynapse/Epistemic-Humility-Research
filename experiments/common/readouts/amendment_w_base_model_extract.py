#!/usr/bin/env python3
"""Amendment W — RAW-base forced-answer generation + dual-position extraction (GPU).

Pre-registered in
experiments/base-model-training-free-mechanism/AMENDMENT.md.
Exploratory, single-model, single-seed; reported separately from PROTOCOL v0.3.

THE QUESTION (§2 H_W1, primary): does the correctness DIAL fit on the RAW Instruct
base (Amendment S, post-gen L20) read a HALLUCINATED answer to an unanswerable
question as low-trust — with NO training at all? U answered this on the TRAINED
checkpoint (AUROC 0.980); this run creates the base-surface analog.

IDENTICAL surface to Amendment S (raw `unsloth/Qwen3-4B-bnb-4bit`, NO adapter,
S's answer-encouraging system prompt) so the base-hallucination post-gen vectors
lie on the SAME generation surface the S base dial was fit on. The ONLY difference
from S is the pool: the SelfAware frozen known/unknown manifest (read straight from
the gate extraction's rows.jsonl, verbatim U path) instead of PopQA/TriviaQA.

Outcome is structural (SelfAware rows are ungraded, verbatim U):
  unknown and answered = HALLUCINATION
  known   and answered = answerable_attempt (ungraded directional control)

Persists, under a gitignored model_tag subtree, for every ANSWERED row:
  <out_dir>/rows.jsonl                     one record per attempt
  <out_dir>/<safe_key>__pre.safetensors    {L0..L<N>} pre-gen anchor (fp32)
  <out_dir>/<safe_key>__post.safetensors   {L0..L<N>} post-gen content token (fp32)
  <out_dir>/manifest.json                  run provenance + config
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
    from .path_compat import locked_eval_dir, knowledge_probe_dir
except ImportError:  # direct script execution
    from path_compat import locked_eval_dir, knowledge_probe_dir

PROBE_DIR = knowledge_probe_dir()
EVAL_DIR = locked_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
# RAW-base surface + helpers VERBATIM from Amendment S (the dial source).
from amendment_s_correctness_probe_extract import (  # noqa: E402
    SYSTEM_PROMPT,
    MODEL_NAME,
    MODEL_TAG,
    _config_sha,
    _content_end_index,
)
# SelfAware pool loader VERBATIM from Amendment U.
from amendment_u_unified_extract import load_selfaware_pool  # noqa: E402


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file

    model_name = args.base_model or MODEL_NAME
    gate_rows = Path(args.gate_rows).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config_payload = {
        "amendment": "W",
        "base_model": model_name,
        "adapter": "NONE-raw-instruct-base",
        "checkpoint": "raw Qwen3-4B Instruct base (no adapter)",
        "model_tag": MODEL_TAG,
        "system_prompt": SYSTEM_PROMPT,
        "abstention_suppression": "NONE-base-is-pre-abstention",
        "pool_source": str(gate_rows),
        "enable_thinking": False,
        "max_new_tokens": args.max_new_tokens,
        "max_attempts": args.max_attempts,
        "seed": args.seed,
        "persist_dtype": "float32",
        "decode": "greedy",
    }
    config_sha = _config_sha(config_payload)

    print(f"[amendment-w] loading RAW base {model_name} (no adapter) ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
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

    pool = load_selfaware_pool(gate_rows, args.seed)
    n_known = sum(1 for p in pool if p["label"] == "known")
    n_unknown = sum(1 for p in pool if p["label"] == "unknown")
    print(f"[amendment-w] pool size={len(pool)} (known={n_known} unknown={n_unknown})",
          flush=True)

    rows_path = out_dir / "rows.jsonl"
    n_answered = n_refused = n_empty = 0
    n_halluc = n_known_answered = 0
    written = 0

    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for item in pool:
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

            outcome = None
            if answered:
                seq_end = content_end
                fwd_ids = full[: seq_end + 1].unsqueeze(0).to(device)
                attn = torch.ones_like(fwd_ids)
                with torch.no_grad():
                    out = model(input_ids=fwd_ids, attention_mask=attn,
                                output_hidden_states=True, use_cache=False)
                hs = out.hidden_states
                pre_tensors = {
                    f"L{li}": hs[li][0, prompt_len - 1, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                post_tensors = {
                    f"L{li}": hs[li][0, seq_end, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                safe_key = item["row_key"].replace("::", "__").replace("|", "_")
                save_file(pre_tensors, str(out_dir / f"{safe_key}__pre.safetensors"))
                save_file(post_tensors, str(out_dir / f"{safe_key}__post.safetensors"))
                if item["label"] == "unknown":
                    outcome = "hallucination"
                    n_halluc += 1
                else:
                    outcome = "answerable_attempt"
                    n_known_answered += 1
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
                "label": item["label"],
                "answer_text": answer_text,
                "answered": answered,
                "refused": refused,
                "outcome": outcome,
                "prompt_len": prompt_len,
                "answer_tok_len": (content_end - prompt_len + 1) if content_end is not None else 0,
                "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 25 == 0:
                print(f"[amendment-w] attempts={written} answered={n_answered} "
                      f"halluc={n_halluc} known_answered={n_known_answered} "
                      f"refused={n_refused} empty={n_empty}", flush=True)

    manifest = {
        **config_payload,
        "config_sha": config_sha,
        "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size,
        "n_pool": len(pool),
        "n_known": n_known,
        "n_unknown": n_unknown,
        "n_attempts": written,
        "n_answered": n_answered,
        "n_hallucination": n_halluc,
        "n_known_answered": n_known_answered,
        "n_refused": n_refused,
        "n_empty": n_empty,
        "out_dir": str(out_dir),
        "positions": ["pre", "post"],
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"\n[amendment-w] DONE answered={n_answered} hallucinations={n_halluc} "
          f"known_answered={n_known_answered} -> {out_dir}", flush=True)

    floor = args.hallucination_floor
    if n_halluc < floor:
        print(f"[amendment-w] WARNING: below hallucination adequacy floor "
              f"({floor}); got {n_halluc}. The raw base is pre-abstention and "
              "should answer freely, so a shortfall is unexpected — this is a "
              "DATA-STAGE stop, NOT a probe verdict.", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True,
                    help="output dir (gitignored model_tag subtree)")
    ap.add_argument("--base-model", default=None,
                    help=f"raw Instruct base (default {MODEL_NAME}); NO adapter")
    ap.add_argument("--gate-rows", required=True,
                    help="SelfAware gate extraction rows.jsonl (frozen pool source)")
    ap.add_argument("--max-attempts", type=int, default=1300)
    ap.add_argument("--max-new-tokens", type=int, default=48)
    ap.add_argument("--hallucination-floor", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260630)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
