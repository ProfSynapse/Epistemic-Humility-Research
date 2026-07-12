#!/usr/bin/env python3
"""Local CPU smoke test for profile_and_read_family_atlas_panel.py against
synthetic captures. No GPU, no real model, no real rows -- proves the shapes,
the eff_dim_frac estimator, the AUROC/bootstrap-CI path, the random-direction
control, and the on-disk split_manifest/capture_manifest/atlas_summary
contract all run end to end before any real capture exists.

Adapted from `experiments/jspace-family-atlas/smoke_profile_and_read_panel.py`
to exercise the generalized, substrate-agnostic script plus the
random_direction_control field that script now always emits.

Synthetic design: 4 hidden-state layers (embeddings + 3 fake blocks),
hidden_dim=16. Layer 0 has NO signal (pure noise on every axis, expect AUROC
near chance and a random-direction control also near chance). Layers 1-3
have an injected mean-shift along a fixed signal dimension per axis, growing
across layers, so held-out AUROC should be higher in later layers and the
random-direction control should stay near chance throughout (it never sees
the signal dimension preferentially). Row/role/split proportions loosely
mirror real cells (more confab than known-correct; unknown_refused is
fit_only, exactly like the real fleets this instrument has mapped so far).
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
import profile_and_read_family_atlas_panel as pp  # noqa: E402

CELL_ID = "smoke_synthetic_cell"
N_LAYERS_HS = 4  # embeddings + 3 fake blocks
# hidden_dim must be large enough that a RANDOM unit direction's expected
# alignment with the single fixed signal dimension (~1/sqrt(hidden_dim)) is
# small relative to per-dimension noise; a low hidden_dim (e.g. 16) lets a
# random direction partially ride the same signal by chance, defeating the
# near-chance assertion below. A fitted mean-difference direction still
# isolates the signal dimension correctly at any hidden_dim, since averaging
# over FIT rows cancels the noise-only dimensions.
HIDDEN_DIM = 256
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


def build_synthetic_captures(rows: list[dict], analysis_dir: Path) -> None:
    rng = np.random.default_rng(SEED)
    cap_dir = analysis_dir / "atlas_capture"
    cap_dir.mkdir(parents=True, exist_ok=True)
    index_lines = []

    # One shared signal dimension: both answered roles (known_correct,
    # confab) shift positive, refused shifts negative, growing with layer.
    # This makes doubt (known vs refused), caution (refused vs confab), and
    # raw_refusal (refused vs merged-answered) all separate along the same
    # dimension without the merged-answered class becoming bimodal, while
    # leaving every OTHER dimension pure noise for the random-direction
    # control to (correctly) fail to pick up.
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
    tmp_root = Path("/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/family_atlas_smoke")
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

    refused_keys = [r["row_key"] for r in rows if r["role"] == "unknown_refused"]
    split_a = pp.split_refused_pool(refused_keys, seed=SEED)
    split_b = pp.split_refused_pool(refused_keys, seed=SEED)
    assert split_a == split_b, "split_refused_pool must be deterministic across calls with the same seed"
    refused_fit_check, refused_eval_check = split_a
    assert not (set(refused_fit_check) & set(refused_eval_check)), "refused_fit/refused_eval must be disjoint"
    assert set(refused_fit_check) | set(refused_eval_check) == set(refused_keys), "split must cover the full refused pool"
    print(
        f"[smoke] split_refused_pool deterministic across two calls: "
        f"refused_fit={len(refused_fit_check)}, refused_eval={len(refused_eval_check)}, disjoint=True"
    )

    # Random-direction determinism: same (hidden_dim, layer, seed) must
    # reproduce the same vector, and a different layer must not.
    dir_a = pp.random_unit_direction(HIDDEN_DIM, layer=2, seed=SEED)
    dir_b = pp.random_unit_direction(HIDDEN_DIM, layer=2, seed=SEED)
    dir_c = pp.random_unit_direction(HIDDEN_DIM, layer=3, seed=SEED)
    assert np.allclose(dir_a, dir_b), "random_unit_direction must be deterministic for the same (dim, layer, seed)"
    assert not np.allclose(dir_a, dir_c), "different layers must draw different random directions"
    print("[smoke] random_unit_direction deterministic per (dim, layer, seed) and layer-distinct")

    result = pp.run_cell(analysis_dir, committed_dir, n_resamples=200, seed=SEED)

    out_path = committed_dir / "atlas_summary.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(f"[smoke] wrote {out_path}")

    assert result["cell_id"] == CELL_ID
    assert result["n_hidden_states"] == N_LAYERS_HS
    assert set(result["per_layer"].keys()) == {0, 1, 2, 3}

    rps = result["refused_pool_split"]
    assert rps["n_refused_fit"] + rps["n_refused_eval"] == rps["n_refused_fit_only_total"]
    assert rps["n_refused_fit_only_total"] == len(refused_keys)
    print(f"[smoke] atlas_summary refused_pool_split: {rps}")

    for layer, entry in sorted(result["per_layer"].items()):
        prof = entry["profile"]
        assert 0.0 < prof["eff_dim_frac"] <= 1.0, (layer, prof)
        for axis, axis_result in entry["read_panel"].items():
            assert 0.0 <= axis_result["point"] <= 1.0, (layer, axis, axis_result)
            assert axis_result["ci95_lo"] <= axis_result["point"] <= axis_result["ci95_hi"], (
                layer, axis, axis_result,
            )
            assert axis_result["n_resamples"] == 200
        rdc = entry["random_direction_control"]
        for contrast, value in rdc.items():
            assert 0.5 <= value <= 1.0, (layer, contrast, value)

    layer0_aurocs = [
        result["per_layer"][0]["read_panel"][axis]["point"] for axis in ("doubt", "caution", "raw_refusal")
    ]
    layer3_aurocs = [
        result["per_layer"][3]["read_panel"][axis]["point"] for axis in ("doubt", "caution", "raw_refusal")
    ]
    layer0_random = list(result["per_layer"][0]["random_direction_control"].values())
    layer3_random = list(result["per_layer"][3]["random_direction_control"].values())
    print(f"[smoke] layer 0 (no injected signal) AUROCs: {layer0_aurocs}")
    print(f"[smoke] layer 3 (largest injected signal) AUROCs: {layer3_aurocs}")
    print(f"[smoke] layer 0 random-direction control: {layer0_random}")
    print(f"[smoke] layer 3 random-direction control: {layer3_random}")
    assert all(a < 0.75 for a in layer0_aurocs), (
        "expected near-chance AUROC on the no-signal layer", layer0_aurocs,
    )
    assert all(a > layer0_aurocs[i] for i, a in enumerate(layer3_aurocs)), (
        "expected the signal layer to score higher than the no-signal layer",
        layer0_aurocs, layer3_aurocs,
    )
    assert all(r < 0.75 for r in layer3_random), (
        "random-direction control must stay near chance even on the "
        "largest-signal layer, since the signal lives on a single fixed "
        "dimension the random direction only rarely aligns with",
        layer3_random,
    )

    print("[smoke] PASS: shapes, eff_dim_frac bounds, AUROC/CI ordering, "
          "signal-layer-beats-noise-layer sanity check, and random-direction "
          "control near-chance behavior all hold.")


if __name__ == "__main__":
    main()
