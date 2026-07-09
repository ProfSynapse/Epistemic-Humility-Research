#!/usr/bin/env python3
"""Amendment AF (script 1/4) — RAW-base pre-generation anchor extraction (GPU).

Pre-registered in
experiments/second-person-doubt-prime/AMENDMENT.md.
Tier-2 exploratory local mechanism evidence (RQ4, base-model substrate).

THE READ (protocol §3): the per-item doubt/answerability label AF renders to text
is a threshold on the base's OWN pre-generation read-out. This script produces the
raw material for that read: for each of the 600 frozen AE pool rows, render with
the BASELINE abstention-affording system prompt (byte-identical to AC/AE) and take
ONE forward pass (NO generation — the doubt label is a pre-generation read), saving
the hidden state at the pre-gen anchor position (prompt_len - 1, W's `pre`) for
every layer as fp32.

Surface mirrors amendment_w_base_model_extract.py: raw `unsloth/Qwen3-4B-bnb-4bit`,
NO adapter, bfloat16, device_map cuda, eval(), enable_thinking False.

Persists under a gitignored subtree:
  <out_dir>/rows.jsonl                    one record per pool row (row_key,label,question)
  <out_dir>/<safe_key>__pre.safetensors   {L0..L<N>} pre-gen anchor (fp32)
  <out_dir>/manifest.json                 run provenance + config
No training run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from path_compat import phase1_eval_dir, phase1_probe_dir  # noqa: E402

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME,
    MODEL_TAG,
    _config_sha,
)

# The BASELINE abstention-affording system prompt is read verbatim from the AC
# config so it is byte-identical to what the AC/AE runner used (protocol §3).
AC_CONFIG = (
    PROBE_DIR.parents[2]
    / "experiments/doubt-regulated-caution/phase3_ac_doubt_coupled_intervention.yaml"
)
DEFAULT_POOL = PROBE_DIR / "analysis" / "ae_base_pool" / "rows.jsonl"
DEFAULT_OUT = PROBE_DIR / "analysis" / "af_base_pregen"


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
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = load_baseline_system_prompt()
    pool = load_pool(pool_path)
    n_known = sum(1 for r in pool if r["label"] == "known")
    n_unknown = sum(1 for r in pool if r["label"] == "unknown")

    config_payload = {
        "amendment": "AF",
        "stage": "base_pregen_extract",
        "base_model": model_name,
        "adapter": "NONE-raw-instruct-base",
        "model_tag": MODEL_TAG,
        "system_prompt": system_prompt,
        "pool_source": str(pool_path),
        "enable_thinking": False,
        "anchor_position": "prompt_len-1",
        "persist_dtype": "float32",
        "generation": "NONE-forward-only",
    }
    config_sha = _config_sha(config_payload)

    print(f"[amendment-af/extract] loading RAW base {model_name} (no adapter) ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    print(f"[amendment-af/extract] pool={len(pool)} (known={n_known} "
          f"unknown={n_unknown}) n_layers={n_layers}", flush=True)

    rows_path = out_dir / "rows.jsonl"
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
                "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 50 == 0:
                print(f"[amendment-af/extract] rows={written}/{len(pool)}",
                      flush=True)

    manifest = {
        **config_payload,
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
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"\n[amendment-af/extract] DONE wrote {written} rows -> {out_dir}",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT),
                    help="output dir (gitignored)")
    ap.add_argument("--base-model", default=None,
                    help=f"raw Instruct base (default {MODEL_NAME}); NO adapter")
    ap.add_argument("--pool", default=str(DEFAULT_POOL),
                    help="frozen AE pool rows.jsonl (600 rows)")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
