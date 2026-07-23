#!/usr/bin/env python3
"""Extract prompt-anchor activations for one family's eval pool, at that
family's own resolved candidate layers.

Ported from `j-space-layer-contrast-replication-qwen3-4b/extract_fresh_anchor.py`
and `j-space-midband-write-sweep-qwen3-4b/extract_layer_sweep_anchor.py`,
generalized to read the checkpoint and candidate hs_indices from a family
config instead of hardcoding `unsloth/Qwen3-4B` and `HS_INDICES = [23, 26,
29, 34]`. Requires `jlens_profile.py --family <slug>` to have already
resolved that family's `band_selection` (midband_candidates_hs +
late_reference_hs) -- this script refuses to run on an unresolved family
rather than silently falling back to Qwen3-4B's own layer set.

Writes private per-row anchor safetensors + a JSON manifest under
`analysis/<family>/`. Does not commit question text or activations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from family_config import FAMILY_SLUGS, hs_indices, load_family  # noqa: E402
import model_lib as ml  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


FLUSH_EVERY = 50  # rows between durable safetensors+manifest flushes (kill-resume safety)


def run(args: argparse.Namespace) -> int:
    import torch
    from safetensors.torch import save_file, load_file

    family = args.family
    cfg = load_family(family)
    hs_list = hs_indices(cfg)  # raises if band_selection not yet resolved

    rows_path = Path(args.rows or (HERE / "analysis" / family / "eval_rows.jsonl"))
    out_path = Path(args.out or (HERE / "analysis" / family / "anchor_extract.safetensors"))
    manifest_path = Path(args.manifest or (HERE / "analysis" / family / "anchor_extract_manifest.json"))
    rows = load_jsonl(rows_path)
    if not rows:
        print(f"[extract-anchor:{family}] ERROR: no rows in {rows_path}", file=sys.stderr)
        return 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows_sha = sha256_file(rows_path)

    # Kill-resume: this is a per-row GPU forward loop that previously buffered
    # ALL rows in memory and wrote the safetensors + manifest only at the end,
    # so a kill lost the whole extraction. It now flushes durably every
    # FLUSH_EVERY rows and RESUMES from the last flush. Resume reuses an existing
    # partial extraction only when its fingerprint (rows_sha256 + candidate hs
    # set) matches; --fresh forces a clean restart. See experiment.yaml
    # instrument.persistence and experiments/common/README-runlog.md.
    tensors: dict[str, "torch.Tensor"] = {}
    row_meta: list[dict] = []
    done_keys: set[str] = set()
    if not args.fresh and out_path.is_file() and manifest_path.is_file():
        prev = json.loads(manifest_path.read_text())
        if prev.get("rows_sha256") == rows_sha and prev.get("hidden_states_indices") == hs_list:
            tensors = dict(load_file(str(out_path)))
            row_meta = list(prev.get("rows", []))
            done_keys = {rm["row_key"] for rm in row_meta}
            print(f"[extract-anchor:{family}] resume: {len(done_keys)} rows already "
                  f"extracted, {len(rows) - len(done_keys)} remaining", flush=True)
        else:
            print(f"[extract-anchor:{family}] existing extract has a different "
                  f"fingerprint (rows/layers changed); starting fresh", flush=True)

    print(f"[extract-anchor:{family}] loading {cfg['checkpoint']['repo']} bf16, "
          f"hs_indices={hs_list}", flush=True)
    model, tokenizer, hidden_size, n_layers = ml.load_model_and_tokenizer(family)
    device = next(model.parameters()).device
    param_dtype = next(model.parameters()).dtype
    assert max(hs_list) <= n_layers, (
        f"requested hs={hs_list} requires >= {max(hs_list)} hidden layers, got {n_layers}"
    )

    def write_manifest(complete: bool) -> dict:
        manifest = {
            "stage": "j_space_cross_family_layer_contrast_anchor_extract",
            "family": family, "base_model": cfg["checkpoint"]["repo"],
            "substrate": "bf16", "torch_dtype": str(param_dtype),
            "hidden_size": hidden_size, "n_hidden_layers": n_layers,
            "layer_labels": [f"hs{h}" for h in hs_list],
            "hidden_states_indices": hs_list, "anchor_position": "prompt_len-1",
            "rows_path": str(rows_path), "rows_sha256": rows_sha,
            "out_path": str(out_path), "n_rows_extracted": len(row_meta),
            "n_rows_total": len(rows), "complete": complete,
            "runtime_sec": round(time.time() - t0, 1), "rows": row_meta,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    t0 = time.time()
    since_flush = 0
    for idx, row in enumerate(rows, start=1):
        if row["row_key"] in done_keys:
            continue
        rendered = ml.render(family, tokenizer, row)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        safe = sanitize_key(row["row_key"])
        for hs_index in hs_list:
            tensors[f"hs{hs_index}__{safe}"] = (
                hs[hs_index][0, prompt_len - 1, :].float().cpu().contiguous()
            )
        row_meta.append({
            "row_key": row["row_key"], "role": row["role"],
            "category_canon": row.get("category_canon"), "prompt_len": prompt_len,
        })
        since_flush += 1
        if since_flush >= FLUSH_EVERY:
            save_file(tensors, str(out_path))  # durable checkpoint
            write_manifest(complete=False)
            since_flush = 0
        if idx % 50 == 0 or idx == len(rows):
            print(f"[extract-anchor:{family}] {idx}/{len(rows)} "
                  f"(extracted {len(row_meta)})", flush=True)

    save_file(tensors, str(out_path))
    manifest = write_manifest(complete=True)
    print(json.dumps({k: manifest[k] for k in ("stage", "family", "n_rows_extracted",
                                                "runtime_sec")}, indent=2))
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--fresh", action="store_true",
                    help="Ignore any existing partial extraction and restart from row 0 "
                         "(default: resume from the last durable flush if the fingerprint matches).")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
