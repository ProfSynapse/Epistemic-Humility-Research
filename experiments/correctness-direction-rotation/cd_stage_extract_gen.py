#!/usr/bin/env python3
"""Correctness-direction rotation (CD) — per-stage forced-best-guess
generation + post-generation hidden-state extraction (GPU).

Pre-registered in experiments/correctness-direction-rotation/AMENDMENT.md
(SIGNED 2026-07-19). Exploratory Tier-2 probe-fit cell; never pooled with the
locked PROTOCOL v0.3 matrix.

WHAT THIS DOES. One generation+extraction pass for ONE stage (raw, cleansft,
or partrue — grpov2 is reused from the existing Amendment T stage2 artifacts
and never regenerated, see AMENDMENT.md Design item 5). Mirrors the Amendment
S/T generation+extraction surface EXACTLY (same pool, same forced-best-guess
abstention suppression, same greedy decode, same verbatim Cheng alias scorer)
with two adaptations pinned by cell.yaml:

  1. ALL THREE stages use the forced-best-guess system prompt (T's method),
     not S's neutral "answer concisely" prompt — cell.yaml's `generation:
     forced_best_guess` applies uniformly to raw/cleansft/partrue
     (AMENDMENT.md Design / Populations and generation).
  2. POST-GENERATION ONLY. cell.yaml pins `position: post_generation` as
     primary with pre-gen "optional-descriptive"; this harness does not
     compute the optional secondary (build-time adjudication, recorded in
     NOTEBOOK.md) to halve extraction/storage cost across three
     large-attempt-budget stages. Only the last-answer-content-token
     (post-gen) hidden state is persisted, all layers.

Model loading varies by stage (three call shapes, one script):
  raw      : HF repo id, bnb-4bit already-quantized, NO adapter
             (AutoModelForCausalLM.from_pretrained(..., torch_dtype=bfloat16,
             device_map="cuda"), exactly Amendment S's load path).
  cleansft : local merged-16bit dir, NO adapter (same call, local path).
  partrue  : local merged-16bit dir + local LoRA adapter applied via PEFT
             (PeftModel.from_pretrained + set_adapter), exactly Amendment T's
             load path.

The pure helpers (pool loaders, content-end trimming, config-sha, prompt
render) are imported from the Amendment S/T extractors VERBATIM so the CD
surface cannot silently diverge from the precedent it mirrors.

OUTPUTS (under a gitignored analysis/ subtree, never committed):
  <out_dir>/rows.jsonl              one record per generated attempt
  <out_dir>/<safe_key>__post.safetensors   {L0..Ln} post-gen vectors (fp32)
  <out_dir>/manifest.json            run provenance + config + yield counts

No dataset/question/answer/alias text or token ids leave this gitignored
tree; only aggregate tables (built by cd_rotation_analysis.py) are committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

READOUTS_DIR = (Path(__file__).resolve().parents[2]
                / "experiments" / "common" / "readouts")
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))

from path_compat import locked_eval_dir, knowledge_probe_dir, repo_root  # noqa: E402

PROBE_DIR = knowledge_probe_dir()
EVAL_DIR = locked_eval_dir()
for _p in (str(PROBE_DIR), str(EVAL_DIR), str(READOUTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scorers  # noqa: E402  (from archive/experiment/phase1/eval)
from backends import render_probe_prompt  # noqa: E402  (from experiments/common/knowledge_probe)
# Reuse Amendment S's pure helpers verbatim so the CD surface cannot silently
# diverge from the S/T precedent it mirrors.
from amendment_s_correctness_probe_extract import (  # noqa: E402
    _content_end_index,
    build_pool,
)

# Forced-best-guess system prompt — LOCKED abstention-suppression method,
# identical string to Amendment T (experiments/common/readouts/
# amendment_t_correctness_readout_deployment_extract.py SYSTEM_PROMPT).
# cell.yaml pins `generation: forced_best_guess` for all three GPU stages.
SYSTEM_PROMPT = (
    "You are a helpful assistant. Always give your single best-guess answer to "
    "every question. Never refuse, never say you do not know, and never decline. "
    "Even if you are unsure, state your most likely answer as a direct, concise "
    "factual answer."
)

STAGE_TAGS = {"raw": "qwen3-4b-raw", "cleansft": "qwen3-4b-cleansft",
              "partrue": "qwen3-4b-partrue"}


def _config_sha(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


def build_model(base_model: str, adapter: str | None):
    """Load base (+ optional LoRA adapter). Mirrors S (no-adapter) / T
    (adapter-active) load paths exactly; base_model may be an HF repo id
    (raw, already bnb-4bit quantized) or a local merged-16bit directory
    (cleansft, partrue).
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.bfloat16, device_map="cuda")
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter, adapter_name="stage")
        model.set_adapter("stage")
    model.eval()
    return model, tokenizer


