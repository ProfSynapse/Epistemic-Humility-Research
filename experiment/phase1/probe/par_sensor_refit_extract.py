#!/usr/bin/env python3
"""PAR sensor-refit extraction (GPU) — clean-SFT checkpoint pre-gen states.

Team-lead overnight order, branch par-mining-recalibration. PASS-2 recalibration
showed the frozen raw-base AF-600 probe is BLIND on the trained lineage
(p_unanswerable ~ 1.0 on 99.9% of GRPO-v2 states), so the PAR sensor must be
refit on the TRAINING-START checkpoint. This extracts L20/L24/L28 (+ all layers)
pre-generation anchor states on the CLEAN-SFT merged-16bit base (NO adapter) for
the surfaces the refit will use:

  EXTRACTION A: the full 18,496-row AH union surface (5,000 mined + 13,496
                expansion), assembled via amendment_ah_stage0_expand_pool.build_union
                -> analysis/par_sensor_refit/union_pregen/
  EXTRACTION B: the 9,397 mining candidates (v1 300 + v2 9,097)
                -> analysis/par_sensor_refit/mining_pregen/

Recipe is byte-identical to the frozen AH stage-0 raw-base extraction
(amendment_ah_stage0_extract) EXCEPT the base model is the clean-SFT merged
checkpoint instead of the raw instruct base:
  - BASELINE (unprimed) system prompt from the AC config (same unprimed surface
    the frozen probes were fit on)
  - render_probe_prompt(..., enable_thinking=False)
  - forward-only (use_cache=False), anchor = position prompt_len-1
  - persist L0..LN float32 cpu, <safe_key>__pre.safetensors
  - batched with LEFT padding + a batched-vs-single equivalence self-check that
    falls back to batch-1 (the AG-exact path) if states diverge beyond tol.

No stored raw-base reference exists on this checkpoint, so instead of an identity
guard we record config_sha and run a 3-row DETERMINISTIC re-forward spot-check:
each of 3 rows is forwarded twice and the two L24 vectors must match bit-for-bit
(cos == 1 / max_abs_diff == 0) — a determinism sanity check on the load.

FalseQA rows (source falseqa_*) are NO-LICENSE (use-only): their question text
is read to render prompts (input) and written to the gitignored rows.jsonl under
analysis/, but MUST NOT appear in any committed file. The committed manifest here
carries counts / config_sha only, no row text.
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

from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import MODEL_TAG, _config_sha  # noqa: E402
from amendment_ah_stage0_extract import (  # noqa: E402
    load_baseline_system_prompt, load_pool, safe_key_for,
)

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
CLEAN_SFT_BASE = (CANONICAL / "scratch/schema_response_confidence/runs/"
                  "sft_schema_clean_seed1_full/20260623_123624/"
                  "Qwen3-4B-bnb-4bit/merged-16bit")
PAR_DESIGN = PROBE_ROOT / "analysis/par_design"
MINING_ALL = PAR_DESIGN / "mining_candidates_all.jsonl"
REFIT_DIR = PROBE_ROOT / "analysis/par_sensor_refit"

SURFACES = {
    "union": {"out": REFIT_DIR / "union_pregen", "expected": 18496},
    "mining": {"out": REFIT_DIR / "mining_pregen", "expected": 9397},
}
SPOT_CHECK_N = 3  # deterministic re-forward rows


def build_union_pool():
    """The 18,496-row AH union surface as extraction items (row_key/label/
    question/source), from the same builder pool_v21 was assembled over."""
    from amendment_ah_stage0_expand_pool import build_union
    union, _base_sd, _cv, _sign = build_union()
    return [{"row_key": r["row_key"], "label": r["label"],
             "question": r["question"], "source": r["source"],
             "aliases": []} for r in union]


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file

    surface = args.surface
    spec = SURFACES[surface]
    out_dir = Path(args.out_dir or spec["out"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base_path = Path(args.base_model).resolve()

    baseline_system = load_baseline_system_prompt()
    if surface == "union":
        pool = build_union_pool()
    else:
        pool = load_pool(MINING_ALL)
    if args.limit:
        pool = pool[: args.limit]
    if not args.skip_count_check and len(pool) != spec["expected"]:
        raise RuntimeError(f"{surface} pool={len(pool)} expected {spec['expected']}")

    config_payload = {
        "stage": "par_sensor_refit_pregen", "surface": surface,
        "base_model": str(base_path), "adapter": "NONE-clean-sft-merged-base",
        "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
        "prime": "NONE-baseline-only", "enable_thinking": False,
        "anchor_position": "prompt_len-1", "persist_dtype": "float32",
        "generation": "NONE-forward-only", "batch_size": args.batch_size,
    }
    config_sha = _config_sha(config_payload)

    print(f"[par/refit] surface={surface} loading clean-SFT base {base_path} ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(str(base_path))
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        str(base_path), torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    print(f"[par/refit] pool={len(pool)} n_layers={n_layers} "
          f"batch_size={args.batch_size} config_sha={config_sha}", flush=True)

    rendered_all = [render_probe_prompt(
        tokenizer, baseline_system, item["question"], enable_thinking=False)[0]
        for item in pool]

    def single_anchor(rendered: str):
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        vecs = {f"L{li}": hs[li][0, prompt_len - 1, :].float().cpu().contiguous()
                for li in range(len(hs))}
        return vecs, prompt_len

    def batched_anchor(batch_rendered):
        enc = tokenizer(batch_rendered, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        batch_vecs = []
        for bi in range(len(batch_rendered)):
            vecs = {f"L{li}": hs[li][bi, -1, :].float().cpu().contiguous()
                    for li in range(len(hs))}
            batch_vecs.append((vecs, None))
        return batch_vecs

    # --- deterministic re-forward spot-check (3 rows, L24 must be bit-identical) ---
    spot = {"performed": True, "n": min(SPOT_CHECK_N, len(pool)),
            "max_abs_diff_L24": None, "passed": None}
    max_d = 0.0
    for i in range(spot["n"]):
        v1, _ = single_anchor(rendered_all[i])
        v2, _ = single_anchor(rendered_all[i])
        max_d = max(max_d, float((v1["L24"] - v2["L24"]).abs().max()))
    spot["max_abs_diff_L24"] = max_d
    spot["passed"] = bool(max_d == 0.0)
    print(f"[par/refit] determinism spot-check max_abs_diff_L24={max_d:.4g} "
          f"passed={spot['passed']}", flush=True)

    # --- batched-vs-single equivalence check (throughput guard) ---
    check_n = min(args.check_n, len(pool)) if args.batch_size > 1 else 0
    check = {"performed": bool(check_n), "n": check_n, "max_abs_diff_all": None,
             "max_abs_diff_L24": None, "tol": args.check_tol, "passed": None}
    if check_n:
        singles = [single_anchor(rendered_all[i])[0] for i in range(check_n)]
        batched = batched_anchor(rendered_all[:check_n])
        max_all = max_l24 = 0.0
        for i in range(check_n):
            for k in singles[i]:
                d = float((singles[i][k] - batched[i][0][k]).abs().max())
                max_all = max(max_all, d)
                if k == "L24":
                    max_l24 = max(max_l24, d)
        check.update(max_abs_diff_all=max_all, max_abs_diff_L24=max_l24,
                     passed=bool(max_all <= args.check_tol))
        print(f"[par/refit] equivalence max_abs_diff_all={max_all:.4g} "
              f"L24={max_l24:.4g} tol={args.check_tol} passed={check['passed']}",
              flush=True)
        if not check["passed"]:
            print("[par/refit] EQUIVALENCE FAILED -> falling back to batch_size=1",
                  flush=True)
            args.batch_size = 1

    # --- main extraction ---
    rows_path = out_dir / "rows.jsonl"
    t0 = time.time()
    written = 0
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        i = 0
        while i < len(pool):
            if args.batch_size <= 1:
                item = pool[i]
                vecs, prompt_len = single_anchor(rendered_all[i])
                sk = safe_key_for(item["row_key"])
                save_file(vecs, str(out_dir / f"{sk}__pre.safetensors"))
                rows_fh.write(json.dumps({
                    "row_key": item["row_key"], "label": item["label"],
                    "question": item["question"], "source": item["source"],
                    "prompt_len": prompt_len, "safe_key": sk,
                    "config_sha": config_sha,
                }, ensure_ascii=False) + "\n")
                i += 1
                written += 1
            else:
                batch_items = pool[i:i + args.batch_size]
                bvecs = batched_anchor(rendered_all[i:i + args.batch_size])
                for bi, item in enumerate(batch_items):
                    vecs, _ = bvecs[bi]
                    sk = safe_key_for(item["row_key"])
                    save_file(vecs, str(out_dir / f"{sk}__pre.safetensors"))
                    # prompt_len from a cheap single tokenize (no forward)
                    plen = int(tokenizer(rendered_all[i + bi],
                                         return_tensors="pt")["input_ids"].shape[1])
                    rows_fh.write(json.dumps({
                        "row_key": item["row_key"], "label": item["label"],
                        "question": item["question"], "source": item["source"],
                        "prompt_len": plen, "safe_key": sk,
                        "config_sha": config_sha,
                    }, ensure_ascii=False) + "\n")
                    written += 1
                i += len(batch_items)
            rows_fh.flush()
            if written % 500 == 0 or i >= len(pool):
                el = time.time() - t0
                print(f"[par/refit] {surface} {written}/{len(pool)} {el:.0f}s "
                      f"({written/el:.1f}/s)", flush=True)

    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size, "n_pool": len(pool),
        "n_written": written, "determinism_spot_check": spot,
        "equivalence_check": check, "runtime_sec": round(time.time() - t0, 1),
        "out_dir": str(out_dir), "tensor_layer_keys": f"L0..L{n_layers}",
        "padding_side": "left",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[par/refit] DONE {surface} {written} rows -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--surface", required=True, choices=list(SURFACES))
    ap.add_argument("--base-model", default=str(CLEAN_SFT_BASE))
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--check-n", type=int, default=20)
    ap.add_argument("--check-tol", type=float, default=2e-3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-count-check", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
