#!/usr/bin/env python3
"""Stage 3 (fit, supplementary held-out AUROC) + Stage 5 (compare) for
base-refusal-direction-under-contract.

The Stage-3 direction JSON itself must come from the PINNED
`experiments/common/mechinterp/residual_caution_direction.py` CLI, invoked
unmodified (see RUNBOOK/report). This script:

  1. Loads that JSON's theta (sanity: recomputes the identical mass-mean
     theta from the raw extraction to confirm it matches the CLI output
     bit-for-bit up to float precision).
  2. Computes a supplementary HELD-OUT AUROC (BR-G0 `fit_holdout_auroc_min:
     0.80`) that residual_caution_direction.py itself does NOT produce (its
     own docstring: "prompt_token_auroc is an in-sample construction sanity
     check, not a held-out claim"). Uses the SAME 5-fold stratified,
     refit-per-fold, project-held-out-knowns procedure
     reconstruct_section5_geometry.py's `aurocs_one_seed()` implements for
     the Section-5 caution AUROC (mass-mean, not logistic).
  3. Stage 5: |cos| between the base direction and each of the three
     trained-regimen directions from trained_references.py's output (mean
     reported per BR-G1); |cos| to the GRPO-v2 doubt/known-unknown axis
     (descriptive, orthogonality, not adjudicated).
  4. Permutation floor: "refits of the same estimator on shuffled labels"
     (manuscript Statistics section) -- shuffles the base's own known-row
     refuse/answer labels N times, refits the mass-mean direction each time,
     computes |cos| to each REAL trained reference, and reports the mean as
     the floor for THIS (mass-mean, raw-space) estimator. NOTE: this is NOT
     the published ~0.014 figure -- that number comes from a DIFFERENT,
     unpinned script (caution_axis_transfer.py: logistic regression in a
     shared-whitened cross-checkpoint frame, broader known-answered class).
     Flagged as a methodology anomaly in the run report; not reconciled here.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

ROOT = Path(__file__).resolve().parents[3]
CELL_DIR = ROOT / "experiments/base-refusal-direction-under-contract"
LAYER = 35


def unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def load_base_extraction(labels_path: Path, ext_dir: Path):
    rows = [json.loads(l) for l in labels_path.open(encoding="utf-8") if l.strip()]
    X, cells, keys = [], [], []
    for r in rows:
        stem = r["row_key"].replace("::", "__")
        p = ext_dir / f"{stem}__h_base.safetensors"
        if not p.exists():
            raise FileNotFoundError(f"missing extraction tensor for {r['row_key']}: {p}")
        X.append(load_file(str(p))[f"L{LAYER}"].astype(np.float64))
        cells.append(r["behavior_cell"])
        keys.append(r["row_key"])
    return np.vstack(X), np.asarray(cells), keys


def mass_mean_direction(x_pos: np.ndarray, x_neg: np.ndarray) -> np.ndarray:
    return unit(x_pos.mean(0) - x_neg.mean(0))


def held_out_auroc(X: np.ndarray, cells: np.ndarray, seed: int, n_folds: int = 5) -> dict:
    """5-fold stratified, mass-mean direction refit per fold on TRAIN rows,
    held-out knowns scored by projection -- reconstruct_section5_geometry.py's
    aurocs_one_seed() pattern, applied to the two-cell (kr/ka) base contrast."""
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold

    y = (cells == "known_refused").astype(int)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    scores = np.full(len(y), np.nan)
    for tr, te in skf.split(X, y):
        pos = X[tr][y[tr] == 1]
        neg = X[tr][y[tr] == 0]
        theta = mass_mean_direction(pos, neg)
        scores[te] = X[te] @ theta
    assert not np.isnan(scores).any()
    auroc = roc_auc_score(y, scores)
    return {"auroc": float(max(auroc, 1 - auroc)), "n_folds": n_folds, "seed": seed}


def permutation_floor(X: np.ndarray, cells: np.ndarray, trained: dict[str, np.ndarray],
                      seed: int, n_reps: int = 200) -> dict:
    rng = np.random.default_rng(seed)
    y = (cells == "known_refused").astype(int)
    n_pos = int(y.sum())
    idx = np.arange(len(y))
    per_direction: dict[str, list[float]] = {name: [] for name in trained}
    for _ in range(n_reps):
        shuf = rng.permutation(idx)
        pos_idx = shuf[:n_pos]
        neg_idx = shuf[n_pos:]
        null_theta = mass_mean_direction(X[pos_idx], X[neg_idx])
        for name, theta in trained.items():
            per_direction[name].append(abs(float(null_theta @ theta)))
    means = {name: float(np.mean(v)) for name, v in per_direction.items()}
    overall = float(np.mean([m for m in means.values()]))
    return {"n_reps": n_reps, "seed": seed, "per_trained_direction_mean": means,
            "overall_mean": overall}


def main() -> int:
    labels_path = CELL_DIR / "analysis/labels/known_rows.jsonl"
    ext_dir = CELL_DIR / "analysis/hidden_states/base_prc_L35"
    fit_json_path = CELL_DIR / "analysis/directions/base_prc_refusal_direction_L35.json"
    directions_dir = CELL_DIR / "analysis/directions"

    X, cells, keys = load_base_extraction(labels_path, ext_dir)
    n_kr = int((cells == "known_refused").sum())
    n_ka = int((cells == "known_correct_answered").sum())

    # Sanity: recompute the mass-mean direction directly and compare to the
    # pinned CLI's own JSON output (bit-identical construction, cross-check
    # only -- the JSON is the artifact of record).
    pos = X[cells == "known_refused"]
    neg = X[cells == "known_correct_answered"]
    theta_recomputed = mass_mean_direction(pos, neg)

    fit_json = json.loads(fit_json_path.read_text(encoding="utf-8"))
    theta_cli = np.asarray(fit_json["theta"], dtype=np.float64)
    theta_cli_unit = theta_cli / np.linalg.norm(theta_cli)
    cli_vs_recompute_cos = float(theta_cli_unit @ theta_recomputed)

    br_g0 = held_out_auroc(X, cells, seed=20260817)

    trained_dir = ROOT / "experiments/base-refusal-direction-under-contract/analysis/directions"
    trained = {
        name: np.load(trained_dir / f"trained_ref__{name}__L35_theta.npy")
        for name in ("clean_sft", "sft_grpo_dpo", "sft_grpo_v2")
    }
    doubt = np.load(trained_dir / "trained_ref__sft_grpo_v2__doubt__L35_theta.npy")

    cos_to_trained = {name: abs(float(theta_cli_unit @ t)) for name, t in trained.items()}
    mean_cos = float(np.mean(list(cos_to_trained.values())))
    cos_to_doubt = abs(float(theta_cli_unit @ doubt))

    floor = permutation_floor(X, cells, trained, seed=20260817, n_reps=200)

    result = {
        "n_rows_loaded": int(len(X)),
        "n_known_refused": n_kr,
        "n_known_correct_answered": n_ka,
        "cli_theta_vs_recomputed_theta_cos_sanity": round(cli_vs_recompute_cos, 6),
        "br_g0_held_out_auroc": br_g0,
        "br_g0_min_rows_per_class_100_pass": bool(n_kr >= 100 and n_ka >= 100),
        "br_g0_fit_holdout_auroc_min_0.80_pass": bool(br_g0["auroc"] >= 0.80),
        "cos_to_trained_directions": {k: round(v, 4) for k, v in cos_to_trained.items()},
        "mean_cos_to_trained_directions": round(mean_cos, 4),
        "cos_to_grpo_v2_doubt_axis_descriptive": round(cos_to_doubt, 4),
        "permutation_floor_matched_methodology": {
            "n_reps": floor["n_reps"],
            "seed": floor["seed"],
            "per_trained_direction_mean": {k: round(v, 4) for k, v in floor["per_trained_direction_mean"].items()},
            "overall_mean": round(floor["overall_mean"], 4),
        },
        "methodology_anomaly_note": (
            "This permutation floor uses the SAME mass-mean estimator as the "
            "base-vs-trained comparison (matched methodology). It is NOT the "
            "published ~0.014 figure from caution_axis_transfer.py, which uses "
            "a different (logistic, shared-whitened-frame, broader "
            "known-answered class) estimator that is not pinned by this cell's "
            "instrument. See run report."
        ),
    }

    out_path = CELL_DIR / "analysis" / "br_compare_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
