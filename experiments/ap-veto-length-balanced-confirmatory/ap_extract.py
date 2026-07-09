#!/usr/bin/env python3
"""Amendment AP - A0-surface regeneration + post-L20 extraction (GPU).

Pre-registered: experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md.
Confirmatory follow-up to Amendment AM
(experiments/residual-catch-veto-coverage/AMENDMENT.md). Tier-2
confirmatory cell; results reported separately from PROTOCOL v0.3 and from the
PR #205 published veto operating characteristics, and never pooled with AM.

WHAT THIS DOES (one GPU pass, run inside the Modal container). Ported
(logic, structure) from experiment/phase1/probe/amendment_am_extract.py
(read-only reference on the unmerged amendment-am branch; not imported across
branches), with exactly two deliberate surface changes per the AMENDMENT
Design section:
  1. max_new_tokens = 192 (up from AM's 96), so the 47% of AM's confabs that
     truncated at the 96-token cap now complete and `content_end` reflects the
     natural answer end.
  2. No residual-rule scalar (score_L24) anywhere in this pipeline: AP screens
     the BROADER hallucination-vs-good population, and the length-balanced
     construction happens downstream in `ap_grade_and_gates.py` via caliper
     matching on `answer_tok_len`, not via a pool-carried scalar.

Steps (identical structure to AM):
  1. Numerics smoke: on a fixed 20-row subset, greedy-generate at batch-1 AND
     at the registered batch (12, left-padded); require TOKEN-LEVEL agreement
     on all 20 rows. On any divergence, bisect down 8/4/2/1 and record the
     largest agreeing batch as the frozen batch.
  2. Full pass at the frozen batch: regenerate the A0 question pool on the RAW
     base (unsloth/Qwen3-4B-bnb-4bit, NO adapter) under the AH A0 surface
     (baseline abstention-affording system prompt, enable_thinking=false,
     greedy, max_new_tokens=192).
  3. For every ANSWERED row, extract dual-position hidden states (pre = anchor
     at prompt_len-1, post = content-end token) for L0..L36, following
     amendment_s_correctness_probe_extract.py / amendment_am_extract.py.
  4. Grade rows with the byte-pinned A0 grader (scorers.is_correct for
     answerable rows with aliases; scorers.is_stated_confidence_refusal for
     refusal; _content_end_index for the content span). Emit per-row
     provenance JSONL, including `hit_token_cap` (the row used the FULL
     max_new_tokens budget with no EOS -- the truncation flag AP exists to
     retire) and `answer_tok_len` (the caliper-matching variable downstream).

SURFACE PINNING: everything about the prompt/decode surface is IDENTICAL to
AM's A0 arm (model, adapter, system prompt, enable_thinking, decode=greedy)
except max_new_tokens. `AP_CONFIG_SHA` is the surface-contract hash of that
payload (amendment="AP", stage="ap_extract_192", max_new_tokens=192); it will
NOT equal AM's A0_CONFIG_SHA (14e5afab67484380) by construction (the extended
token budget is the whole point), so this script checks against its OWN pinned
sha, not AM's, and fails loud on any OTHER surface drift (model, prompt,
decode).

DETERMINISM: batch-1 greedy is the ground truth. Left-padded batched
generation must reproduce it token-for-token; the smoke enforces that.
Extraction is a single forward per answered row at batch-1 (deterministic).

Outputs (canonical, gitignored) under <out-dir>:
  rows.jsonl                            one record per pool row (graded)
  <safe_key>__pre.safetensors           {L0..L36} pre-gen anchor (fp32) [answered]
  <safe_key>__post.safetensors          {L0..L36} post-gen content token (fp32)
  manifest.json                         config + counts + smoke result + frozen batch
No training run. NO FalseQA text is emitted (the pool carries only the
questions already in the frozen A0 pool).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = REPO_ROOT / "experiment/phase1/probe"
EVAL_DIR = REPO_ROOT / "experiment/phase1/eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import yaml  # noqa: E402

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME, MODEL_TAG, _config_sha, _content_end_index,
)

# AP's own surface-contract sha: the config_payload below (AM's A0 payload
# minus the "arm" key, which AM used for AH multi-arm bookkeeping that AP has
# no equivalent of, plus max_new_tokens raised from 96 to 192, the one
# deliberate surface delta). Verified by hand before freezing this pin:
# AM's own A0 payload (WITH "arm": "A0", max_new_tokens=96) reproduces AM's
# pinned 14e5afab67484380 exactly through the identical `_config_sha` function,
# confirming the hash is stable and reproducible; this constant is the same
# function applied to AP's own payload shape below.
AP_CONFIG_SHA = "9d753f2348391187"
MAX_NEW_TOKENS = 192
# The baseline system prompt is loaded from the same config the AH main run
# used (AM's exact source; the AP AMENDMENT pins "the SAME ... generation
# surface as AM").
AC_CONFIG = (
    PROBE_DIR.parents[2]
    / "experiments/doubt-regulated-caution/phase3_ac_doubt_coupled_intervention.yaml"
)
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
            print(f"[ap/extract] smoke batch={B}: {agree}/{len(subset)} agree",
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

    # Reproduce the AP surface contract payload/sha (AM's A0 payload with
    # max_new_tokens raised to 192, the one deliberate delta). Must match.
    config_payload = {
        "amendment": "AP", "stage": "ap_extract_192",
        "base_model": model_name, "adapter": "NONE-raw-instruct-base",
        "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
        "prime": None, "enable_thinking": False,
        "max_new_tokens": MAX_NEW_TOKENS, "decode": "greedy",
    }
    config_sha = _config_sha(config_payload)
    if not args.skip_sha_check and config_sha != AP_CONFIG_SHA:
        raise RuntimeError(
            f"[ap/extract] AP surface drift: regenerated config_sha={config_sha} "
            f"!= AP {AP_CONFIG_SHA}. The prompt/decode contract has changed "
            "from the pinned AP surface. Refusing to proceed.")
    print(f"[ap/extract] AP surface config_sha={config_sha} (matches AP pin)",
          flush=True)

    print(f"[ap/extract] loading RAW base {model_name} (no adapter) ...", flush=True)
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

    # --- numerics smoke: freeze the batch that reproduces batch-1 -------
    frozen_batch, smoke = run_smoke(model, tokenizer, pool, baseline_system,
                                    gen_kwargs, device, pad_id)
    print(f"[ap/extract] frozen_batch={frozen_batch} (smoke passed={smoke['passed']})",
          flush=True)
    if not smoke["passed"]:
        raise RuntimeError("[ap/extract] numerics smoke failed at every batch; "
                           "cannot freeze a batch. Aborting before the full pass.")

    rows_path = out_dir / "rows.jsonl"
    counts = {"answered": 0, "refused": 0, "ungradeable": 0, "correct": 0,
              "graded_answerable": 0, "confab_on_unanswerable": 0,
              "hit_token_cap": 0}
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
                    # hit_token_cap: the model used the FULL budget with no EOS
                    # anywhere in the generated tail -- the truncation flag AP
                    # exists to retire (AM found 47% of confabs truncated at 96).
                    hit_token_cap = (len(new_ids) >= MAX_NEW_TOKENS
                                     and not any(int(t) in special_ids for t in new_ids))
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
                    if answered and hit_token_cap:
                        counts["hit_token_cap"] += 1

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
                        "answer_text": answer_text, "refused": refused,
                        "answered": answered, "ungradeable": ungradeable,
                        "correct": correct, "confab_on_unanswerable": confab,
                        "prompt_len": prompt_len,
                        "answer_tok_len": (content_end - prompt_len + 1)
                                          if content_end is not None else 0,
                        "hit_token_cap": bool(answered and hit_token_cap),
                        "config_sha": config_sha,
                    }, ensure_ascii=False) + "\n")
                    rows_fh.flush()
                    written += 1
                if written and (written % 100 == 0 or written >= len(pool)):
                    el = time.time() - t0
                    rate = written / el if el else 0
                    print(f"[ap/extract] {written}/{len(pool)} {el:.0f}s "
                          f"({rate:.2f}/s) {counts}", flush=True)
    finally:
        tokenizer.padding_side = orig_side

    manifest = {
        **config_payload, "config_sha": config_sha,
        "pool_source": str(pool_path),  # provenance only; excluded from surface sha
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
    print(f"[ap/extract] DONE answered={counts['answered']} extracted={n_extracted} "
          f"confab={counts['confab_on_unanswerable']} correct={counts['correct']} "
          f"hit_token_cap={counts['hit_token_cap']} -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", required=True,
                    help="self-contained AP pool (ap_build_pool.py output)")
    ap.add_argument("--base-model", default=None,
                    help=f"raw Instruct base (default {MODEL_NAME}); NO adapter")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=0,
                    help="smoke only: cap pool rows")
    ap.add_argument("--skip-sha-check", action="store_true",
                    help="smoke only: bypass the AP config_sha guard")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
