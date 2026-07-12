#!/usr/bin/env python3
"""CPU-only workspace profile + read panel for one family-atlas cell.

READ-ONLY scoring over captures already written by
`capture_family_atlas_cell.py`. No GPU, no model loading, no generation.
Generalized from `experiments/jspace-family-atlas/profile_and_read_panel.py`
(the resolved llama32_3b/mistral7b atlas); nothing in this script is
per-model or per-family, it only reads whatever `capture_manifest.json` /
`split_manifest.json` / captures a given cell wrote.

Three outputs per cell, all aggregate and fitted-metadata only (never row
text, never token IDs):

1. Per-layer eff_dim_frac (workspace profile): the participation-ratio
   estimator (ported byte-for-byte from
   `experiments/qwen35-4b-midband-doubt-snap/jlens_qwen35.py:183-193`
   `_participation_ratio`, normalization convention at line 224:
   `effective_dim_frac = _participation_ratio(mat) / mat.shape[0]`) applied
   directly to the per-layer matrix of FIT-row anchor hidden-state vectors.
   Estimator-input note (carried over from jspace-family-atlas, still true
   for every future atlas cell unless a signed amendment changes it): the
   estimator formula is byte-identical to Stage A's, but Stage A applies it
   to corpus-averaged JVP "push" vectors from a gradient-based J-lens, which
   a capture-only atlas cannot reproduce. This profile is therefore a
   representation-variance PR, comparable ACROSS this instrument's own
   cells only, never across a JVP-based profile from a different
   instrument.

2. Per-layer held-out AUROC with a bootstrap CI for three read axes (doubt,
   caution, raw_refusal), each a unit mean-difference direction fit on FIT
   rows and scored by projection on held-out rows.

   The program's row-role taxonomy this instrument assumes: `confab`,
   `known_correct_answered`, `unknown_refused`, with split labels `fit`,
   `held_out`, `fit_only`. If a source pool's `unknown_refused` role is
   `fit_only` (no held-out partition for that role at all -- true of every
   cell run through this instrument so far), `_split_refused_pool` divides
   it deterministically into `refused_fit` (direction fitting, alongside FIT
   known/confab rows) and `refused_eval` (scoring, alongside held-out
   known/confab rows), so every reported panel AUROC is two-sided held-out.
   If a future pool's `unknown_refused` role instead already carries real
   `held_out` rows, pass `--no-split-refused` and this script uses those
   rows directly instead of subdividing the fit_only pool.

3. Per-layer random-direction control: a fixed, deterministically-seeded
   random unit direction per layer, scored with the SAME best-orientation
   AUROC (`max(auroc, 1-auroc)`, since a random direction carries no
   meaningful sign) against the SAME three held-out score populations used
   by the read panel (`ref_vs_known`, `ref_vs_confab`, `ref_vs_answered`).
   In jspace-family-atlas this was a post-hoc, lab-notebook-tier diagnostic
   (`analysis-committed/random_direction_control.json`, run by hand after
   the panel raised a norm/position-confound concern on the doubt axis at
   the final-prompt-token anchor). It is promoted here to a standard part
   of `atlas_summary.json`: every future atlas cell gets this control for
   free, without anyone having to remember to ask for it. Read the doubt
   axis's AUROC against its own layer's `ref_vs_known` control value, not
   against 0.5, whenever the control reads meaningfully above chance.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_SEED = 20260707


def split_refused_pool(row_keys: list[str], seed: int = DEFAULT_SEED) -> tuple[list[str], list[str]]:
    """Deterministically subdivide a fit_only role's row-key pool into a
    fitting half and a scoring half, so every read-panel axis's held-out
    AUROC is two-sided held-out. Sort first for a stable base ordering, then
    shuffle with `random.Random(seed)`, then cut once: first floor(n/2) rows
    -> fit half, the rest -> eval half. Disjoint and deterministic by
    construction."""
    ordered = sorted(row_keys)
    rng = random.Random(seed)
    rng.shuffle(ordered)
    n_fit = len(ordered) // 2
    return ordered[:n_fit], ordered[n_fit:]


# ---------------------------------------------------------------------------
# Participation-ratio / eff_dim_frac estimator.
# Byte-for-byte port of experiments/qwen35-4b-midband-doubt-snap/
# jlens_qwen35.py:183-193 (_participation_ratio), operating here on a
# (n_rows, hidden_dim) matrix of anchor hidden-state vectors rather than on
# corpus-averaged JVP push vectors. See module docstring.
# ---------------------------------------------------------------------------

def participation_ratio(mat: np.ndarray) -> float:
    x = mat.astype(np.float64)
    x = x - x.mean(axis=0, keepdims=True)
    n = x.shape[0]
    gram = (x @ x.T) / max(n - 1, 1)
    eigvals = np.linalg.eigvalsh(gram)
    eigvals = np.clip(eigvals, 0.0, None)
    s1 = eigvals.sum()
    s2 = (eigvals ** 2).sum()
    if s2 <= 1e-30:
        return 1.0
    return float((s1 * s1) / s2)


def eff_dim_frac(mat: np.ndarray) -> float:
    """jlens_qwen35.py:224 normalization convention: PR / n_samples."""
    n = mat.shape[0]
    if n < 2:
        raise ValueError("eff_dim_frac needs at least 2 rows")
    return participation_ratio(mat) / float(n)


# ---------------------------------------------------------------------------
# Read-panel axis: unit mean-difference direction, AUROC + bootstrap CI.
# ---------------------------------------------------------------------------

def unit(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    return v / norm if norm else v


def fit_axis_direction(pos_fit: np.ndarray, neg_fit: np.ndarray) -> np.ndarray:
    """unit(mean(positive FIT) - mean(negative FIT))."""
    if pos_fit.shape[0] == 0 or neg_fit.shape[0] == 0:
        raise ValueError("cannot fit an axis direction with an empty class")
    return unit(pos_fit.mean(axis=0) - neg_fit.mean(axis=0))


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUROC (Mann-Whitney U / n_pos / n_neg). labels are 0/1."""
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    n_pos, n_neg = pos.shape[0], neg.shape[0]
    if n_pos == 0 or n_neg == 0:
        raise ValueError("AUROC needs at least one row in each class")
    combined = np.concatenate([pos, neg])
    order = np.argsort(combined)
    ranks_sorted = np.empty(len(combined), dtype=np.float64)
    sorted_vals = combined[order]
    i = 0
    while i < len(sorted_vals):
        j = i
        while j + 1 < len(sorted_vals) and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks_sorted[i : j + 1] = avg_rank
        i = j + 1
    full_ranks = np.empty(len(combined), dtype=np.float64)
    full_ranks[order] = ranks_sorted
    pos_ranks = full_ranks[:n_pos]
    rank_sum_pos = pos_ranks.sum()
    u_stat = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return float(u_stat / (n_pos * n_neg))


