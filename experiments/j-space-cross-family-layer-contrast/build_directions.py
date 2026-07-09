#!/usr/bin/env python3
"""Cross-family J-space layer contrast -- CPU offline direction build.

Ported from `j-space-midband-write-sweep-qwen3-4b/build_directions.py`,
generalized to read the family's checkpoint/hidden_dim/candidate hs_indices
from its resolved band selection instead of hardcoding Qwen3-4B and
`HS_INDICES = [23, 26, 29, 34]`. Method is otherwise IDENTICAL across
families (LOCKED DESIGN: same mechanism class, only family/layer varies):

  1. u_d = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused])).
  2. pos_ctrl / neg_ctrl refit on (FIT confab + ALL unknown_refused):
       refuse_dir  = unit(mean(H[unknown_refused]) - mean(H[confab_fit]))     (mass-mean)
       prop_dir    = unit(LogisticRegression(saga, C=1.0, tol=1e-3,
                     max_iter=5000, random_state=RANDOM_STATE).fit(
                     StandardScaler-transformed H, y_confab).coef_ / scale_)
     caution_dir := refuse_dir (pos_ctrl); u_p := prop_dir (neg_ctrl).
  3. c_hat = unit(caution_dir orthogonalized against BOTH u_d and u_p).
  4. Standardization stats computed over the SAME FIT population.

FIT / HELD-OUT split, direction fit, and gate threshold are per-family and
NEVER pooled across families (each family's HELD-OUT rows are never touched
by this script, matching the predecessor's held-out discipline).

Outputs (committed, tracked): analysis-committed/<family>/layers/hs{...}/...
and analysis-committed/<family>/build_manifest_layers.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from family_config import (  # noqa: E402
    FAMILY_SLUGS, hs_to_block, layer_dir_name, load_family, hs_indices as family_hs_indices,
)

RANDOM_STATE = 20260707  # pinned, identical across families (see module docstring)


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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    ap.add_argument("--verify-reproducible", action="store_true",
                     help="fit twice and assert byte-identical before writing")
    args = ap.parse_args(argv)

    family = args.family
    cfg = load_family(family)
    hs_list = family_hs_indices(cfg)  # raises if band_selection unresolved

    analysis = HERE / "analysis" / family
    committed = HERE / "analysis-committed" / family
    committed.mkdir(parents=True, exist_ok=True)

    extract_manifest_path = analysis / "anchor_extract_manifest.json"
    split_manifest_path = committed / "split_manifest.json"
    extract_tensors_path = analysis / "anchor_extract.safetensors"

    extract_manifest = json.loads(extract_manifest_path.read_text())
    assert extract_manifest["substrate"] == "bf16"
    assert extract_manifest["family"] == family
    hidden_dim = extract_manifest["hidden_size"]
    role_by_key = {rm["row_key"]: rm["role"] for rm in extract_manifest["rows"]}

    split_manifest = json.loads(split_manifest_path.read_text())
    split_by_key = {r["row_key"]: r["split"] for r in split_manifest["rows"]}

    from safetensors.numpy import load_file
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in load_file(str(extract_tensors_path)).items()}

    def direction_json(vector: np.ndarray, sigma: float, role: str, hs_index: int,
                        extra_prov: dict) -> dict:
        return {
            "schema_version": "mechinterp-direction/v1",
            "layer": hs_to_block(hs_index), "hidden_dim": hidden_dim,
            "normalized": True, "vector": [float(x) for x in vector],
            "raw_norm": 1.0, "intercept": 0.0, "mu": [0.0] * hidden_dim, "sigma": sigma,
            "calibration": {}, "recipe": {"source": "build_directions.py"},
            "provenance": {
                "role": role, "amendment": "j-space-cross-family-layer-contrast",
                "family": family, "substrate": "bf16",
                "base_model": cfg["checkpoint"]["repo"],
                "fit_population": "FIT split only (see split_manifest.json)",
                "hs_index": hs_index, "decoder_block_index": hs_to_block(hs_index),
                **extra_prov,
            },
        }

    report = {
        "family": family, "substrate": "bf16", "base_model": cfg["checkpoint"]["repo"],
        "hidden_dim": hidden_dim, "random_state": RANDOM_STATE,
        "reproducibility_verified": bool(args.verify_reproducible),
        "extract_manifest_sha256": _sha256_file(extract_manifest_path),
        "split_manifest_sha256": _sha256_file(split_manifest_path),
        "layers": {},
    }

    for hs_index in hs_list:
        fit1 = fit_all(fresh, role_by_key, split_by_key, RANDOM_STATE, hs_index)
        if args.verify_reproducible:
            fit2 = fit_all(fresh, role_by_key, split_by_key, RANDOM_STATE, hs_index)
            for name in ("u_d", "u_p", "caution_dir", "c_hat"):
                a, b = fit1[name], fit2[name]
                if not np.array_equal(a, b):
                    max_diff = float(np.max(np.abs(a - b)))
                    print(f"[build:{family}] REPRODUCIBILITY FAIL hs={hs_index} on {name}: "
                          f"max_abs_diff={max_diff}", file=sys.stderr)
                    return 1
            print(f"[build:{family}] reproducibility check PASS hs={hs_index}")

        u_d, u_p = fit1["u_d"], fit1["u_p"]
        caution_dir, c_hat = fit1["caution_dir"], fit1["c_hat"]
        known_fit, confab_fit = fit1["known_fit"], fit1["confab_fit"]
        unknown_refused, ctrl_fit_info = fit1["unknown_refused"], fit1["ctrl_fit_info"]

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
        layer_dir = committed / "layers" / layer_name
        source_dir = layer_dir / "source_directions"
        source_dir.mkdir(parents=True, exist_ok=True)

        u_d_json = direction_json(
            u_d, 1.0, "doubt_sensor_u_d", hs_index,
            {"method": "mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]), unit-normalized",
             "n_known_correct_answered_fit": len(known_fit), "n_unknown_refused": len(unknown_refused),
             "layer_label": layer_name, "mu_d_over_fit_pool": mu_d, "sigma_d_over_fit_pool": sigma_d,
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
             "cos_caution_dir_c_hat": cos_caution_chat, "mu_c_over_fit_pool": mu_c,
             "sigma_c_over_fit_pool": sigma_c, "n_fit_pool": len(fit_keys_labeled)},
        )
        (layer_dir / f"c_hat_{layer_name}.json").write_text(json.dumps(c_hat_json, indent=2))

        report["layers"][layer_name] = {
            "hs_index": hs_index, "decoder_block_index": hs_to_block(hs_index),
            "n_known_correct_answered_fit": len(known_fit), "n_confab_fit": len(confab_fit),
            "n_unknown_refused": len(unknown_refused), "cos_u_d_u_p": cos_ud_up,
            "cos_caution_dir_c_hat": cos_caution_chat,
            "mu_d": mu_d, "sigma_d": sigma_d, "mu_p": mu_p, "sigma_p": sigma_p,
            "mu_c": mu_c, "sigma_c": sigma_c,
        }

    (committed / "build_manifest_layers.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
