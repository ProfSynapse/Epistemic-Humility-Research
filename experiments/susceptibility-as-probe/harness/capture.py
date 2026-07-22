#!/usr/bin/env python3
"""SC1 capture: hs20 anchor extraction + frozen-c_hat readout z-score for
susceptibility-as-probe (M2).

GPU. Renders each row via `render.py` (baseline JSON-answer stack, atlas
conventions), tokenizes manually (`add_special_tokens=True`), computes the
anchor position as `len(token_ids) - 1`, and invokes synaptic-tuner's
`batch-capture` (engine hf-batched, `--layers 20` = the single hs_index this
cell needs, persist_dtype float32, resume-safe) to extract ONLY the anchor
hidden state at hs_index 20 (decoder block 19) for every row. No steering, no
interventions, no generation -- read-only mapping capture, mirroring
`.skills/family-atlas/scripts/capture_family_atlas_cell.py`'s own
`batch-capture` invocation shape.

Readout z-score: z = dot(h_anchor, c_hat.vector) / c_hat.sigma (c_hat.json's
own `mu` field is the all-zero hidden-state-space centering vector the
direction-record schema always writes when no centering was fit; `intercept`
is always 0.0; per the task directive "its json carries the normalization;
NO refit" -- no additional mu_c/sigma_c pair from any OTHER file, and no
threshold, is applied here). NOT necessarily the same sign convention as the
`neg_z_d` doubt-gate score reported in the amendment's Decision record item
5 anchor citation (see harness run notes) -- c_hat is fit as an
orthogonalized "snap write" direction, not itself given a committed AUC in
this or any prior amendment; the raw z-projection is used unmodified and the
readout AUROC is computed treating role=='confab' as the positive class,
consistent with every other channel's convention (confidence/susceptibility
both already orient "higher score = more confab-like").
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import population as population_mod  # noqa: E402

REPO_ROOT = config.REPO_ROOT
TUNER = REPO_ROOT / "synaptic-tuner" / "tuner.py"
STAGED = config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / config.FAMILY


def _sh(cmd: list[str]) -> None:
    print(f"[m2-capture] $ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def render_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Render + tokenize every row for the capture pass. Returns
    (capture_rows for batch-capture, template_sha256 of the byte-identical
    system-prompt+template contract -- used for the capture manifest's
    template hash field)."""
    os.environ["M2_CAPTURE_RENDER_MODEL"] = config.MODEL_REPO
    os.environ["M2_CAPTURE_RENDER_REVISION"] = config.MODEL_REVISION
    import render  # noqa: E402  (imported after env vars set; module caches tokenizer lazily)

    tok = render._tokenizer()
    cap_rows: list[dict[str, Any]] = []
    for row in rows:
        prompt = render.render(row)
        token_ids = tok(prompt, add_special_tokens=config.READOUT_ADD_SPECIAL_TOKENS)["input_ids"]
        cap_rows.append({
            "id": row["row_key"],
            "token_ids": token_ids,
            "positions": {"anchor": len(token_ids) - 1},
            "role": row["role"],
            "expected_token_count": len(token_ids),
        })
    template_sha256 = common.sha256_of_bytes(render.BASELINE_SYSTEM_PROMPT.encode("utf-8"))
    return cap_rows, template_sha256


def run_capture(cap_rows: list[dict[str, Any]], out_dir: Path, batch_size: int) -> None:
    cap_in = out_dir / "capture_rows.jsonl"
    common.write_jsonl(cap_in, cap_rows)
    _sh([
        sys.executable, str(TUNER), "batch-capture",
        "--rows", str(cap_in),
        "--model", config.MODEL_REPO,
        "--model-revision", config.MODEL_REVISION,
        "--out-dir", str(out_dir / "capture"),
        "--engine", config.READOUT_ENGINE,
        "--layers", str(config.READOUT_HS_INDEX),
        "--persist-dtype", config.READOUT_PERSIST_DTYPE,
        "--batch-size", str(batch_size),
        "--resume",
    ])


def load_c_hat() -> dict[str, Any]:
    return common.load_json(STAGED / "directions" / "hs20" / "c_hat.json")


