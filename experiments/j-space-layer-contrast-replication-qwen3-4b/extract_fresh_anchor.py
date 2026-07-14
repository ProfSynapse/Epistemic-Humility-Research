#!/usr/bin/env python3
"""Extract prompt-anchor activations for the fresh J-space replication rows.

The fresh eval pool is private and lives under analysis/fresh_eval_rows.jsonl.
This script writes private safetensors anchor states for hs23/26/29/34. It does
not commit question text or activations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
ANALYSIS = HERE / "analysis"
RENDER_DIR = HERE.parent / "common" / "renders"
PROBE_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/archive/experiment/phase1/probe")
EVAL_DIR = PROBE_DIR.parent / "eval"

for p in (str(SOURCE), str(RENDER_DIR), str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from layers import HS_INDICES  # noqa: E402

MODEL_NAME = "unsloth/Qwen3-4B"
DEFAULT_ROWS = ANALYSIS / "fresh_eval_rows.jsonl"
DEFAULT_OUT = ANALYSIS / "fresh_anchor_extract.safetensors"
DEFAULT_MANIFEST = ANALYSIS / "fresh_anchor_extract_manifest.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def build_model():
    import torch
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=2048,
        dtype=torch.bfloat16,
        load_in_4bit=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def run(args: argparse.Namespace) -> int:
    import torch
    from safetensors.torch import save_file
    from ah_a0_raw_base_render import render

    rows_path = Path(args.rows).resolve()
    out_path = Path(args.out).resolve()
    manifest_path = Path(args.manifest).resolve()
    rows = load_jsonl(rows_path)
    if not rows:
        print(f"[extract-fresh] ERROR: no rows in {rows_path}", file=sys.stderr)
        return 1
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[extract-fresh] loading {MODEL_NAME} bf16 unsloth", flush=True)
    model, tokenizer = build_model()
    device = next(model.parameters()).device
    param_dtype = next(model.parameters()).dtype

    tensors = {}
    row_meta = []
    t0 = time.time()
    try:
        for idx, row in enumerate(rows, start=1):
            rendered = render(row)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                out = model(**enc, output_hidden_states=True, use_cache=False)
            hs = out.hidden_states
            safe = sanitize_key(row["row_key"])
            for hs_index in HS_INDICES:
                tensors[f"hs{hs_index}__{safe}"] = (
                    hs[hs_index][0, prompt_len - 1, :].float().cpu().contiguous()
                )
            row_meta.append({
                "row_key": row["row_key"],
                "role": row["role"],
                "source": row.get("source"),
                "category_canon": row.get("category_canon"),
                "prompt_len": prompt_len,
                "hs_tensor_keys": {str(h): f"hs{h}__{safe}" for h in HS_INDICES},
            })
            if idx % 50 == 0 or idx == len(rows):
                print(f"[extract-fresh] {idx}/{len(rows)}", flush=True)
    finally:
        del model
        torch.cuda.empty_cache()

    save_file(tensors, str(out_path))
    manifest = {
        "stage": "j_space_layer_contrast_replication_fresh_anchor_extract",
        "base_model": MODEL_NAME,
        "substrate": "bf16",
        "loader": "unsloth.FastLanguageModel",
        "torch_dtype": str(param_dtype),
        "layer_labels": [f"hs{h}" for h in HS_INDICES],
        "hidden_states_indices": HS_INDICES,
        "anchor_position": "prompt_len-1",
        "rows_path": str(rows_path),
        "rows_sha256": sha256_file(rows_path),
        "out_path": str(out_path),
        "n_rows_extracted": len(rows),
        "runtime_sec": round(time.time() - t0, 1),
        "rows": row_meta,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("stage", "n_rows_extracted", "runtime_sec")}, indent=2))
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", default=str(DEFAULT_ROWS))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
