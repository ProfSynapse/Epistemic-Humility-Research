#!/usr/bin/env python3
"""PAR sensor-refit v2 — 4-bit SERVING pre-gen extraction (GPU).

Team-lead sensor-v2 order (commit 89bd7bce): the v1 sensor was fit on bf16
un-quantized-base pre-gen states, but the PAR reward reads the model AS SERVED
in training — unsloth FastLanguageModel load_in_4bit=True with the train-time
LoRA (identity at init) applied and for_inference. The smoke's criterion 2
exposed the gap (one union row: 4-bit-served p 0.97 vs bf16-fit p 2e-5). This
re-extracts L20/L24/L28 (+ all layers) pre-gen anchor states from the SERVING
model so par_sensor_refit_fit.py --variant v2 can refit the sensor on the exact
distribution the reward reads.

Load path is byte-identical to amendment_ai_smoke.py:
  FastLanguageModel.from_pretrained(clean-SFT merged, max_seq_length=2048,
    load_in_4bit=True) -> get_peft_model(r=32, alpha=64, dropout=0.05,
    the 7 attn/mlp target modules, gsc="unsloth", random_state=1)
  -> FastLanguageModel.for_inference. Baseline unprimed system prompt,
  render_probe_prompt(enable_thinking=False), anchor = prompt_len-1,
  forward-only (use_cache=False), persist L0..LN float32.

Surfaces -> the v2 input dirs par_sensor_refit_fit.py expects:
  union  -> analysis/par_sensor_refit/union_pregen_4bit/   (18,496 rows)
  mining -> analysis/par_sensor_refit/mining_pregen_4bit/  (9,397 rows)

Determinism spot-check (3 rows, L24 re-forward bit-identical) as in the v1
extractor. Batch-1 only (unsloth for_inference single-sequence forward; matches
the smoke's per-prompt read exactly — no left-pad batching gap). FalseQA text is
input-only and lands solely in the gitignored rows.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent
for p in (str(PROBE_DIR),):
    if p not in sys.path:
        sys.path.insert(0, p)

from amendment_s_correctness_probe_extract import MODEL_TAG, _config_sha  # noqa: E402
from amendment_ah_stage0_extract import (  # noqa: E402
    load_baseline_system_prompt, load_pool, safe_key_for,
)
from par_sensor_refit_extract import build_union_pool, MINING_ALL  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
CLEAN_SFT_BASE = (CANONICAL / "scratch/schema_response_confidence/runs/"
                  "sft_schema_clean_seed1_full/20260623_123624/"
                  "Qwen3-4B-bnb-4bit/merged-16bit")
REFIT_DIR = PROBE_ROOT / "analysis/par_sensor_refit"

SURFACES = {
    "union": {"out": REFIT_DIR / "union_pregen_4bit", "expected": 18496},
    "mining": {"out": REFIT_DIR / "mining_pregen_4bit", "expected": 9397},
}
SPOT_CHECK_N = 3


def run(args) -> int:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    from unsloth import FastLanguageModel  # import first (patches transformers)
    import torch
    from safetensors.torch import save_file
    from backends import render_probe_prompt

    surface = args.surface
    spec = SURFACES[surface]
    out_dir = Path(args.out_dir or spec["out"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base_path = Path(args.base_model).resolve()

    baseline_system = load_baseline_system_prompt()
    pool = build_union_pool() if surface == "union" else load_pool(MINING_ALL)
    if args.limit:
        pool = pool[: args.limit]
    if not args.skip_count_check and len(pool) != spec["expected"]:
        raise RuntimeError(f"{surface} pool={len(pool)} expected {spec['expected']}")

    config_payload = {
        "stage": "par_sensor_refit_pregen_4bit_serving", "surface": surface,
        "base_model": str(base_path), "load_in_4bit": True,
        "lora": "train-time r32 a64 identity-at-init, for_inference",
        "adapter": "clean-sft + fresh GRPO LoRA (identity)", "model_tag": MODEL_TAG,
        "baseline_system_prompt": baseline_system, "prime": "NONE-baseline-only",
        "enable_thinking": False, "anchor_position": "prompt_len-1",
        "persist_dtype": "float32", "generation": "NONE-forward-only",
        "batch_size": 1,
    }
    config_sha = _config_sha(config_payload)

    print(f"[par/refit4bit] surface={surface} loading SERVING clean-SFT "
          f"(4-bit + train-time LoRA) {base_path} ...", flush=True)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(base_path), max_seq_length=2048, dtype=None, load_in_4bit=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = FastLanguageModel.get_peft_model(
        model, r=32, lora_alpha=64, lora_dropout=0.05, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth", random_state=1)
    FastLanguageModel.for_inference(model)
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    print(f"[par/refit4bit] pool={len(pool)} n_layers={n_layers} "
          f"config_sha={config_sha}", flush=True)

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

    # determinism spot-check (L24 re-forward bit-identical)
    spot = {"performed": True, "n": min(SPOT_CHECK_N, len(pool)),
            "max_abs_diff_L24": None, "passed": None}
    max_d = 0.0
    for i in range(spot["n"]):
        v1, _ = single_anchor(rendered_all[i])
        v2, _ = single_anchor(rendered_all[i])
        max_d = max(max_d, float((v1["L24"] - v2["L24"]).abs().max()))
    spot["max_abs_diff_L24"] = max_d
    spot["passed"] = bool(max_d == 0.0)
    print(f"[par/refit4bit] determinism spot-check max_abs_diff_L24={max_d:.4g} "
          f"passed={spot['passed']}", flush=True)

    rows_path = out_dir / "rows.jsonl"
    t0 = time.time()
    written = 0
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for i, item in enumerate(pool):
            vecs, prompt_len = single_anchor(rendered_all[i])
            sk = safe_key_for(item["row_key"])
            save_file(vecs, str(out_dir / f"{sk}__pre.safetensors"))
            rows_fh.write(json.dumps({
                "row_key": item["row_key"], "label": item["label"],
                "question": item["question"], "source": item["source"],
                "prompt_len": prompt_len, "safe_key": sk, "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 500 == 0 or written == len(pool):
                el = time.time() - t0
                print(f"[par/refit4bit] {surface} {written}/{len(pool)} {el:.0f}s "
                      f"({written/el:.1f}/s)", flush=True)

    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size, "n_pool": len(pool),
        "n_written": written, "determinism_spot_check": spot,
        "runtime_sec": round(time.time() - t0, 1), "out_dir": str(out_dir),
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[par/refit4bit] DONE {surface} {written} rows -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--surface", required=True, choices=list(SURFACES))
    ap.add_argument("--base-model", default=str(CLEAN_SFT_BASE))
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-count-check", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
