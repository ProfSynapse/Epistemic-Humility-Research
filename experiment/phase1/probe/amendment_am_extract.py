#!/usr/bin/env python3
"""Amendment AM - A0-surface regeneration + dual-position extraction (GPU).

Pre-registered: experiment/protocol/AMENDMENT-AM-residual-catch-veto-coverage.md
(SIGNED 2026-07-06, §3 design, §5 preconditions). Tier-A exploratory cell;
results reported separately from PROTOCOL v0.3 and from the PR #205 veto numbers.

WHAT THIS DOES (one GPU pass, run inside the Modal container):
  1. Numerics smoke (§5.3): on a fixed 20-row subset, greedy-generate at batch-1
     AND at the registered batch (12, left-padded) and require TOKEN-LEVEL
     agreement on all 20 rows. On any divergence, bisect down 8/4/2/1 and record
     the largest agreeing batch as the frozen batch. Greedy decode is
     deterministic; left-padding must not change token output, so the smoke turns
     that invariant into a checked precondition before the full run.
  2. Full pass at the frozen batch: regenerate the A0 question pool on the RAW
     base (unsloth/Qwen3-4B-bnb-4bit, NO adapter) under the AH A0 surface
     (baseline abstention-affording system prompt, enable_thinking=false, greedy,
     max_new_tokens=96), pinned to the A0 config (config_sha 68847c8396f688d4).
  3. For every ANSWERED row, extract dual-position hidden states (pre = anchor at
     prompt_len-1, post = content-end token) for L0..L36, following
     amendment_w_base_model_extract.py, BUT on the A0 prompt surface (NOT
     Amendment S's prompt).
  4. Grade rows with the byte-pinned A0 grader (scorers.is_correct for answerable
     rows with aliases; scorers.is_stated_confidence_refusal for refusal;
     _content_end_index for the content span). Emit per-row provenance JSONL.

SURFACE PINNING (why this is a new cell, not a reuse):
  - The A0 rows were generated under the AH baseline system prompt (from
    config/phase3_ac_doubt_coupled_intervention.yaml prompt.system), 96 new
    tokens. Amendment W/S used a DIFFERENT (answer-encouraging) prompt at 48
    tokens. The correctness direction cold-transfers across surfaces at only
    ~0.679, so a valid veto number requires refitting on the A0 surface. This
    script produces the A0-surface activations; the CPU analysis
    (amendment_am_grade_and_gates.py) fits the veto out-of-fold and scores gates.

DETERMINISM: batch-1 greedy is the ground truth. Left-padded batched generation
must reproduce it token-for-token; the smoke enforces that. Extraction is a
single forward per answered row at batch-1 (deterministic), same cost as W.

Outputs (canonical, gitignored) under <out-dir>:
  rows.jsonl                            one record per pool row (graded)
  <safe_key>__pre.safetensors           {L0..L36} pre-gen anchor (fp32) [answered]
  <safe_key>__post.safetensors          {L0..L36} post-gen content token (fp32)
  manifest.json                         config + counts + smoke result + frozen batch
No training run. NO FalseQA text is emitted (the pool carries only the questions
already in the frozen A0 pool).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import yaml  # noqa: E402

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME, MODEL_TAG, _config_sha, _content_end_index,
)

# The A0 config_sha (from ah_main/manifest.json arm A0). The regenerated config
# payload must reproduce this SHA or the surface has drifted; fail loud if not.
A0_CONFIG_SHA = "68847c8396f688d4"
# Byte-frozen A0 surface: 96 new tokens, greedy, enable_thinking false.
MAX_NEW_TOKENS = 96
# The baseline system prompt is loaded from the same config the AH main run used.
AC_CONFIG = PROBE_DIR / "config" / "phase3_ac_doubt_coupled_intervention.yaml"
SMOKE_N = 20
BISECT_BATCHES = [12, 8, 4, 2, 1]  # registered batch first, then bisect down


def load_baseline_system_prompt() -> str:
    with AC_CONFIG.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg["prompt"]["system"]


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def _build_gen_kwargs(tokenizer, eos_for_gen):
    return dict(
        max_new_tokens=MAX_NEW_TOKENS, do_sample=False, num_beams=1,
        eos_token_id=eos_for_gen,
        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
    )


def _generate_batch(model, tokenizer, rendered_list, gen_kwargs, device):
    """Left-padded batched greedy generate. Returns list of new-token-id lists.

    Left padding is REQUIRED for correct batched decoder-only generation: the
    tokenizer's padding_side is set to 'left' by the caller so the real prompt
    tokens sit flush-right and the attention mask hides the pads.
    """
    import torch
    enc = tokenizer(rendered_list, return_tensors="pt", padding=True).to(device)
    in_len = int(enc["input_ids"].shape[1])
    with torch.no_grad():
        gen = model.generate(**enc, return_dict_in_generate=True, **gen_kwargs)
    seqs = gen.sequences  # (B, in_len + new)
    # With left padding the generated tokens start at column in_len for every row.
    return [seqs[i, in_len:].tolist() for i in range(seqs.shape[0])]


def _generate_single(model, tokenizer, rendered, gen_kwargs, device):
    """Batch-1 greedy generate (no padding). Returns (new_ids, prompt_len)."""
    import torch
    enc = tokenizer(rendered, return_tensors="pt").to(device)
    prompt_len = int(enc["input_ids"].shape[1])
    with torch.no_grad():
        gen = model.generate(**enc, return_dict_in_generate=True, **gen_kwargs)
    full = gen.sequences[0].tolist()
    return full[prompt_len:], prompt_len


def _strip_trailing_pad(ids, pad_id):
    """Batched greedy pads short rows on the right with pad_id after EOS.
    Batch-1 stops at EOS with no trailing pad. Compare on the pre-pad prefix."""
    out = list(ids)
    while out and out[-1] == pad_id:
        out.pop()
    return out


def run_smoke(model, tokenizer, pool, system_prompt, gen_kwargs, device, pad_id):
    """Return (frozen_batch, smoke_record). Token-level agreement batch-1 vs batch-N."""
    subset = pool[:min(SMOKE_N, len(pool))]
    rendered = [render_probe_prompt(tokenizer, system_prompt, it["question"],
                                    enable_thinking=False)[0] for it in subset]
    # batch-1 ground truth
    single = []
    for r in rendered:
        new_ids, _ = _generate_single(model, tokenizer, r, gen_kwargs, device)
        single.append(_strip_trailing_pad(new_ids, pad_id))

    smoke = {"performed": True, "n": len(subset), "batches_tried": [],
             "frozen_batch": None, "passed": None}
    orig_side = tokenizer.padding_side
    try:
        for B in BISECT_BATCHES:
            if B == 1:
                smoke["batches_tried"].append({"batch": 1, "agree": len(subset),
                                               "total": len(subset)})
                smoke["frozen_batch"] = 1
                smoke["passed"] = True
                break
            tokenizer.padding_side = "left"
            batched = []
            for i in range(0, len(rendered), B):
                chunk = rendered[i:i + B]
                batched.extend(_generate_batch(model, tokenizer, chunk,
                                               gen_kwargs, device))
            agree = sum(1 for a, b in zip(single, batched)
                        if a == _strip_trailing_pad(b, pad_id))
            smoke["batches_tried"].append({"batch": B, "agree": agree,
                                           "total": len(subset)})
            print(f"[am/extract] smoke batch={B}: {agree}/{len(subset)} agree",
                  flush=True)
            if agree == len(subset):
                smoke["frozen_batch"] = B
                smoke["passed"] = True
                break
    finally:
        tokenizer.padding_side = orig_side
    return smoke["frozen_batch"], smoke


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file

    model_name = args.base_model or MODEL_NAME
    pool_path = Path(args.pool).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    pool = load_jsonl(pool_path)
    if args.limit:
        pool = pool[:args.limit]

    # Reproduce the A0 config payload/SHA (arm A0 of ah_main). Must match.
    config_payload = {
        "amendment": "AH", "stage": "main_generate", "arm": "A0",
        "base_model": model_name, "adapter": "NONE-raw-instruct-base",
        "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
        "prime": None, "pool_source": str(pool_path), "enable_thinking": False,
        "max_new_tokens": MAX_NEW_TOKENS, "decode": "greedy",
    }
    config_sha = _config_sha(config_payload)
    if not args.skip_sha_check and config_sha != A0_CONFIG_SHA:
        raise RuntimeError(
            f"[am/extract] A0 surface drift: regenerated config_sha={config_sha} "
            f"!= A0 {A0_CONFIG_SHA}. The prompt/decode contract has changed; "
            "the veto would not be fit on the A0 surface. Refusing to proceed.")
    print(f"[am/extract] A0 surface config_sha={config_sha} (matches A0)",
          flush=True)

    print(f"[am/extract] loading RAW base {model_name} (no adapter) ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
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
    pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    gen_kwargs = _build_gen_kwargs(tokenizer, eos_for_gen)

    # --- §5.3 numerics smoke: freeze the batch that reproduces batch-1 -------
    frozen_batch, smoke = run_smoke(model, tokenizer, pool, baseline_system,
                                    gen_kwargs, device, pad_id)
    print(f"[am/extract] frozen_batch={frozen_batch} (smoke passed={smoke['passed']})",
          flush=True)
    if not smoke["passed"]:
        raise RuntimeError("[am/extract] numerics smoke failed at every batch; "
                           "cannot freeze a batch. Aborting before the full pass.")

    def grade_row(item, answer_text):
        refused = scorers.is_stated_confidence_refusal(answer_text)
        return refused

    rows_path = out_dir / "rows.jsonl"
    counts = {"answered": 0, "refused": 0, "ungradeable": 0, "correct": 0,
              "graded_answerable": 0, "confab_on_unanswerable": 0}
    n_extracted = 0
    t0 = time.time()

    # Full pass: batched left-padded generation at the frozen batch, then a
    # per-answered-row batch-1 forward for dual-position extraction.
    orig_side = tokenizer.padding_side
    tokenizer.padding_side = "left"
    written = 0
    try:
        with rows_path.open("w", encoding="utf-8") as rows_fh:
            for i in range(0, len(pool), frozen_batch):
                chunk = pool[i:i + frozen_batch]
                rendered = [render_probe_prompt(tokenizer, baseline_system,
                                                it["question"],
                                                enable_thinking=False)[0]
                            for it in chunk]
                if frozen_batch == 1:
                    new_ids_list = [_generate_single(model, tokenizer, rendered[0],
                                                     gen_kwargs, device)[0]]
                else:
                    new_ids_list = _generate_batch(model, tokenizer, rendered,
                                                   gen_kwargs, device)

                for item, new_ids in zip(chunk, new_ids_list):
                    new_ids = _strip_trailing_pad(new_ids, pad_id)
                    answer_text = tokenizer.decode(
                        new_ids, skip_special_tokens=True).strip()
                    refused = scorers.is_stated_confidence_refusal(answer_text)

                    # Rebuild the full sequence at batch-1 for exact content-end
                    # index + activation extraction (no padding ambiguity).
                    enc1 = tokenizer(
                        render_probe_prompt(tokenizer, baseline_system,
                                            item["question"],
                                            enable_thinking=False)[0],
                        return_tensors="pt").to(device)
                    prompt_len = int(enc1["input_ids"].shape[1])
                    full_list = enc1["input_ids"][0].tolist() + list(new_ids)
                    content_end = _content_end_index(full_list, prompt_len,
                                                     special_ids)
                    answered = ((content_end is not None) and bool(answer_text)
                                and not refused)
                    ungradeable = (not refused) and (not answered)

                    is_answerable = (item["gold_class"] == "answerable")
                    aliases = item.get("aliases", [])
                    correct = None
                    if is_answerable and aliases:
                        correct = bool(scorers.is_correct(answer_text, aliases))
                        counts["graded_answerable"] += 1
                        if correct:
                            counts["correct"] += 1
                    confab = bool(answered and (not is_answerable))

                    if answered:
                        counts["answered"] += 1
                    elif refused:
                        counts["refused"] += 1
                    else:
                        counts["ungradeable"] += 1
                    if confab:
                        counts["confab_on_unanswerable"] += 1

                    safe_key = item["safe_key"]
                    if answered:
                        seq_end = content_end
                        fwd_ids = torch.tensor(
                            full_list[: seq_end + 1], device=device).unsqueeze(0)
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
                        save_file(pre_tensors,
                                  str(out_dir / f"{safe_key}__pre.safetensors"))
                        save_file(post_tensors,
                                  str(out_dir / f"{safe_key}__post.safetensors"))
                        n_extracted += 1

                    rows_fh.write(json.dumps({
                        "row_key": item["row_key"], "safe_key": safe_key,
                        "question": item["question"],
                        "gold_class": item["gold_class"],
                        "category_canon": item.get("category_canon", ""),
                        "score_L24": item["score_L24"],
                        "answer_text": answer_text, "refused": refused,
                        "answered": answered, "ungradeable": ungradeable,
                        "correct": correct, "confab_on_unanswerable": confab,
                        "prompt_len": prompt_len,
                        "answer_tok_len": (content_end - prompt_len + 1)
                                          if content_end is not None else 0,
                        "config_sha": config_sha,
                    }, ensure_ascii=False) + "\n")
                    rows_fh.flush()
                    written += 1
                if written and (written % 100 == 0 or written >= len(pool)):
                    el = time.time() - t0
                    rate = written / el if el else 0
                    print(f"[am/extract] {written}/{len(pool)} {el:.0f}s "
                          f"({rate:.2f}/s) {counts}", flush=True)
    finally:
        tokenizer.padding_side = orig_side

    manifest = {
        **config_payload, "config_sha": config_sha,
        "n_layers": n_layers, "hidden_dim": model.config.hidden_size,
        "n_pool": len(pool), "n_written": written, "counts": counts,
        "n_extracted": n_extracted, "frozen_batch": frozen_batch,
        "numerics_smoke": smoke, "positions": ["pre", "post"],
        "tensor_layer_keys": f"L0..{n_layers}",
        "runtime_sec": round(time.time() - t0, 1), "out_dir": str(out_dir),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[am/extract] DONE answered={counts['answered']} extracted={n_extracted} "
          f"confab={counts['confab_on_unanswerable']} correct={counts['correct']} "
          f"-> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", required=True,
                    help="self-contained AM pool (amendment_am_build_pool.py output)")
    ap.add_argument("--base-model", default=None,
                    help=f"raw Instruct base (default {MODEL_NAME}); NO adapter")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=0,
                    help="smoke only: cap pool rows")
    ap.add_argument("--skip-sha-check", action="store_true",
                    help="smoke only: bypass the A0 config_sha guard")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
