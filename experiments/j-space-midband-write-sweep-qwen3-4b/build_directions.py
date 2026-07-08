#!/usr/bin/env python3
"""J-space mid-band write sweep -- CPU offline direction build.

Fits u_d (doubt axis), pos_ctrl (raw caution/write direction), and neg_ctrl
(confab-propensity, carried only to keep c_hat's 2-D orthogonalization
identical to the resolved predecessor's caution-direction construction -- this
instrument's GATE reads doubt only, see AMENDMENT.md) ALL on the FIT split ONLY:
FIT
confab + FIT known_correct_answered for u_d's two poles, FIT confab + ALL
unknown_refused for the AK-Stage-1-style pos_ctrl/neg_ctrl population.
HELD-OUT rows are NEVER touched by this script -- keeping the direction fit
itself out of the population every reported gate number is computed over,
which preserves the predecessor's held-out discipline.

Method (ported from the resolved predecessor's direction builder):
  1. u_d = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused])).
  2. pos_ctrl / neg_ctrl refit on (FIT confab + ALL unknown_refused):
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

Reproducibility guard: LogisticRegression pins RANDOM_STATE;
`--verify-reproducible` runs the fit twice and asserts the fitted vectors are
byte-identical before writing anything.

Outputs (committed, tracked -- NOT the gitignored analysis/):
  analysis-committed/layers/hs{23,26,29,34}/...
  analysis-committed/build_manifest_layers.json
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

SPLIT_MANIFEST = (
    HERE.parent / "common" / "doubt-gated-caution-tighten-heldout-split" / "split_manifest.json"
)

EXTRACT_TENSORS = ANALYSIS / "layer_sweep_anchor_extract.safetensors"
EXTRACT_MANIFEST = ANALYSIS / "layer_sweep_anchor_extract_manifest.json"

HIDDEN_DIM = 2560
RANDOM_STATE = 20260707  # pinned -- see module docstring "DEFECT FIX"

from layers import HS_INDICES, hs_to_block, layer_dir_name  # noqa: E402


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


def _tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{_sanitize_key(row_key)}"


def fit_all(
    fresh: dict, role_by_key: dict, split_by_key: dict, random_state: int, hs_index: int
):
    known_fit = [rk for rk, role in role_by_key.items()
                 if role == "known_correct_answered" and split_by_key.get(rk) == "fit"]
    confab_fit = [rk for rk, role in role_by_key.items()
                  if role == "confab" and split_by_key.get(rk) == "fit"]
    unknown_refused = [rk for rk, role in role_by_key.items() if role == "unknown_refused"]

    H_known_fit = np.stack([fresh[_tensor_key(hs_index, rk)] for rk in known_fit])
    H_unknown = np.stack([fresh[_tensor_key(hs_index, rk)] for rk in unknown_refused])
    u_d = unit(H_known_fit.mean(0) - H_unknown.mean(0))

    ak_rows_in_order = unknown_refused + confab_fit
    H_ak = np.stack([fresh[_tensor_key(hs_index, rk)] for rk in ak_rows_in_order])
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

    def direction_json(
        vector: np.ndarray, sigma: float, role: str, hs_index: int, extra_prov: dict
    ) -> dict:
        return {
            "schema_version": "mechinterp-direction/v1",
            "layer": hs_to_block(hs_index),
            "hidden_dim": HIDDEN_DIM,
            "normalized": True,
            "vector": [float(x) for x in vector],
            "raw_norm": 1.0,
            "intercept": 0.0,
            "mu": [0.0] * HIDDEN_DIM,
            "sigma": sigma,
            "calibration": {},
            "recipe": {"source": "build_directions.py"},
            "provenance": {"role": role, "amendment": "j-space-midband-write-sweep-qwen3-4b",
                          "substrate": "bf16", "base_model": "unsloth/Qwen3-4B",
                          "fit_population": "FIT split only (see split_manifest.json)",
                          "hs_index": hs_index,
                          "decoder_block_index": hs_to_block(hs_index),
                          **extra_prov},
        }

    report = {
        "substrate": "bf16", "base_model": "unsloth/Qwen3-4B",
        "random_state": RANDOM_STATE,
        "reproducibility_verified": bool(args.verify_reproducible),
        "extract_manifest_sha256": _sha256_file(EXTRACT_MANIFEST),
        "split_manifest_sha256": _sha256_file(SPLIT_MANIFEST),
        "layers": {},
    }

    for hs_index in HS_INDICES:
        fit1 = fit_all(fresh, role_by_key, split_by_key, RANDOM_STATE, hs_index)
        if args.verify_reproducible:
            fit2 = fit_all(fresh, role_by_key, split_by_key, RANDOM_STATE, hs_index)
            for name in ("u_d", "u_p", "caution_dir", "c_hat"):
                a, b = fit1[name], fit2[name]
                if not np.array_equal(a, b):
                    max_diff = float(np.max(np.abs(a - b)))
                    print(
                        f"[build] REPRODUCIBILITY FAIL hs={hs_index} on {name}: "
                        f"max_abs_diff={max_diff}",
                        file=sys.stderr,
                    )
                    return 1
            print(f"[build] reproducibility check PASS hs={hs_index}")

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

        fit_keys_labeled = [(rk, "confab") for rk in confab_fit] + [
            (rk, "known_correct_answered") for rk in known_fit
        ]
        H_fit = np.stack([fresh[_tensor_key(hs_index, rk)] for rk, _ in fit_keys_labeled])
        proj_d_fit = H_fit @ u_d
        proj_p_fit = H_fit @ u_p
        proj_c_fit = H_fit @ c_hat
        mu_d, sigma_d = float(proj_d_fit.mean()), float(proj_d_fit.std())
        mu_p, sigma_p = float(proj_p_fit.mean()), float(proj_p_fit.std())
        mu_c, sigma_c = float(proj_c_fit.mean()), float(proj_c_fit.std())

        layer_name = layer_dir_name(hs_index)
        layer_dir = COMMITTED / "layers" / layer_name
        source_dir = layer_dir / "source_directions"
        source_dir.mkdir(parents=True, exist_ok=True)

        u_d_json = direction_json(
            u_d, 1.0, "doubt_sensor_u_d", hs_index,
            {"method": "mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]), unit-normalized",
             "n_known_correct_answered_fit": len(known_fit),
             "n_unknown_refused": len(unknown_refused),
             "layer_label": layer_name,
             "mu_d_over_fit_pool": mu_d, "sigma_d_over_fit_pool": sigma_d,
             "cos_u_d_u_p": cos_ud_up},
        )
        (layer_dir / f"u_d_{layer_name}.json").write_text(json.dumps(u_d_json, indent=2))

        pos_ctrl_json = direction_json(
            caution_dir, 1.0, "positive_control", hs_index,
            {"signal": "refuse_vs_confab_mass_mean",
             "method": "predecessor refuse/propensity fit, refit on FIT confab + ALL unknown_refused",
             "layer_label": layer_name, "n_confab_fit": len(confab_fit),
             "n_unknown_refused": len(unknown_refused), **ctrl_fit_info},
        )
        (source_dir / f"pos_ctrl_{layer_name}.json").write_text(json.dumps(pos_ctrl_json, indent=2))

        neg_ctrl_json = direction_json(
            u_p, 1.0, "negative_control", hs_index,
            {"signal": "confab_propensity_logistic",
             "method": "predecessor refuse/propensity fit with random_state pinned",
             "layer_label": layer_name, "n_confab_fit": len(confab_fit),
             "n_unknown_refused": len(unknown_refused),
             "note": "Not read by this instrument's gate; used for c_hat orthogonalization.",
             **ctrl_fit_info},
        )
        (source_dir / f"neg_ctrl_{layer_name}.json").write_text(json.dumps(neg_ctrl_json, indent=2))

        c_hat_json = direction_json(
            c_hat, sigma_c, "caution_write_c_hat", hs_index,
            {"orthogonalized_against": [f"u_d_{layer_name}.json", f"source_directions/neg_ctrl_{layer_name}.json"],
             "source_caution_dir": f"source_directions/pos_ctrl_{layer_name}.json",
             "cos_caution_dir_c_hat": cos_caution_chat,
             "mu_c_over_fit_pool": mu_c, "sigma_c_over_fit_pool": sigma_c,
             "n_fit_pool": len(fit_keys_labeled)},
        )
        (layer_dir / f"c_hat_{layer_name}.json").write_text(json.dumps(c_hat_json, indent=2))

        report["layers"][layer_name] = {
            "hs_index": hs_index,
            "decoder_block_index": hs_to_block(hs_index),
            "n_known_correct_answered_fit": len(known_fit),
            "n_confab_fit": len(confab_fit),
            "n_unknown_refused": len(unknown_refused),
            "cos_u_d_u_p": cos_ud_up,
            "cos_caution_dir_c_hat": cos_caution_chat,
            "mu_d": mu_d, "sigma_d": sigma_d,
            "mu_p": mu_p, "sigma_p": sigma_p,
            "mu_c": mu_c, "sigma_c": sigma_c,
        }

    (COMMITTED / "build_manifest_layers.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