def verify_capture_integrity(cap_rows: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    """Per-row token-count and anchor-position assertions; zero silent
    drops."""
    index = common.load_jsonl(out_dir / "capture" / "capture.jsonl")
    index_by_id = {r["id"]: r for r in index}
    expected_ids = {r["id"] for r in cap_rows}
    captured_ids = set(index_by_id.keys())
    missing = sorted(expected_ids - captured_ids)
    extra = sorted(captured_ids - expected_ids)
    bad_position: list[str] = []
    bad_layer: list[str] = []
    for r in cap_rows:
        rec = index_by_id.get(r["id"])
        if rec is None:
            continue
        if rec["positions"].get("anchor") != r["positions"]["anchor"]:
            bad_position.append(r["id"])
        if rec.get("n_layers") != 1 or rec.get("hidden_dim") != config.READOUT_HIDDEN_DIM:
            bad_layer.append(r["id"])
    return {
        "n_expected": len(expected_ids), "n_captured": len(captured_ids),
        "n_missing": len(missing), "missing_sample": missing[:10],
        "n_extra": len(extra), "extra_sample": extra[:10],
        "n_bad_position": len(bad_position), "bad_position_sample": bad_position[:10],
        "n_bad_layer_shape": len(bad_layer), "bad_layer_shape_sample": bad_layer[:10],
        "zero_silent_drops": len(missing) == 0 and len(extra) == 0,
        "all_positions_match": len(bad_position) == 0,
        "all_layer_shapes_match": len(bad_layer) == 0,
    }


def compute_readout_scores(cap_rows: list[dict[str, Any]], out_dir: Path) -> dict[str, float]:
    """row_key -> readout z-score, z = dot(h_anchor, c_hat.vector) / sigma."""
    from safetensors.torch import load_file

    c_hat = load_c_hat()
    vector = np.asarray(c_hat["vector"], dtype=np.float64)
    mu = np.asarray(c_hat["mu"], dtype=np.float64)
    sigma = float(c_hat["sigma"])
    intercept = float(c_hat["intercept"])
    if vector.shape[0] != config.READOUT_HIDDEN_DIM:
        raise SystemExit(f"capture FAIL: c_hat vector dim {vector.shape[0]} != expected {config.READOUT_HIDDEN_DIM}")

    index = common.load_jsonl(out_dir / "capture" / "capture.jsonl")
    key = f"anchor__L{config.READOUT_HS_INDEX}"
    scores: dict[str, float] = {}
    for rec in index:
        tensors = load_file(str(out_dir / "capture" / rec["file"]))
        if key not in tensors:
            raise SystemExit(f"capture FAIL: row {rec['id']!r} missing tensor key {key!r} (found {list(tensors.keys())})")
        h = tensors[key].to(dtype=__import__("torch").float32).numpy().astype(np.float64)
        proj = float(np.dot(h - mu, vector)) - intercept
        z = proj / sigma
        scores[rec["id"]] = z
    return scores


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True, help="analysis/capture or analysis/preflight/capture_smoke")
    ap.add_argument("--rows", type=int, default=None, help="cap population to first N rows (smoke)")
    ap.add_argument("--batch-size", type=int, default=config.READOUT_BATCH_SIZE)
    args = ap.parse_args()

    hashes = config.verify_pinned_hashes()
    if not all(hashes.values()):
        raise SystemExit(f"capture FAIL: cell.yaml/gates.yaml sha256 mismatch: {hashes}")

    if args.rows is None:
        marker_path = config.EXPERIMENT_DIR / config.PREFLIGHT_PASS_MARKER
        if not marker_path.is_file():
            raise SystemExit(
                f"capture FAIL: full capture pass requested (--rows omitted) but "
                f"no preflight PASS marker at {marker_path}; run preflight.py first "
                f"(Decision record item 7 / SC1 mandatory GPU preflight)."
            )
        marker = common.load_json(marker_path)
        if not marker.get("pass"):
            raise SystemExit(f"capture FAIL: preflight PASS marker at {marker_path} records pass=False; refusing full run: {marker}")

    rows = population_mod.build_population()
    if args.rows is not None:
        rows = rows[: args.rows]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cap_rows, template_sha256 = render_rows(rows)
    run_capture(cap_rows, out_dir, args.batch_size)
    integrity = verify_capture_integrity(cap_rows, out_dir)
    scores = compute_readout_scores(cap_rows, out_dir)

    role_by_key = {r["row_key"]: r["role"] for r in rows}
    rows_out = [
        {"row_key": rk, "role": role_by_key[rk], "readout_z": z}
        for rk, z in scores.items()
    ]
    common.write_jsonl(out_dir / "readout_scores.jsonl", rows_out)

    manifest = {
        "model": config.MODEL_REPO, "revision": config.MODEL_REVISION,
        "engine": config.READOUT_ENGINE, "persist_dtype": config.READOUT_PERSIST_DTYPE,
        "compute_dtype": "bf16-on-cuda (default; hf_batched engine, no --compute-dtype override)",
        "batch_size": args.batch_size,
        "layer_index": config.READOUT_LAYER_INDEX, "hs_index": config.READOUT_HS_INDEX,
        "anchor_position_rule": "len(token_ids) - 1 (manual tokenize, add_special_tokens=True)",
        "template_sha256": template_sha256,
        "c_hat_sha256": common.sha256_of_file(STAGED / "directions" / "hs20" / "c_hat.json"),
        "n_rows_requested": len(rows), "n_rows_scored": len(scores),
        "integrity": integrity,
    }
    common.write_json(out_dir / "capture_manifest.json", manifest)
    print(json.dumps(manifest, indent=2), flush=True)

    if not integrity["zero_silent_drops"] or not integrity["all_positions_match"] or not integrity["all_layer_shapes_match"]:
        raise SystemExit(f"capture FAIL: integrity check failed: {json.dumps(integrity, indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
