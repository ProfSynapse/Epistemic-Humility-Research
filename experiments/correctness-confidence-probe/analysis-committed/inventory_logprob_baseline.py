#!/usr/bin/env python3
"""Inventory check: does the Amendment S (dial) cached extraction contain
per-token logprobs/logits, sufficient to derive an output-logprob baseline
for the correctness dial on the SAME scored population?

Read-only. Does not load any model, does not touch the GPU. Enumerates the
field set actually present in the cached rows.jsonl and the tensor key set
actually present in the cached safetensors files, and reports whether either
carries logit/logprob information.

Run from the canonical checkout (cached artifacts are gitignored and are not
present in a fresh worktree):
    python3 experiments/correctness-confidence-probe/analysis-committed/inventory_logprob_baseline.py \
        --stage2-dir experiment/phase1/probe/qwen3-4b-instruct/amendment_s/stage2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LOGPROB_MARKERS = ("logprob", "logit", "log_prob", "score")


def inspect_rows(rows_path: Path) -> tuple[set[str], int]:
    keys: set[str] = set()
    n = 0
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            keys |= set(json.loads(line).keys())
            n += 1
    return keys, n


def inspect_safetensors(path: Path) -> set[str]:
    from safetensors import safe_open
    with safe_open(str(path), framework="pt") as fh:
        return set(fh.keys())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage2-dir", required=True)
    args = ap.parse_args()

    stage2_dir = Path(args.stage2_dir).resolve()
    manifest = json.loads((stage2_dir / "manifest.json").read_text())
    row_keys, n_rows = inspect_rows(stage2_dir / "rows.jsonl")

    safetensors_files = sorted(stage2_dir.glob("*.safetensors"))
    tensor_keys: set[str] = set()
    if safetensors_files:
        tensor_keys = inspect_safetensors(safetensors_files[0])

    has_logprob_rows = any(
        any(m in k.lower() for m in LOGPROB_MARKERS) for k in row_keys
    )
    has_logprob_tensors = any(
        any(m in k.lower() for m in LOGPROB_MARKERS) for k in tensor_keys
    )

    report = {
        "stage2_dir": str(stage2_dir),
        "manifest_n_answered": manifest.get("n_answered"),
        "manifest_n_correct": manifest.get("n_correct"),
        "manifest_n_wrong": manifest.get("n_wrong"),
        "rows_jsonl_lines": n_rows,
        "rows_jsonl_fields": sorted(row_keys),
        "n_safetensors_files": len(safetensors_files),
        "safetensors_tensor_keys_sample": sorted(tensor_keys),
        "logprob_or_logit_field_present_in_rows": has_logprob_rows,
        "logprob_or_logit_field_present_in_tensors": has_logprob_tensors,
        "conclusion": (
            "COMPUTABLE" if (has_logprob_rows or has_logprob_tensors) else
            "NOT_COMPUTABLE_FROM_CACHE"
        ),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
