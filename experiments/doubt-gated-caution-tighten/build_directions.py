#!/usr/bin/env python3
"""Doubt-gated caution snap -- CPU offline build (step 2/3, after
extract_l34_anchor.py + split_fit_heldout.py). BF16 substrate.

Fits u_d (doubt axis), pos_ctrl (raw caution/write direction), and neg_ctrl
(confab-propensity, carried only to keep c_hat's 2-D orthogonalization
identical in method to the sibling two-signal diagnostic that produced this
instrument's cited estimates -- this instrument's GATE reads doubt only, see
AMENDMENT.md) ALL on the FIT split ONLY (see split_fit_heldout.py): FIT
confab + FIT known_correct_answered for u_d's two poles, FIT confab + ALL
unknown_refused for the AK-Stage-1-style pos_ctrl/neg_ctrl population.
HELD-OUT rows are NEVER touched by this script -- keeping the direction fit
itself out of the population every reported gate number is computed over,
which is the corrected-redesign's whole point (the sibling two-signal
diagnostic disclosed, but did not fix, the same confab rows being in-sample
to both its direction fit and its G1-tighten eval tail).

Method (ported verbatim from the sibling two-signal experiment's own
build_two_signal_directions.py, itself ported verbatim from
dark-actuator-screen's build_directions.py:_raw_refuse_and_propensity, both
read in full before writing this):
  1. u_d = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused])) at L34.
  2. pos_ctrl / neg_ctrl refit at L34 on (FIT confab + ALL unknown_refused):
       refuse_dir  = unit(mean(H[unknown_refused]) - mean(H[confab_fit]))     (mass-mean)
       prop_dir    = unit(LogisticRegression(saga, C=1.0, tol=1e-3,
                     max_iter=5000, random_state=RANDOM_STATE).fit(
                     StandardScaler-transformed H, y_confab).coef_ / scale_)
     caution_dir := refuse_dir (pos_ctrl); u_p := prop_dir (neg_ctrl).
  3. c_hat = unit(caution_dir orthogonalized against BOTH u_d and u_p), a 2-D
     Gram-Schmidt erase (QR of span(u_d, u_p)).
  4. Standardization stats (mu_d/sigma_d, mu_p/sigma_p, mu_c/sigma_c) computed
     over the SAME FIT population (FIT confab + FIT known_correct_answered)
     that gate_fit.py reads -- so the gate the held-out pipeline applies uses
     out-of-sample standardization, never touching held-out activations.

DEFECT FIX (this instrument, vs the superseded two-signal build): the prior
build's LogisticRegression(solver="saga", ...) had NO random_state, so
neg_ctrl/c_hat were NOT REPRODUCIBLE -- a re-run could silently produce a
different committed vector (confirmed as a live defect, see NOTEBOOK.md /
docs/sessions/20260707T123611Z-two-signal-bf16-pivot-containment-guard-hardening.md checkpoint 005-checkpoint "OTHER DEFECTS found"). Fixed
here by pinning RANDOM_STATE; `--verify-reproducible` runs the fit TWICE and
asserts the two neg_ctrl/pos_ctrl/c_hat vectors are byte-identical before
writing anything.

Outputs (committed, tracked -- NOT the gitignored analysis/):
  analysis-committed/source_directions/pos_ctrl_L34.json
  analysis-committed/source_directions/neg_ctrl_L34.json
  analysis-committed/u_d_L34.json
  analysis-committed/c_hat_L34.json
  analysis-committed/build_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

EXTRACT_TENSORS = ANALYSIS / "l34_anchor_extract.safetensors"
EXTRACT_MANIFEST = ANALYSIS / "l34_anchor_extract_manifest.json"
SPLIT_MANIFEST = COMMITTED / "split_manifest.json"

LAYER_BLOCK = 33  # tuner 0-indexed decoder block for "L34"
HIDDEN_DIM = 2560
RANDOM_STATE = 20260707  # pinned -- see module docstring "DEFECT FIX"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def _raw_refuse_and_propensity(
    H_anchor: np.ndarray, y_confab: np.ndarray, random_state: int
) -> tuple[np.ndarray, np.ndarray, dict]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    refuse_mean = H_anchor[y_confab == 0].mean(0)
    confab_mean = H_anchor[y_confab == 1].mean(0)
    refuse_dir = unit(refuse_mean - confab_mean)

    sc = StandardScaler().fit(H_anchor)
    Z = sc.transform(H_anchor)
    clf = LogisticRegression(
        solver="saga", tol=1e-3, max_iter=5000, C=1.0, random_state=random_state
    ).fit(Z, y_confab)
    prop_raw = clf.coef_.ravel() / sc.scale_
    prop_dir = unit(prop_raw)
    fit_info = {
        "n_confab": int(y_confab.sum()), "n_refuse": int((1 - y_confab).sum()),
        "logreg": {"solver": "saga", "tol": 1e-3, "max_iter": 5000, "C": 1.0,
                   "random_state": random_state},
    }
    return refuse_dir, prop_dir, fit_info


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def load_fresh_extract() -> dict[str, np.ndarray]:
    from safetensors.numpy import load_file
    t = load_file(str(EXTRACT_TENSORS))
    return {k: np.asarray(v, dtype=np.float64) for k, v in t.items()}


def fit_all(fresh: dict, role_by_key: dict, split_by_key: dict, random_state: int):
    known_fit = [rk for rk, role in role_by_key.items()
                 if role == "known_correct_answered" and split_by_key.get(rk) == "fit"]
    confab_fit = [rk for rk, role in role_by_key.items()
                  if role == "confab" and split_by_key.get(rk) == "fit"]
    unknown_refused = [rk for rk, role in role_by_key.items() if role == "unknown_refused"]

    H_known_fit = np.stack([fresh[_sanitize_key(rk)] for rk in known_fit])
    H_unknown = np.stack([fresh[_sanitize_key(rk)] for rk in unknown_refused])
    u_d = unit(H_known_fit.mean(0) - H_unknown.mean(0))

    ak_rows_in_order = unknown_refused + confab_fit
    H_ak = np.stack([fresh[_sanitize_key(rk)] for rk in ak_rows_in_order])
    y_confab = np.array([0] * len(unknown_refused) + [1] * len(confab_fit), dtype=int)
    caution_dir, u_p, ctrl_fit_info = _raw_refuse_and_propensity(H_ak, y_confab, random_state)

    M = np.stack([u_d, u_p], axis=1)
    Q, _ = np.linalg.qr(M)
    c_perp = caution_dir - Q @ (Q.T @ caution_dir)
    c_hat = unit(c_perp)

    return {
        "u_d": u_d, "u_p": u_p, "caution_dir": caution_dir, "c_hat": c_hat,
        "known_fit": known_fit, "confab_fit": confab_fit, "unknown_refused": unknown_refused,
        "ctrl_fit_info": ctrl_fit_info,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-reproducible", action="store_true",
                     help="fit twice and assert byte-identical before writing")
    args = ap.parse_args()

    COMMITTED.mkdir(parents=True, exist_ok=True)
    (COMMITTED / "source_directions").mkdir(parents=True, exist_ok=True)

    extract_manifest = json.loads(EXTRACT_MANIFEST.read_text())
    assert extract_manifest["substrate"] == "bf16"
    assert extract_manifest["base_model"] == "unsloth/Qwen3-4B"
    role_by_key = {rm["row_key"]: rm["role"] for rm in extract_manifest["rows"]}
    cat_by_key = {rm["row_key"]: rm.get("category_canon") for rm in extract_manifest["rows"]}

    split_manifest = json.loads(SPLIT_MANIFEST.read_text())
    split_by_key = {r["row_key"]: r["split"] for r in split_manifest["rows"]}

    fresh = load_fresh_extract()

    fit1 = fit_all(fresh, role_by_key, split_by_key, RANDOM_STATE)
    if args.verify_reproducible:
        fit2 = fit_all(fresh, role_by_key, split_by_key, RANDOM_STATE)
        for name in ("u_d", "u_p", "caution_dir", "c_hat"):
            a, b = fit1[name], fit2[name]
            if not np.array_equal(a, b):
                max_diff = float(np.max(np.abs(a - b)))
                print(f"[build] REPRODUCIBILITY FAIL on {name}: max_abs_diff={max_diff}",
                      file=sys.stderr)
                return 1
        print("[build] reproducibility check PASS: u_d/u_p/caution_dir/c_hat "
              "byte-identical across two independent fits.")

    u_d = fit1["u_d"]
    u_p = fit1["u_p"]
    caution_dir = fit1["caution_dir"]
    c_hat = fit1["c_hat"]
    known_fit = fit1["known_fit"]
    confab_fit = fit1["confab_fit"]
    unknown_refused = fit1["unknown_refused"]
    ctrl_fit_info = fit1["ctrl_fit_info"]

    cos_ud_up = float(np.dot(u_d, u_p))
    cos_caution_chat = float(np.dot(caution_dir, c_hat))

    # -- standardization stats over the FIT population (confab_fit + known_fit) --
    fit_keys_labeled = [(rk, "confab") for rk in confab_fit] + [(rk, "known_correct_answered") for rk in known_fit]
    H_fit = np.stack([fresh[_sanitize_key(rk)] for rk, _ in fit_keys_labeled])
    proj_d_fit = H_fit @ u_d
    proj_p_fit = H_fit @ u_p
    proj_c_fit = H_fit @ c_hat
    mu_d, sigma_d = float(proj_d_fit.mean()), float(proj_d_fit.std())
    mu_p, sigma_p = float(proj_p_fit.mean()), float(proj_p_fit.std())
    mu_c, sigma_c = float(proj_c_fit.mean()), float(proj_c_fit.std())

    def direction_json(vector: np.ndarray, sigma: float, role: str, extra_prov: dict) -> dict:
        return {
            "schema_version": "mechinterp-direction/v1",
            "layer": LAYER_BLOCK,
            "hidden_dim": HIDDEN_DIM,
            "normalized": True,
            "vector": [float(x) for x in vector],
            "raw_norm": 1.0,
            "intercept": 0.0,
            "mu": [0.0] * HIDDEN_DIM,
            "sigma": sigma,
            "calibration": {},
            "recipe": {"source": "build_directions.py"},
            "provenance": {"role": role, "amendment": "doubt-gated-caution-tighten",
                          "substrate": "bf16", "base_model": "unsloth/Qwen3-4B",
                          "fit_population": "FIT split only (see split_manifest.json)",
                          **extra_prov},
        }

    u_d_json = direction_json(
        u_d, 1.0, "doubt_sensor_u_d",
        {"method": "mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]), unit-normalized",
         "n_known_correct_answered_fit": len(known_fit),
         "n_unknown_refused": len(unknown_refused),
         "layer_label": "L34",
         "mu_d_over_fit_pool": mu_d, "sigma_d_over_fit_pool": sigma_d,
         "cos_u_d_u_p": cos_ud_up},
    )
    (COMMITTED / "u_d_L34.json").write_text(json.dumps(u_d_json, indent=2))

    pos_ctrl_json = direction_json(
        caution_dir, 1.0, "positive_control",
        {"signal": "refuse_vs_confab_mass_mean",
         "method": "dark-actuator-screen build_directions.py:_raw_refuse_and_propensity "
                    "(pre-QR refuse direction), verbatim, refit on FIT confab + ALL unknown_refused",
         "layer_label": "L34", "n_confab_fit": len(confab_fit), "n_unknown_refused": len(unknown_refused),
         **ctrl_fit_info},
    )
    (COMMITTED / "source_directions" / "pos_ctrl_L34.json").write_text(
        json.dumps(pos_ctrl_json, indent=2))

    neg_ctrl_json = direction_json(
        u_p, 1.0, "negative_control",
        {"signal": "confab_propensity_logistic",
         "method": "dark-actuator-screen build_directions.py:_raw_refuse_and_propensity "
                    "(pre-QR propensity direction), verbatim, refit on FIT confab + ALL unknown_refused, "
                    "random_state PINNED (defect fix vs the superseded two-signal build)",
         "layer_label": "L34", "n_confab_fit": len(confab_fit), "n_unknown_refused": len(unknown_refused),
         "note": "NOT read by this instrument's gate (doubt only); carried solely to keep c_hat's "
                 "2-D orthogonalization identical in method to the sibling diagnostic that produced "
                 "this instrument's cited dose-response estimates.",
         **ctrl_fit_info},
    )
    (COMMITTED / "source_directions" / "neg_ctrl_L34.json").write_text(
        json.dumps(neg_ctrl_json, indent=2))

    c_hat_json = direction_json(
        c_hat, sigma_c, "caution_write_c_hat",
        {"orthogonalized_against": ["u_d_L34.json", "source_directions/neg_ctrl_L34.json"],
         "source_caution_dir": "source_directions/pos_ctrl_L34.json",
         "cos_caution_dir_c_hat": cos_caution_chat,
         "mu_c_over_fit_pool": mu_c, "sigma_c_over_fit_pool": sigma_c,
         "n_fit_pool": len(fit_keys_labeled)},
    )
    (COMMITTED / "c_hat_L34.json").write_text(json.dumps(c_hat_json, indent=2))

    report = {
        "substrate": "bf16", "base_model": "unsloth/Qwen3-4B",
        "random_state": RANDOM_STATE,
        "n_known_correct_answered_fit": len(known_fit),
        "n_confab_fit": len(confab_fit),
        "n_unknown_refused": len(unknown_refused),
        "cos_u_d_u_p": cos_ud_up,
        "cos_caution_dir_c_hat": cos_caution_chat,
        "mu_d": mu_d, "sigma_d": sigma_d,
        "mu_p": mu_p, "sigma_p": sigma_p,
        "mu_c": mu_c, "sigma_c": sigma_c,
        "reproducibility_verified": bool(args.verify_reproducible),
        "extract_manifest_sha256": _sha256_file(EXTRACT_MANIFEST),
        "split_manifest_sha256": _sha256_file(SPLIT_MANIFEST),
    }
    (COMMITTED / "build_manifest.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
