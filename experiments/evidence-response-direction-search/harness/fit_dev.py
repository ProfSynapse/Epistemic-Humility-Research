#!/usr/bin/env python3
"""d_ev fit for evidence-response-direction-search (M4c). Step 3 of the
execution sequence. Fits `d_ev` = unit-normalized mean(h_true - h_false) over
the 200 FIT confab rows' RAW `anchor__L20` tensors (cell.yaml
`fit.estimator_primary`), plus the pre-registered top-PC secondary
(`fit.estimator_secondary`, report-only). Freezes the rung-(b) reference-dose
inputs (mu_c/sigma_c) from the FIT confab rows' `no_answer_baseline`
projections ONLY -- correct-control is never in fit and this module never
reads a held-out baseline projection (self-blinding).

d_ev is NEVER scored on the true-vs-false contrast it was fit from (AMENDMENT
`The construct: d_ev`): no AUROC or separation statistic on that contrast is
computed or reported anywhere in this module.

Writes `analysis-committed/directions/hs20/d_ev.json` (primary,
mechinterp-direction/v1) and `d_ev_topPC.json` (secondary, report-only
sibling) BEFORE any held-out AUROC, comparator difference, or survival
contrast is computed (SC0).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import tensors  # noqa: E402

COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"
DIRECTIONS_DIR = COMMITTED / "directions" / "hs20"


def fit_d_ev(fit_row_keys: list[str]) -> dict:
    h_true = tensors.load_anchors("true_answer", fit_row_keys)
    h_false = tensors.load_anchors("false_answer_placebo", fit_row_keys)
    diff = h_true - h_false  # (200, 2560); false -> true, per row
    d_ev_raw = diff.mean(axis=0)
    d_ev = common.unit(d_ev_raw)

    # Secondary (report-only): top principal component of the CENTERED
    # paired-difference matrix. Centering subtracts the column mean, which is
    # d_ev_raw itself (mean of the rows of `diff`).
    centered = diff - d_ev_raw
    # SVD of the centered (200 x 2560) matrix; top right-singular vector is
    # the first principal component direction in hidden-state space.
    _, s, vt = np.linalg.svd(centered, full_matrices=False)
    top_pc = vt[0]
    top_pc = common.unit(top_pc)
    if float(np.dot(top_pc, d_ev)) < 0.0:
        top_pc = -top_pc  # orientation convention: align with d_ev's sign, report-only
    explained_variance_ratio = float((s[0] ** 2) / np.sum(s ** 2)) if np.sum(s ** 2) > 0 else 0.0

    return {
        "d_ev_raw": d_ev_raw,
        "d_ev": d_ev,
        "top_pc": top_pc,
        "top_pc_explained_variance_ratio": explained_variance_ratio,
        "top_pc_cos_with_d_ev": float(np.dot(top_pc, d_ev)),
        "n_fit": len(fit_row_keys),
    }


def compute_reference_dose_inputs(d_ev: np.ndarray, fit_row_keys: list[str]) -> dict:
    """mu_c/sigma_c of the baseline-arm (no_answer_baseline) projection
    distribution, restricted to the 200 FIT confab rows -- the only
    population available before the split/d_ev freeze without touching a
    held-out baseline projection (self-blinding; circularity item iii). This
    is narrower than M4-WK's native fit (which combined confab+known FIT
    rows, both drawn from its own disjoint native_fit_split) because M4c's
    fit population, by the AMENDMENT's hard population constraint, is
    confab-only (all 360 correct-control rows are held-out by construction,
    decision record item 3). Reported straight; flagged in the harness
    report as an interpretation of the "baseline-arm projection
    distribution" convention (rulings record item 3) under this population
    constraint."""
    h_baseline_fit = tensors.load_anchors("no_answer_baseline", fit_row_keys)
    proj = h_baseline_fit @ d_ev
    mu_c = float(proj.mean())
    sigma_c = float(proj.std()) or 1.0
    return {"mu_c": mu_c, "sigma_c": sigma_c, "n": len(fit_row_keys), "population": "FIT confab rows only (200), no_answer_baseline arm"}


def main() -> int:
    config.assert_pinned_hashes()

    split_path = SELECTION_DIR / "fit_heldout_split.json"
    if not split_path.is_file():
        raise SystemExit(f"fit_dev FAIL: no {split_path}; run split_freeze.py first.")
    split = common.load_json(split_path)
    fit_row_keys = sorted(split["fit_row_keys"])
    if len(fit_row_keys) != config.N_FIT:
        raise SystemExit(f"fit_dev FAIL: fit split has {len(fit_row_keys)} rows, expected {config.N_FIT}")
    fit_split_file_sha256 = common.sha256_of_file(split_path)
    fit_id_list_sha256 = common.sha256_of_bytes(
        __import__("json").dumps(fit_row_keys, sort_keys=False).encode("utf-8")
    )

    print(f"[fit_dev] fitting d_ev on {len(fit_row_keys)} FIT confab rows...", flush=True)
    fit_result = fit_d_ev(fit_row_keys)
    d_ev = fit_result["d_ev"]
    print(f"[fit_dev] d_ev fit complete. top_pc_cos_with_d_ev={fit_result['top_pc_cos_with_d_ev']:.6f} explained_var_ratio={fit_result['top_pc_explained_variance_ratio']:.6f}", flush=True)

    dose_inputs = compute_reference_dose_inputs(d_ev, fit_row_keys)
    reference_dose_abs = config.REFERENCE_DOSE_MULTIPLIER * dose_inputs["sigma_c"]
    print(f"[fit_dev] reference dose: mu_c={dose_inputs['mu_c']:.6f} sigma_c={dose_inputs['sigma_c']:.6f} reference_dose_abs={reference_dose_abs:.6f}", flush=True)

    d_ev_record = {
        "schema_version": "mechinterp-direction/v1",
        "layer": config.LAYER_INDEX,
        "hidden_dim": config.HIDDEN_DIM,
        "normalized": True,
        "vector": [float(x) for x in d_ev],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * config.HIDDEN_DIM,
        "sigma": dose_inputs["sigma_c"],
        "calibration": {"mu_c": dose_inputs["mu_c"], "sigma_c": dose_inputs["sigma_c"]},
        "recipe": {
            "source": "fit_dev.py (this experiment)",
            "estimator": "mean paired difference mean(h_true - h_false) over FIT confab rows, unit-normalized (cell.yaml fit.estimator_primary)",
        },
        "provenance": {
            "role": "evidence_response_direction_d_ev",
            "amendment": "evidence-response-direction-search",
            "base_model": config.MODEL_REPO,
            "revision": config.MODEL_REVISION,
            "fit_population": f"{dose_inputs['n']} FIT confab rows (seed {config.SPLIT_SEED} split of the M4-WK 400-row test confab population), true_answer minus false_answer_placebo arms",
            "hs_index": config.HS_INDEX,
            "sign_convention": "d_ev points false -> true (grounding positive) by construction (mean(h_true - h_false)); registered confab-positive SCORE is the negated projection -(h . d_ev), applied at readout time, not baked into this vector",
            "reference_dose_abs": reference_dose_abs,
            "reference_dose_derivation": f"{config.REFERENCE_DOSE_MULTIPLIER}x sigma_c of the baseline-arm (no_answer_baseline) projection distribution, restricted to the 200 FIT confab rows (see mu_c_sigma_c_population_note)",
            "mu_c_sigma_c_population_note": dose_inputs["population"],
            "fit_split_file_sha256": fit_split_file_sha256,
            "fit_id_list_sha256": fit_id_list_sha256,
        },
    }

    top_pc_record = {
        "schema_version": "mechinterp-direction/v1",
        "layer": config.LAYER_INDEX,
        "hidden_dim": config.HIDDEN_DIM,
        "normalized": True,
        "vector": [float(x) for x in fit_result["top_pc"]],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * config.HIDDEN_DIM,
        "sigma": None,
        "calibration": None,
        "recipe": {
            "source": "fit_dev.py (this experiment)",
            "estimator": "top principal component of the centered paired-difference matrix {h_true(i) - h_false(i)} over FIT confab rows (cell.yaml fit.estimator_secondary); REPORT-ONLY, never rounds into the primary verdict (rulings record item 6)",
        },
        "provenance": {
            "role": "evidence_response_direction_d_ev_topPC_secondary",
            "amendment": "evidence-response-direction-search",
            "base_model": config.MODEL_REPO,
            "revision": config.MODEL_REVISION,
            "fit_population": f"{dose_inputs['n']} FIT confab rows, true_answer minus false_answer_placebo arms",
            "hs_index": config.HS_INDEX,
            "explained_variance_ratio": fit_result["top_pc_explained_variance_ratio"],
            "cos_with_primary_d_ev": fit_result["top_pc_cos_with_d_ev"],
            "orientation_convention": "sign flipped if needed so that dot(top_pc, d_ev) >= 0 (report-only convention, no registered score depends on this)",
            "fit_split_file_sha256": fit_split_file_sha256,
            "fit_id_list_sha256": fit_id_list_sha256,
        },
    }

    DIRECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(DIRECTIONS_DIR / "d_ev.json", d_ev_record)
    common.write_json(DIRECTIONS_DIR / "d_ev_topPC.json", top_pc_record)
    d_ev_sha256 = common.sha256_of_file(DIRECTIONS_DIR / "d_ev.json")
    print(f"[fit_dev] wrote {DIRECTIONS_DIR / 'd_ev.json'} sha256={d_ev_sha256}", flush=True)
    print(f"[fit_dev] wrote {DIRECTIONS_DIR / 'd_ev_topPC.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
