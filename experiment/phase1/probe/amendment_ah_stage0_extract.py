#!/usr/bin/env python3
"""Amendment AH Stage-0 (script 3/4) — pre-generation anchor extraction (GPU).

Pre-registered in
experiments/divergent-pool-own-readout/AMENDMENT.md (§4 step 3).

Byte-identical to the frozen AF/AG pre-gen extraction surface:
  - raw base unsloth/Qwen3-4B-bnb-4bit, no adapter, bfloat16, cuda
  - BASELINE system prompt (no prime) -- the mining pass reads the UNPRIMED
    internal readout, exactly the surface the frozen probes were fit on
  - render_probe_prompt(..., enable_thinking=False)
  - forward-only (use_cache=False), anchor = position prompt_len-1
  - persist L0..LN float32 cpu, af_base_pregen naming (<safe_key>__pre.safetensors)

Batching: extraction has no decode-comparability constraint, so we batch with
LEFT padding (anchor = last real token = last column) for throughput. Before
trusting batched states we run a self-check on the first N rows: batched vs
single-row (batch=1, no padding) states must agree within float tolerance;
the check result is recorded in the manifest and printed. --batch-size 1
forces the single-row path (the AG-exact rendering) if the check ever fails.

Outputs (canonical checkout, gitignored):
  analysis/ah_stage0/pregen/<safe_key>__pre.safetensors
  analysis/ah_stage0/pregen/rows.jsonl
  analysis/ah_stage0/pregen/manifest.json
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
from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME, MODEL_TAG, _config_sha,
)

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AC_CONFIG = PROBE_DIR / "config" / "phase3_ac_doubt_coupled_intervention.yaml"
DEFAULT_POOL = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0/candidates.jsonl"
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0/pregen"


def load_baseline_system_prompt() -> str:
    with AC_CONFIG.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg["prompt"]["system"]


def load_pool(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def safe_key_for(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_")


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file

    model_name = args.base_model or MODEL_NAME
    pool_path = Path(args.pool).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    pool = load_pool(pool_path)
    if args.limit:
        pool = pool[: args.limit]

    config_payload = {
        "amendment": "AH", "stage": "stage0_pregen_extract",
        "base_model": model_name, "adapter": "NONE-raw-instruct-base",
        "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
        "prime": "NONE-baseline-only",
        "pool_source": str(pool_path), "enable_thinking": False,
        "anchor_position": "prompt_len-1", "persist_dtype": "float32",
        "generation": "NONE-forward-only", "batch_size": args.batch_size,
    }
    config_sha = _config_sha(config_payload)

    print(f"[ah/extract] loading RAW base {model_name} ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.padding_side = "left"  # anchor = last real token = last column
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    print(f"[ah/extract] pool={len(pool)} n_layers={n_layers} "
          f"batch_size={args.batch_size}", flush=True)

    # Pre-render every prompt once (deterministic rendering, batch-independent).
    rendered_all = []
    for item in pool:
        rendered, _mode = render_probe_prompt(
            tokenizer, baseline_system, item["question"], enable_thinking=False)
        rendered_all.append(rendered)

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
        # left padding => last column is the real anchor for every row
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        real_lens = enc["attention_mask"].sum(dim=1).tolist()
        batch_vecs = []
        for bi in range(len(batch_rendered)):
            vecs = {f"L{li}": hs[li][bi, -1, :].float().cpu().contiguous()
                    for li in range(len(hs))}
            batch_vecs.append((vecs, int(real_lens[bi])))
        return batch_vecs

    # --- Batched-vs-single equivalence check on the first N rows ---
    check_n = min(args.check_n, len(pool)) if args.batch_size > 1 else 0
    check = {"performed": bool(check_n), "n": check_n, "max_abs_diff_L24": None,
             "max_abs_diff_all": None, "tol": args.check_tol, "passed": None}
    if check_n:
        print(f"[ah/extract] equivalence check on first {check_n} rows ...",
              flush=True)
        singles = [single_anchor(rendered_all[i])[0] for i in range(check_n)]
        # batch them together (a single padded batch)
        batched = batched_anchor(rendered_all[:check_n])
        max_all = 0.0
        max_l24 = 0.0
        for i in range(check_n):
            for k in singles[i]:
                d = float((singles[i][k] - batched[i][0][k]).abs().max())
                max_all = max(max_all, d)
                if k == "L24":
                    max_l24 = max(max_l24, d)
        check["max_abs_diff_all"] = max_all
        check["max_abs_diff_L24"] = max_l24
        check["passed"] = bool(max_all <= args.check_tol)
        print(f"[ah/extract] equivalence: max_abs_diff_all={max_all:.4g} "
              f"L24={max_l24:.4g} tol={args.check_tol} "
              f"passed={check['passed']}", flush=True)
        if not check["passed"]:
            print("[ah/extract] EQUIVALENCE FAILED -> falling back to batch_size=1",
                  flush=True)
            args.batch_size = 1

    # --- Main extraction ---
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
                    "question": item["question"], "aliases": item.get("aliases", []),
                    "source": item["source"], "prompt_len": prompt_len,
                    "safe_key": sk, "config_sha": config_sha,
                }, ensure_ascii=False) + "\n")
                i += 1
                written += 1
            else:
                batch_items = pool[i:i + args.batch_size]
                batch_rendered = rendered_all[i:i + args.batch_size]
                bvecs = batched_anchor(batch_rendered)
                for bi, item in enumerate(batch_items):
                    vecs, real_len = bvecs[bi]
                    sk = safe_key_for(item["row_key"])
                    save_file(vecs, str(out_dir / f"{sk}__pre.safetensors"))
                    rows_fh.write(json.dumps({
                        "row_key": item["row_key"], "label": item["label"],
                        "question": item["question"],
                        "aliases": item.get("aliases", []),
                        "source": item["source"], "prompt_len": real_len,
                        "safe_key": sk, "config_sha": config_sha,
                    }, ensure_ascii=False) + "\n")
                    written += 1
                i += len(batch_items)
            rows_fh.flush()
            if written % 200 == 0 or i >= len(pool):
                el = time.time() - t0
                rate = written / el if el else 0
                print(f"[ah/extract] rows={written}/{len(pool)} "
                      f"{el:.0f}s ({rate:.1f}/s)", flush=True)

    runtime = time.time() - t0
    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size, "n_pool": len(pool),
        "n_written": written, "runtime_sec": round(runtime, 1),
        "equivalence_check": check, "out_dir": str(out_dir),
        "tensor_layer_keys": f"L0..L{n_layers}", "padding_side": "left",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[ah/extract] DONE {written} rows in {runtime:.0f}s -> {out_dir}",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    ap.add_argument("--base-model", default=None)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--check-n", type=int, default=20)
    ap.add_argument("--check-tol", type=float, default=2e-3)
    ap.add_argument("--limit", type=int, default=0, help="debug: cap pool size")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
