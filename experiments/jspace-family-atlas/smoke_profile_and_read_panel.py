#!/usr/bin/env python3
"""Local CPU smoke test for profile_and_read_panel.py against synthetic
captures. No GPU, no real model, no real rows -- proves the shapes, the
eff_dim_frac estimator, the AUROC/bootstrap-CI path, and the on-disk
split_manifest/capture_manifest/atlas_summary contract all run end to end
before any real Modal capture exists.

Synthetic design: 4 hidden-state layers (embeddings + 3 fake blocks),
hidden_dim=16. Layer 0 has NO signal (pure noise on every axis, expect
AUROC near chance). Layers 1-3 have an injected mean-shift along a fixed
signal dimension per axis, growing across layers, so held-out AUROC should
be higher in later layers and CI width should shrink as class sizes fit the
scale used. Row/role/split proportions loosely mirror the real cells
(more confab than known-correct; unknown_refused is fit_only, exactly like
the real fleet split).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import save_file

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import profile_and_read_panel as pp  # noqa: E402

CELL_ID = "smoke_synthetic_cell"
N_LAYERS_HS = 4  # embeddings + 3 fake blocks
HIDDEN_DIM = 16
SEED = 20260707


def _make_rows(rng: np.random.Generator) -> list[dict]:
    rows = []
    specs = [
        ("known_correct_answered", "fit", 24),
        ("known_correct_answered", "held_out", 18),
        ("confab", "fit", 30),
        ("confab", "held_out", 22),
        ("unknown_refused", "fit_only", 20),
    ]
    i = 0
    for role, split, n in specs:
        for _ in range(n):
            rows.append(
                {
                    "row_key": f"{role}:{split}:{i}",
                    "role": role,
                    "split": split,
                    "source": "smoke_synthetic",
                    "category_canon": "smoke",
                }
            )
            i += 1
    return rows


def _signal_vector(rng: np.random.Generator, dim: int) -> np.ndarray:
    v = np.zeros(dim)
    v[0] = 1.0
    return v


def build_synthetic_captures(rows: list[dict], analysis_dir: Path) -> None:
    rng = np.random.default_rng(SEED)
    cap_dir = analysis_dir / "atlas_capture"
    cap_dir.mkdir(parents=True, exist_ok=True)
    index_lines = []

    # One shared signal dimension: both answered roles (known_correct,
    # confab) shift positive, refused shifts negative, growing with layer.
    # This makes doubt (known vs refused), caution (refused vs confab), and
    # raw_refusal (refused vs merged-answered) all separate along the same
    # dimension without the merged-answered class becoming bimodal.
    role_shift = {
        "known_correct_answered": +1.0,
        "confab": +1.0,
        "unknown_refused": -1.0,
    }

    for row in rows:
        tensors = {}
        for layer in range(N_LAYERS_HS):
            base = rng.normal(size=HIDDEN_DIM)
            if layer == 0:
                shift = 0.0
            else:
                shift = role_shift[row["role"]] * (layer * 1.5)
            vec = base.copy()
            vec[0] += shift
            tensors[f"anchor__L{layer}"] = vec.astype(np.float32)
        fname = f"{row['row_key'].replace(':', '_')}.safetensors"
        save_file(tensors, str(cap_dir / fname))
        index_lines.append({"id": row["row_key"], "file": fname})

    with (cap_dir / "capture.jsonl").open("w", encoding="utf-8") as fh:
        for rec in index_lines:
            fh.write(json.dumps(rec) + "\n")


def main() -> None:
    tmp_root = Path("/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/jspace_atlas_smoke")
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    analysis_dir = tmp_root / "analysis" / CELL_ID
    committed_dir = tmp_root / "analysis-committed" / CELL_ID
    analysis_dir.mkdir(parents=True, exist_ok=True)
    committed_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(SEED)
    rows = _make_rows(rng)
    build_synthetic_captures(rows, analysis_dir)

    split_manifest = {"cell_id": CELL_ID, "rows": rows}
    (committed_dir / "split_manifest.json").write_text(json.dumps(split_manifest, indent=2))

    capture_manifest = {
        "cell_id": CELL_ID,
        "model": "smoke/fake-model",
        "revision": "0" * 40,
        "num_hidden_layers": N_LAYERS_HS - 1,
        "hidden_size": HIDDEN_DIM,
        "n_hidden_states": N_LAYERS_HS,
        "n_rows_in_pool": len(rows),
        "n_rows_captured": len(rows),
        "coverage_frac": 1.0,
        "coverage_pass_ag0": True,
    }
    (committed_dir / "capture_manifest.json").write_text(json.dumps(capture_manifest, indent=2))

    print(f"[smoke] synthetic rows: {len(rows)}, n_hidden_states={N_LAYERS_HS}, hidden_dim={HIDDEN_DIM}")

    result = pp.run_cell(analysis_dir, committed_dir, n_resamples=200, seed=SEED)

    out_path = committed_dir / "atlas_summary.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(f"[smoke] wrote {out_path}")

    assert result["cell_id"] == CELL_ID
    assert result["n_hidden_states"] == N_LAYERS_HS
    assert set(result["per_layer"].keys()) == {0, 1, 2, 3}

    for layer, entry in sorted(result["per_layer"].items()):
        prof = entry["profile"]
        assert 0.0 < prof["eff_dim_frac"] <= 1.0, (layer, prof)
        for axis, axis_result in entry["read_panel"].items():
            assert 0.0 <= axis_result["point"] <= 1.0, (layer, axis, axis_result)
            assert axis_result["ci95_lo"] <= axis_result["point"] <= axis_result["ci95_hi"], (
                layer, axis, axis_result,
            )
            assert axis_result["n_resamples"] == 200

    layer0_aurocs = [
        result["per_layer"][0]["read_panel"][axis]["point"] for axis in ("doubt", "caution", "raw_refusal")
    ]
    layer3_aurocs = [
        result["per_layer"][3]["read_panel"][axis]["point"] for axis in ("doubt", "caution", "raw_refusal")
    ]
    print(f"[smoke] layer 0 (no injected signal) AUROCs: {layer0_aurocs}")
    print(f"[smoke] layer 3 (largest injected signal) AUROCs: {layer3_aurocs}")
    assert all(a < 0.75 for a in layer0_aurocs), (
        "expected near-chance AUROC on the no-signal layer", layer0_aurocs,
    )
    assert all(a > layer0_aurocs[i] for i, a in enumerate(layer3_aurocs)), (
        "expected the signal layer to score higher than the no-signal layer",
        layer0_aurocs, layer3_aurocs,
    )

    print("[smoke] PASS: shapes, eff_dim_frac bounds, AUROC/CI ordering, and "
          "signal-layer-beats-noise-layer sanity check all hold.")


if __name__ == "__main__":
    main()
