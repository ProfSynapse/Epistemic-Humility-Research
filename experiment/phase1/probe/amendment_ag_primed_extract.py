#!/usr/bin/env python3
"""Amendment AG (script 2/3) — primed anchor extraction (GPU), §8 instrumentation.

Pre-registered in
experiments/oracle-dissociation-prime/AMENDMENT.md (§8).

Observational, GATE-FREE. For each of two renderings —
  high: every row gets PRIME_HIGH + " " + baseline system prompt
  low : every row gets PRIME_LOW  + " " + baseline system prompt
— run all 600 AE pool rows, capture the hidden state at position prompt_len−1
for ALL layers (the pre-gen anchor), and save per-row safetensors in the exact
format/naming of af_base_pregen (L0..LN keys, float32 cpu contiguous) so
downstream probe code can consume them without modification.

Outputs:
  analysis/ag_primed_pregen/high/<safe_key>__pre.safetensors
  analysis/ag_primed_pregen/high/rows.jsonl
  analysis/ag_primed_pregen/high/manifest.json
  analysis/ag_primed_pregen/low/  (same structure)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME,
    MODEL_TAG,
    _config_sha,
)

AC_CONFIG = (
    PROBE_DIR.parents[2]
    / "experiments/doubt-regulated-caution/phase3_ac_doubt_coupled_intervention.yaml"
)

# Frozen inputs from canonical checkout
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research/"
                 "experiment/phase1/probe")
DEFAULT_POOL = CANONICAL / "analysis" / "ae_base_pool" / "rows.jsonl"

# Output goes into the worktree
DEFAULT_OUT = PROBE_DIR / "analysis" / "ag_primed_pregen"

# Byte-identical prime sentences to AF
PRIME_HIGH = ("Your own prior knowledge of this question is reliable; answer it "
              "directly unless you truly cannot.")
PRIME_LOW = ("Your own prior knowledge of this question is unreliable; if you are "
             "not sure, say you don't know.")


def load_baseline_system_prompt() -> str:
    with AC_CONFIG.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg["prompt"]["system"]


def load_pool(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file

    model_name = args.base_model or MODEL_NAME
    pool_path = Path(args.pool).resolve()
    out_root = Path(args.out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    pool = load_pool(pool_path)
    n_known = sum(1 for r in pool if r["label"] == "known")
    n_unknown = sum(1 for r in pool if r["label"] == "unknown")

    # Two renderings: prime sentence + " " + baseline system
    renderings = {
        "high": PRIME_HIGH + " " + baseline_system,
        "low": PRIME_LOW + " " + baseline_system,
    }

    config_payload = {
        "amendment": "AG",
        "stage": "primed_pregen_extract",
        "base_model": model_name,
        "adapter": "NONE-raw-instruct-base",
        "model_tag": MODEL_TAG,
        "baseline_system_prompt": baseline_system,
        "prime_high": PRIME_HIGH,
        "prime_low": PRIME_LOW,
        "pool_source": str(pool_path),
        "enable_thinking": False,
        "anchor_position": "prompt_len-1",
        "persist_dtype": "float32",
        "generation": "NONE-forward-only",
        "renderings": ["high", "low"],
        "rendered_prompt_recipe": (
            "prime_sentence + single_space + baseline_system_prompt; "
            "high uses PRIME_HIGH, low uses PRIME_LOW"
        ),
    }
    config_sha = _config_sha(config_payload)

    print(f"[amendment-ag/extract] loading RAW base {model_name} (no adapter) ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    print(f"[amendment-ag/extract] pool={len(pool)} (known={n_known} "
          f"unknown={n_unknown}) n_layers={n_layers}", flush=True)

    for rendering_name, system_prompt in renderings.items():
        out_dir = out_root / rendering_name
        out_dir.mkdir(parents=True, exist_ok=True)
        rows_path = out_dir / "rows.jsonl"

        print(f"[amendment-ag/extract] starting rendering={rendering_name}", flush=True)
        written = 0
        with rows_path.open("w", encoding="utf-8") as rows_fh:
            for item in pool:
                row_key = item["row_key"]
                rendered, _mode = render_probe_prompt(
                    tokenizer, system_prompt, item["question"], enable_thinking=False)
                enc = tokenizer(rendered, return_tensors="pt").to(device)
                prompt_len = int(enc["input_ids"].shape[1])

                with torch.no_grad():
                    out = model(**enc, output_hidden_states=True, use_cache=False)
                hs = out.hidden_states
                # Exact mirror of af_base_pregen: L0..LN, prompt_len-1, float32, cpu
                pre_tensors = {
                    f"L{li}": hs[li][0, prompt_len - 1, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                safe_key = row_key.replace("::", "__").replace("|", "_")
                save_file(pre_tensors, str(out_dir / f"{safe_key}__pre.safetensors"))

                rows_fh.write(json.dumps({
                    "row_key": row_key,
                    "label": item["label"],
                    "question": item["question"],
                    "prompt_len": prompt_len,
                    "safe_key": safe_key,
                    "rendering": rendering_name,
                    "config_sha": config_sha,
                }, ensure_ascii=False) + "\n")
                rows_fh.flush()
                written += 1
                if written % 50 == 0:
                    print(f"[amendment-ag/extract] rendering={rendering_name} "
                          f"rows={written}/{len(pool)}", flush=True)

        manifest_r = {
            **config_payload,
            "rendering": rendering_name,
            "system_prompt_used": system_prompt,
            "config_sha": config_sha,
            "n_layers": n_layers,
            "hidden_dim": model.config.hidden_size,
            "n_pool": len(pool),
            "n_known": n_known,
            "n_unknown": n_unknown,
            "n_written": written,
            "out_dir": str(out_dir),
            "position": "pre",
            "tensor_layer_keys": f"L0..L{n_layers}",
        }
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest_r, indent=2), encoding="utf-8")
        print(f"[amendment-ag/extract] rendering={rendering_name} DONE "
              f"wrote {written} rows -> {out_dir}", flush=True)

    # Root manifest
    root_manifest = {
        **config_payload,
        "config_sha": config_sha,
        "n_pool": len(pool),
        "n_known": n_known,
        "n_unknown": n_unknown,
        "out_root": str(out_root),
    }
    (out_root / "manifest.json").write_text(
        json.dumps(root_manifest, indent=2), encoding="utf-8")
    print(json.dumps(root_manifest, indent=2), flush=True)
    print(f"\n[amendment-ag/extract] DONE both renderings -> {out_root}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--base-model", default=None,
                    help=f"raw Instruct base (default {MODEL_NAME}); NO adapter")
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
