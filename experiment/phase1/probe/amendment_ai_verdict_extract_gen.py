#!/usr/bin/env python3
"""Amendment AI — verdict-eval GPU half (extraction + generation).

Produces the GPU-side inputs the CPU scorer (amendment_ai_verdict_score.py)
consumes for gates AI-G0/G1/G2. Written for the HF Jobs cloud lane; runs
through the clean-SFT merged base loaded in the 4-BIT SERVING configuration
with the arm's TRAINED LoRA adapter applied — the exact serving lineage the
PAR reward read (sensor v2, prereg section 1.1). Do not change the load path
or the render without re-checking the sensor-v2 provenance
(par_sensor_refit_extract_4bit.py) and the AH generation harness
(amendment_ah_main_generate.py); token-position / rendering mismatches have
burned this program before (Amendment R).

THREE JOBS in one entry (choose with --stage):

  --stage extract --surface union
      CELL A part 1. Pre-generation states (L20/L24/L28, final prompt token)
      for the union refit surface, through THIS arm's final checkpoint.
      Output dir feeds the scorer's --*-fit-states (Amendment T
      refit-per-checkpoint; the scorer excludes holdout row_keys from the
      fit). rows.jsonl carries row_key/safe_key/label (no question text).

  --stage extract --surface holdout
      CELL A part 2. Same pre-gen states for the 400 locked holdout rows.
      Feeds the scorer's --*-holdout-states.

  --stage generate
      CELL B. Greedy batch-1 generation on the 400 holdout rows through the
      arm's final checkpoint (schema contract, enable_thinking=False, refusal
      via scorers.is_stated_confidence_refusal). Output rows.jsonl feeds the
      scorer's --*-gen with row_key/refused/answered/schema_valid.

INPUT POOLS (passed as file paths; the cloud wrapper fetches them from the
PRIVATE staging dataset repo because the union surface is derived from
NO-LICENSE FalseQA source text that never enters the public repo). Each pool
line is one JSON object:
  union pool   : row_key, question, label ("known"|"unknown"), source
  holdout pool : row_key, question, gold_label, source (the pool build's
                 holdout_eval.jsonl schema; label is derived from gold_label)

FalseQA / NO-LICENSE handling: question text is read ONLY to render prompts.
It is NEVER written to any output file. Extraction rows.jsonl carries
row_key/safe_key/label/prompt_len/config_sha; generation rows.jsonl carries
row_key/refused/answered/schema_valid/degenerate/prompt_len/config_sha plus
answer_text (the MODEL's own emission, not source text) for audit.

Load path (byte-identical to par_sensor_refit_extract_4bit.py + the AI
trainer's serving config, with the TRAINED adapter instead of an identity
LoRA):
  FastLanguageModel.from_pretrained(clean-SFT merged, max_seq_length=2048,
    load_in_4bit=True)
  -> PeftModel.from_pretrained(model, adapter_repo, revision=...)  [TRAINED]
  -> FastLanguageModel.for_inference
  baseline unprimed system prompt, render_probe_prompt(enable_thinking=False),
  anchor = prompt_len-1, forward-only for extraction (use_cache=False),
  greedy batch-1 for generation (do_sample=False, num_beams=1,
  max_new_tokens=96 — the AH main-generate value).
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

from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_TAG, _config_sha, _content_end_index,
)
from amendment_ah_stage0_extract import (  # noqa: E402
    load_baseline_system_prompt, safe_key_for,
)

LAYERS = ("L20", "L24", "L28")
DEGEN_RUN = 12
MAX_NEW_TOKENS = 96
SPOT_CHECK_N = 3


def load_jsonl(p: Path):
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def is_degenerate(text: str) -> bool:
    if not text.strip():
        return True
    toks = text.split()
    run = 1
    for i in range(1, len(toks)):
        if toks[i] == toks[i - 1]:
            run += 1
            if run >= DEGEN_RUN:
                return True
        else:
            run = 1
    return False


def load_pool(pool_path: Path, surface: str) -> list[dict]:
    """Normalize an input pool to items with row_key/question/label.

    union pool lines carry `label`; holdout pool lines carry `gold_label`
    (the pool build's holdout_eval.jsonl schema) which we map to `label`.
    """
    rows = load_jsonl(pool_path)
    items = []
    for r in rows:
        label = r.get("label")
        if label is None:
            gold = r.get("gold_label")
            label = "unknown" if gold == "unknown" else "known"
        items.append({
            "row_key": r["row_key"], "question": r["question"],
            "label": label, "source": r.get("source", ""),
        })
    return items


def build_model(base_path: str, adapter_repo: str | None,
                adapter_revision: str | None):
    """Clean-SFT 4-bit serving config with the TRAINED adapter applied."""
    from unsloth import FastLanguageModel  # import first (patches transformers)
    from peft import PeftModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_path, max_seq_length=2048, dtype=None,
        load_in_4bit=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    if adapter_repo:
        # The arm's TRAINED LoRA (not the identity-at-init wrapper the sensor
        # extraction used): apply the real weights so the verdict measures the
        # trained policy. Adapter target modules / r / alpha travel in the
        # adapter's own config.
        model = PeftModel.from_pretrained(
            model, adapter_repo, revision=adapter_revision)
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def run_extract(args) -> int:
    import torch
    from safetensors.torch import save_file
    from backends import render_probe_prompt

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_system = load_baseline_system_prompt()
    pool = load_pool(Path(args.pool), args.surface)
    if args.limit:
        pool = pool[: args.limit]

    config_payload = {
        "stage": "amendment_ai_verdict_extract", "surface": args.surface,
        "base_model": args.base_model, "load_in_4bit": True,
        "adapter_repo": args.adapter_repo, "adapter_revision": args.adapter_revision,
        "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
        "prime": "NONE-baseline-only", "enable_thinking": False,
        "anchor_position": "prompt_len-1", "persist_dtype": "float32",
        "generation": "NONE-forward-only", "batch_size": 1,
        "layers": list(LAYERS),
    }
    config_sha = _config_sha(config_payload)

    print(f"[ai/verdict/extract] surface={args.surface} n={len(pool)} "
          f"adapter={args.adapter_repo}@{args.adapter_revision} "
          f"config_sha={config_sha}", flush=True)
    model, tokenizer = build_model(args.base_model, args.adapter_repo,
                                   args.adapter_revision)
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    for lk in LAYERS:
        li = int(lk[1:])
        if li > n_layers:
            raise RuntimeError(f"layer {lk} > n_layers {n_layers}")

    rendered_all = [render_probe_prompt(
        tokenizer, baseline_system, item["question"], enable_thinking=False)[0]
        for item in pool]

    def single_anchor(rendered: str):
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        vecs = {lk: hs[int(lk[1:])][0, prompt_len - 1, :].float().cpu().contiguous()
                for lk in LAYERS}
        return vecs, prompt_len

    # determinism spot-check (L24 re-forward bit-identical, threshold <= 1e-5)
    spot = {"performed": True, "n": min(SPOT_CHECK_N, len(pool)),
            "max_abs_diff_L24": None, "threshold": 1e-5, "passed": None}
    max_d = 0.0
    for i in range(spot["n"]):
        v1, _ = single_anchor(rendered_all[i])
        v2, _ = single_anchor(rendered_all[i])
        max_d = max(max_d, float((v1["L24"] - v2["L24"]).abs().max()))
    spot["max_abs_diff_L24"] = max_d
    spot["passed"] = bool(max_d <= 1e-5)
    print(f"[ai/verdict/extract] determinism max_abs_diff_L24={max_d:.4g} "
          f"passed={spot['passed']}", flush=True)

    # --- RESUME: skip safe_keys whose tensor already exists (batch-1 greedy-
    # deterministic forward is byte-identical to a fresh run). Rewrite the
    # rows.jsonl for present rows, then append the rest. ---
    done_keys = set()
    prior_rows = []
    rows_path = out_dir / "rows.jsonl"
    if rows_path.exists() and not args.overwrite:
        for ln in rows_path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                pr = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if pr.get("config_sha") != config_sha:
                raise RuntimeError(
                    f"resume config_sha mismatch: {pr.get('config_sha')} "
                    f"!= {config_sha}")
            if not (out_dir / f"{pr['safe_key']}__pre.safetensors").exists():
                continue
            done_keys.add(pr["row_key"])
            prior_rows.append(pr)
    if done_keys:
        print(f"[ai/verdict/extract] RESUME: {len(done_keys)} present, "
              f"{len(pool) - len(done_keys)} remaining", flush=True)

    t0 = time.time()
    written = len(done_keys)
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for pr in prior_rows:
            rows_fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
        rows_fh.flush()
        for i, item in enumerate(pool):
            if item["row_key"] in done_keys:
                continue
            vecs, prompt_len = single_anchor(rendered_all[i])
            sk = safe_key_for(item["row_key"])
            save_file(vecs, str(out_dir / f"{sk}__pre.safetensors"))
            rows_fh.write(json.dumps({
                "row_key": item["row_key"], "label": item["label"],
                "source": item["source"], "prompt_len": prompt_len,
                "safe_key": sk, "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")   # NO question text (NO-LICENSE safe)
            rows_fh.flush()
            written += 1
            if written % 500 == 0 or written == len(pool):
                el = time.time() - t0
                print(f"[ai/verdict/extract] {args.surface} {written}/{len(pool)} "
                      f"{el:.0f}s ({written/el:.1f}/s)", flush=True)

    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size, "n_pool": len(pool),
        "n_written": written, "determinism_spot_check": spot,
        "runtime_sec": round(time.time() - t0, 1), "out_dir": str(out_dir),
        "tensor_layer_keys": list(LAYERS),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[ai/verdict/extract] DONE {args.surface} {written} rows -> {out_dir}",
          flush=True)
    return 0


def run_generate(args) -> int:
    import torch
    import scorers
    from backends import render_probe_prompt

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_system = load_baseline_system_prompt()
    pool = load_pool(Path(args.pool), "holdout")
    if args.limit:
        pool = pool[: args.limit]

    config_payload = {
        "stage": "amendment_ai_verdict_generate", "surface": "holdout",
        "base_model": args.base_model, "load_in_4bit": True,
        "adapter_repo": args.adapter_repo, "adapter_revision": args.adapter_revision,
        "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
        "prime": "NONE-baseline-only", "enable_thinking": False,
        "decode": "greedy", "do_sample": False, "num_beams": 1,
        "max_new_tokens": MAX_NEW_TOKENS, "batch_size": 1,
    }
    config_sha = _config_sha(config_payload)

    print(f"[ai/verdict/generate] holdout n={len(pool)} "
          f"adapter={args.adapter_repo}@{args.adapter_revision} "
          f"config_sha={config_sha}", flush=True)
    model, tokenizer = build_model(args.base_model, args.adapter_repo,
                                   args.adapter_revision)
    device = next(model.parameters()).device

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

    rows_path = out_dir / "rows.jsonl"
    done_keys = set()
    prior_rows = []
    if rows_path.exists() and not args.overwrite:
        for ln in rows_path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                pr = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if pr.get("config_sha") != config_sha:
                raise RuntimeError(
                    f"resume config_sha mismatch: {pr.get('config_sha')} "
                    f"!= {config_sha}")
            done_keys.add(pr["row_key"])
            prior_rows.append(pr)
    if done_keys:
        print(f"[ai/verdict/generate] RESUME: {len(done_keys)} present, "
              f"{len(pool) - len(done_keys)} remaining", flush=True)

    counts = {"answered": 0, "refused": 0, "ungradeable": 0,
              "degenerate": 0, "schema_valid": 0}
    for pr in prior_rows:
        if pr.get("answered"):
            counts["answered"] += 1
        elif pr.get("refused"):
            counts["refused"] += 1
        else:
            counts["ungradeable"] += 1
        counts["degenerate"] += int(bool(pr.get("degenerate")))
        counts["schema_valid"] += int(bool(pr.get("schema_valid")))

    t0 = time.time()
    written = len(done_keys)
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for pr in prior_rows:
            rows_fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
        rows_fh.flush()
        for item in pool:
            if item["row_key"] in done_keys:
                continue
            rendered, _mode = render_probe_prompt(
                tokenizer, baseline_system, item["question"],
                enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                gen = model.generate(
                    **enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                    num_beams=1, eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True)
            full_list = gen.sequences[0].tolist()
            answer_text = tokenizer.decode(
                full_list[prompt_len:], skip_special_tokens=True).strip()

            refused = bool(scorers.is_stated_confidence_refusal(answer_text))
            content_end = _content_end_index(full_list, prompt_len, special_ids)
            answered = bool((content_end is not None) and bool(answer_text)
                            and not refused)
            # schema_valid: the required stated-confidence JSON parsed with the
            # answer+confidence keys (scorers.parse_stated_confidence returns a
            # non-None stated_confidence exactly when the schema is well-formed).
            parsed = scorers.parse_stated_confidence(answer_text)
            schema_valid = bool(parsed.stated_confidence is not None)
            degenerate = is_degenerate(answer_text)

            if answered:
                counts["answered"] += 1
            elif refused:
                counts["refused"] += 1
            else:
                counts["ungradeable"] += 1
            counts["degenerate"] += int(degenerate)
            counts["schema_valid"] += int(schema_valid)

            rows_fh.write(json.dumps({
                "row_key": item["row_key"], "safe_key": safe_key_for(item["row_key"]),
                "refused": refused, "answered": answered,
                "schema_valid": schema_valid, "degenerate": degenerate,
                "answer_text": answer_text,   # model emission (not source text)
                "prompt_len": prompt_len, "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 50 == 0 or written == len(pool):
                el = time.time() - t0
                print(f"[ai/verdict/generate] {written}/{len(pool)} {el:.0f}s "
                      f"({written/el:.2f}/s) {counts}", flush=True)

    manifest = {**config_payload, "config_sha": config_sha, "n_pool": len(pool),
                "n_written": written, "counts": counts,
                "runtime_sec": round(time.time() - t0, 1), "out_dir": str(out_dir)}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[ai/verdict/generate] DONE {written} rows -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, choices=["extract", "generate"])
    ap.add_argument("--surface", choices=["union", "holdout"],
                    help="required for --stage extract")
    ap.add_argument("--pool", required=True,
                    help="input pool jsonl (fetched from the private staging repo)")
    ap.add_argument("--base-model", required=True,
                    help="clean-SFT merged 16-bit base (HF repo id or local path)")
    ap.add_argument("--adapter-repo", default=None,
                    help="trained LoRA adapter HF repo id (the arm under eval)")
    ap.add_argument("--adapter-revision", default=None,
                    help="adapter repo revision/commit to pin")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)
    if args.stage == "extract" and not args.surface:
        ap.error("--stage extract requires --surface")
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.stage == "extract":
        return run_extract(args)
    return run_generate(args)


if __name__ == "__main__":
    sys.exit(main())