def bootstrap_auroc_ci(
    scores: np.ndarray,
    labels: np.ndarray,
    n_resamples: int = 2000,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Bootstrap CI, resampling within each class separately (keeps class
    balance stable across resamples; standard stratified bootstrap for
    AUROC)."""
    rng = np.random.default_rng(seed)
    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    if pos_idx.shape[0] == 0 or neg_idx.shape[0] == 0:
        raise ValueError("bootstrap needs at least one row in each class")
    point = auroc(scores, labels)
    resampled = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        bp = rng.choice(pos_idx, size=pos_idx.shape[0], replace=True)
        bn = rng.choice(neg_idx, size=neg_idx.shape[0], replace=True)
        idx = np.concatenate([bp, bn])
        boot_labels = np.concatenate(
            [np.ones(bp.shape[0]), np.zeros(bn.shape[0])]
        )
        resampled[i] = auroc(scores[idx], boot_labels)
    lo, hi = np.percentile(resampled, [2.5, 97.5])
    return {
        "point": point,
        "ci95_lo": float(lo),
        "ci95_hi": float(hi),
        "n_resamples": n_resamples,
        "seed": seed,
        "n_pos": int(pos_idx.shape[0]),
        "n_neg": int(neg_idx.shape[0]),
    }


def score_axis(
    pos_fit: np.ndarray,
    neg_fit: np.ndarray,
    pos_score: np.ndarray,
    neg_score: np.ndarray,
    n_resamples: int = 2000,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    direction = fit_axis_direction(pos_fit, neg_fit)
    scores = np.concatenate([pos_score, neg_score]) @ direction
    labels = np.concatenate(
        [np.ones(pos_score.shape[0]), np.zeros(neg_score.shape[0])]
    )
    result = bootstrap_auroc_ci(scores, labels, n_resamples=n_resamples, seed=seed)
    result["direction_norm_check"] = float(np.linalg.norm(direction))
    return result


# ---------------------------------------------------------------------------
# Random-direction control: standard part of the panel output (see module
# docstring point 3). No fitting, no bootstrap CI (a fixed random direction
# has no sampling distribution to bound the same way a fitted direction
# does); best-orientation AUROC only.
# ---------------------------------------------------------------------------

def random_unit_direction(hidden_dim: int, layer: int, seed: int) -> np.ndarray:
    """Deterministic per-layer random unit direction. Independent of row
    data and of any axis direction; the same (hidden_dim, layer, seed)
    always reproduces the same vector."""
    rng = np.random.default_rng([seed, layer])
    v = rng.normal(size=hidden_dim)
    return unit(v)


def best_orientation_auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    a = auroc(scores, labels)
    return max(a, 1.0 - a)


def score_random_direction_contrast(
    direction: np.ndarray, pos_score: np.ndarray, neg_score: np.ndarray
) -> float:
    scores = np.concatenate([pos_score, neg_score]) @ direction
    labels = np.concatenate(
        [np.ones(pos_score.shape[0]), np.zeros(neg_score.shape[0])]
    )
    return best_orientation_auroc(scores, labels)


# ---------------------------------------------------------------------------
# Per-cell driver: load captures, split_manifest, run profile + read panel.
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_captures(analysis_dir: Path) -> dict[str, dict[int, np.ndarray]]:
    """Returns {row_key: {layer_int: vector}}."""
    from safetensors.numpy import load_file

    cap_dir = analysis_dir / "atlas_capture"
    index = load_jsonl(cap_dir / "capture.jsonl")
    out: dict[str, dict[int, np.ndarray]] = {}
    for rec in index:
        tensors = load_file(str(cap_dir / rec["file"]))
        layers: dict[int, np.ndarray] = {}
        prefix = "anchor__L"
        for key, vec in tensors.items():
            if key.startswith(prefix):
                layer = int(key[len(prefix) :])
                layers[layer] = vec.astype(np.float64)
        out[rec["id"]] = layers
    return out


def build_layer_matrix(
    captures: dict[str, dict[int, np.ndarray]],
    row_keys: list[str],
    layer: int,
) -> np.ndarray:
    return np.stack([captures[k][layer] for k in row_keys if k in captures])


def rows_by(rowmeta: list[dict[str, Any]], **filters: Any) -> list[str]:
    out = []
    for r in rowmeta:
        if all(r.get(k) == v for k, v in filters.items()):
            out.append(r["row_key"])
    return out


def run_cell(
    analysis_dir: Path,
    committed_dir: Path,
    n_resamples: int,
    seed: int,
    split_refused: bool = True,
) -> dict[str, Any]:
    split_manifest = json.loads((committed_dir / "split_manifest.json").read_text())
    rowmeta = split_manifest["rows"]
    capture_manifest = json.loads((committed_dir / "capture_manifest.json").read_text())
    n_hidden_states = capture_manifest["n_hidden_states"]
    hidden_dim = capture_manifest.get("hidden_size")

    captures = load_captures(analysis_dir)

    fit_rows = rows_by(rowmeta, split="fit") + rows_by(rowmeta, split="fit_only")
    known_fit = rows_by(rowmeta, role="known_correct_answered", split="fit")
    known_held = rows_by(rowmeta, role="known_correct_answered", split="held_out")
    confab_fit = rows_by(rowmeta, role="confab", split="fit")
    confab_held = rows_by(rowmeta, role="confab", split="held_out")

    if split_refused:
        refused_fit_only = rows_by(rowmeta, role="unknown_refused", split="fit_only")
        refused_fit, refused_eval = split_refused_pool(refused_fit_only, seed=seed)
        refused_pool_note = (
            "sorted row_key, random.Random(seed).shuffle, first floor(n/2) "
            "-> refused_fit, remainder -> refused_eval"
        )
    else:
        refused_fit_only = []
        refused_fit = rows_by(rowmeta, role="unknown_refused", split="fit")
        refused_eval = rows_by(rowmeta, role="unknown_refused", split="held_out")
        refused_pool_note = "unknown_refused already carries real fit/held_out rows; no subdivision applied"

    answered_fit = known_fit + confab_fit
    answered_held = known_held + confab_held

    assert not (set(refused_fit) & set(refused_eval)), "refused_fit/refused_eval must be disjoint"

    per_layer: dict[int, dict[str, Any]] = {}
    for layer in range(n_hidden_states):
        fit_mat = build_layer_matrix(captures, fit_rows, layer)
        layer_profile = {"eff_dim_frac": eff_dim_frac(fit_mat), "n_fit_rows": int(fit_mat.shape[0])}

        known_fit_mat = build_layer_matrix(captures, known_fit, layer)
        known_held_mat = build_layer_matrix(captures, known_held, layer)
        confab_fit_mat = build_layer_matrix(captures, confab_fit, layer)
        confab_held_mat = build_layer_matrix(captures, confab_held, layer)
        refused_fit_mat = build_layer_matrix(captures, refused_fit, layer)
        refused_eval_mat = build_layer_matrix(captures, refused_eval, layer)
        answered_fit_mat = build_layer_matrix(captures, answered_fit, layer)
        answered_held_mat = build_layer_matrix(captures, answered_held, layer)

        doubt = score_axis(
            pos_fit=known_fit_mat, neg_fit=refused_fit_mat,
            pos_score=known_held_mat, neg_score=refused_eval_mat,
            n_resamples=n_resamples, seed=seed,
        )
        caution = score_axis(
            pos_fit=refused_fit_mat, neg_fit=confab_fit_mat,
            pos_score=refused_eval_mat, neg_score=confab_held_mat,
            n_resamples=n_resamples, seed=seed,
        )
        raw_refusal = score_axis(
            pos_fit=refused_fit_mat, neg_fit=answered_fit_mat,
            pos_score=refused_eval_mat, neg_score=answered_held_mat,
            n_resamples=n_resamples, seed=seed,
        )

        layer_hidden_dim = hidden_dim or fit_mat.shape[1]
        rand_dir = random_unit_direction(layer_hidden_dim, layer, seed)
        random_direction_control = {
            "ref_vs_known": score_random_direction_contrast(rand_dir, refused_eval_mat, known_held_mat),
            "ref_vs_confab": score_random_direction_contrast(rand_dir, refused_eval_mat, confab_held_mat),
            "ref_vs_answered": score_random_direction_contrast(rand_dir, refused_eval_mat, answered_held_mat),
        }

        per_layer[layer] = {
            "profile": layer_profile,
            "read_panel": {"doubt": doubt, "caution": caution, "raw_refusal": raw_refusal},
            "random_direction_control": random_direction_control,
        }

    return {
        "cell_id": split_manifest["cell_id"],
        "n_hidden_states": n_hidden_states,
        "n_resamples": n_resamples,
        "seed": seed,
        "refused_pool_split": {
            "n_refused_fit_only_total": len(refused_fit_only) if split_refused else None,
            "n_refused_fit": len(refused_fit),
            "n_refused_eval": len(refused_eval),
            "method": refused_pool_note,
        },
        "held_out_note": (
            "Every read-panel axis's held-out AUROC is two-sided held-out: "
            "known/confab use the source pool's own FIT/held-out split "
            "unchanged; unknown_refused is either subdivided (split_refused=True) "
            "or already carries real held-out rows (split_refused=False)."
        ),
        "random_direction_control_note": (
            "Best-orientation AUROC (max(auroc, 1-auroc)) for a fixed, "
            "deterministically-seeded random unit direction per layer, "
            "scored against the same held-out populations as the read "
            "panel. Read any axis's AUROC against this control's matching "
            "contrast, not against 0.5, whenever the control reads "
            "meaningfully above chance (a norm/position confound at the "
            "capture anchor, not a property of the fitted axis)."
        ),
        "per_layer": per_layer,
    }


def cmd_score(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parent
    analysis_dir = root / "analysis" / args.cell_id
    committed_dir = root / "analysis-committed" / args.cell_id
    result = run_cell(
        analysis_dir,
        committed_dir,
        args.n_resamples,
        args.seed,
        split_refused=not args.no_split_refused,
    )
    out_path = committed_dir / "atlas_summary.json"
    write_json(out_path, result)
    print(f"[profile-and-read-family-atlas-panel] wrote {out_path}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_score = sub.add_parser("score", help="run profile + read panel for one captured cell")
    p_score.add_argument("--cell-id", required=True)
    p_score.add_argument("--n-resamples", type=int, default=2000)
    p_score.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p_score.add_argument(
        "--no-split-refused",
        action="store_true",
        help="Use unknown_refused's own fit/held_out rows directly instead of subdividing a fit_only pool.",
    )
    p_score.set_defaults(func=cmd_score)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