def run(args) -> int:
    import torch
    from safetensors.torch import save_file

    datasets_root = Path(args.datasets_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config_payload = {
        "cell": "correctness-direction-rotation",
        "stage": args.stage,
        "base_model": args.base_model,
        "adapter": args.adapter,
        "model_tag": STAGE_TAGS[args.stage],
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
        "position": "post_generation_only",
    }
    config_sha = _config_sha(config_payload)

    print(f"[cd/{args.stage}] loading base={args.base_model} "
          f"adapter={args.adapter} config_sha={config_sha}", flush=True)
    model, tokenizer = build_model(args.base_model, args.adapter)
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
    print(f"[cd/{args.stage}] pool size={len(pool)}; "
          f"targets correct>={args.target_correct} wrong>={args.target_wrong}",
          flush=True)

    rows_path = out_dir / "rows.jsonl"
    done_keys = set()
    prior_rows = []
    n_correct = n_wrong = n_answered = n_refused = n_empty = 0
    if rows_path.exists() and not args.overwrite:
        for ln in rows_path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            pr = json.loads(ln)
            if pr.get("config_sha") != config_sha:
                raise RuntimeError(
                    f"resume config_sha mismatch: {pr.get('config_sha')} "
                    f"!= {config_sha}")
            done_keys.add(pr["row_key"])
            prior_rows.append(pr)
            if pr.get("answered"):
                n_answered += 1
                if pr.get("correct"):
                    n_correct += 1
                else:
                    n_wrong += 1
            elif pr.get("refused"):
                n_refused += 1
            else:
                n_empty += 1
        print(f"[cd/{args.stage}] RESUME: {len(done_keys)} present "
              f"(correct={n_correct} wrong={n_wrong})", flush=True)

    written = len(done_keys)
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for pr in prior_rows:
            rows_fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
        rows_fh.flush()
        for item in pool:
            if item["row_key"] in done_keys:
                continue
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
                hs = out.hidden_states  # tuple len n_layers+1
                post_tensors = {
                    f"L{li}": hs[li][0, seq_end, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                safe_key = item["row_key"].replace("::", "__").replace("|", "_")
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
            if written % 25 == 0 or written == len(pool):
                print(f"[cd/{args.stage}] attempts={written} answered={n_answered} "
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
        "positions": ["post"],
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"\n[cd/{args.stage}] DONE answered={n_answered} correct={n_correct} "
          f"wrong={n_wrong} -> {out_dir}", flush=True)

    floor = args.adequacy_floor
    if n_correct < floor or n_wrong < floor:
        print(f"[cd/{args.stage}] WARNING: below CD-G0 floor ({floor}/{floor}); "
              f"correct={n_correct} wrong={n_wrong}. This is a DATA-STAGE "
              "stop for this stage ('rotation not measurable at this stage'), "
              "NOT a probe verdict.", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, choices=list(STAGE_TAGS))
    ap.add_argument("--base-model", required=True,
                    help="HF repo id (raw) or local merged-16bit dir (cleansft/partrue)")
    ap.add_argument("--adapter", default=None,
                    help="local LoRA adapter dir (final_model); omit for raw/cleansft")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--datasets-root", default=str(repo_root() / "datasets"))
    ap.add_argument("--datasets", nargs="+", default=["popqa", "triviaqa"],
                    choices=["popqa", "triviaqa"])
    ap.add_argument("--per-dataset", type=int, default=None)
    ap.add_argument("--target-correct", type=int, default=250)
    ap.add_argument("--target-wrong", type=int, default=250)
    ap.add_argument("--max-attempts", type=int, default=4000)
    ap.add_argument("--max-new-tokens", type=int, default=48)
    ap.add_argument("--adequacy-floor", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260719)
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
