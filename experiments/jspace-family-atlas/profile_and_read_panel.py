#!/usr/bin/env python3
"""CPU-only workspace profile + read panel for one jspace-family-atlas cell.

READ-ONLY scoring over captures already written by `capture_atlas_cell.py`.
No GPU, no model loading, no generation. Two outputs per cell, both aggregate
and fitted-metadata only (never row text, never token IDs):

1. Per-layer eff_dim_frac (workspace profile), using the participation-ratio
   estimator ported byte-for-byte from
   `experiments/qwen35-4b-midband-doubt-snap/jlens_qwen35.py:183-193`
   (`_participation_ratio`) and its normalization convention at line 224
   (`effective_dim_frac = _participation_ratio(mat) / mat.shape[0]`).
   Stage A applies this to corpus-averaged JVP "push" vectors (5 random
   directions x double-backward); this atlas is capture-only (no gradients,
   per AMENDMENT.md's "no steering hooks" / "capture plus CPU scoring only"
   spend statement), so "the same estimator" is read here as the identical
   formula applied directly to the per-layer matrix of FIT-row anchor
   hidden-state vectors. See cell.yaml `profile:` block for the same note.

2. Per-layer held-out AUROC with a 2000-resample bootstrap CI for three
   read axes (doubt, caution, raw_refusal), each a unit mean-difference
   direction fit on FIT rows and scored by projection on held-out rows.

   CAVEAT (flag for lead review, restated from cell.yaml `read_panel:`):
   the fleet's own stratified_split assigns every unknown_refused-role row
   split="fit_only" -- there is no held-out partition for that role at all,
   for either cell. Since all three axes contrast something against refused
   (unknown_refused), a literal two-sided held-out AUROC is not achievable
   without re-splitting, which AMENDMENT.md forbids ("FIT/held-out labels
   carried through unchanged"). Each axis's "held-out AUROC" here scores the
   side that genuinely has held-out rows (known-correct for doubt; confab for
   caution; confab+known-correct for raw_refusal) against the SAME fit_only
   refused pool used to fit the direction. This is a real generalization test
   for the held-out class, but not a fully held-out test for the refused
   class -- report this caveat alongside every AUROC number, especially when
   comparing against the falsifier's >=0.80 threshold.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

BOOTSTRAP_SEED = 20260707


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
    order = np.argsort(np.concatenate([pos, neg]))
    ranks = np.empty_like(order, dtype=np.float64)
    combined = np.concatenate([pos, neg])[order]
    # average ranks for ties
    ranks_sorted = np.empty(len(combined), dtype=np.float64)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1] == combined[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks_sorted[i : j + 1] = avg_rank
        i = j + 1
    full_ranks = np.empty(len(combined), dtype=np.float64)
    full_ranks[order] = ranks_sorted
    pos_ranks = full_ranks[: n_pos]
    rank_sum_pos = pos_ranks.sum()
    u_stat = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return float(u_stat / (n_pos * n_neg))


def bootstrap_auroc_ci(
    scores: np.ndarray,
    labels: np.ndarray,
    n_resamples: int = 2000,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """2000-resample bootstrap CI, resampling within each class separately
    (keeps class balance stable across resamples; standard stratified
    bootstrap for AUROC)."""
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
    seed: int = BOOTSTRAP_SEED,
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


def run_cell(analysis_dir: Path, committed_dir: Path, n_resamples: int, seed: int) -> dict[str, Any]:
    split_manifest = json.loads((committed_dir / "split_manifest.json").read_text())
    rowmeta = split_manifest["rows"]
    capture_manifest = json.loads((committed_dir / "capture_manifest.json").read_text())
    n_hidden_states = capture_manifest["n_hidden_states"]

    captures = load_captures(analysis_dir)

    fit_rows = rows_by(rowmeta, split="fit") + rows_by(rowmeta, split="fit_only")
    known_fit = rows_by(rowmeta, role="known_correct_answered", split="fit")
    known_held = rows_by(rowmeta, role="known_correct_answered", split="held_out")
    confab_fit = rows_by(rowmeta, role="confab", split="fit")
    confab_held = rows_by(rowmeta, role="confab", split="held_out")
    refused_fit_only = rows_by(rowmeta, role="unknown_refused", split="fit_only")
    answered_fit = known_fit + confab_fit
    answered_held = known_held + confab_held

    per_layer: dict[int, dict[str, Any]] = {}
    for layer in range(n_hidden_states):
        fit_mat = build_layer_matrix(captures, fit_rows, layer)
        layer_profile = {"eff_dim_frac": eff_dim_frac(fit_mat), "n_fit_rows": int(fit_mat.shape[0])}

        known_fit_mat = build_layer_matrix(captures, known_fit, layer)
        known_held_mat = build_layer_matrix(captures, known_held, layer)
        confab_fit_mat = build_layer_matrix(captures, confab_fit, layer)
        confab_held_mat = build_layer_matrix(captures, confab_held, layer)
        refused_mat = build_layer_matrix(captures, refused_fit_only, layer)
        answered_fit_mat = build_layer_matrix(captures, answered_fit, layer)
        answered_held_mat = build_layer_matrix(captures, answered_held, layer)

        doubt = score_axis(
            pos_fit=known_fit_mat, neg_fit=refused_mat,
            pos_score=known_held_mat, neg_score=refused_mat,
            n_resamples=n_resamples, seed=seed,
        )
        caution = score_axis(
            pos_fit=refused_mat, neg_fit=confab_fit_mat,
            pos_score=refused_mat, neg_score=confab_held_mat,
            n_resamples=n_resamples, seed=seed,
        )
        raw_refusal = score_axis(
            pos_fit=refused_mat, neg_fit=answered_fit_mat,
            pos_score=refused_mat, neg_score=answered_held_mat,
            n_resamples=n_resamples, seed=seed,
        )

        per_layer[layer] = {
            "profile": layer_profile,
            "read_panel": {"doubt": doubt, "caution": caution, "raw_refusal": raw_refusal},
        }

    return {
        "cell_id": split_manifest["cell_id"],
        "n_hidden_states": n_hidden_states,
        "n_resamples": n_resamples,
        "seed": seed,
        "held_out_partial_caveat": (
            "unknown_refused is fit_only for both fleet cells (0 held-out "
            "rows by design); every axis's held-out AUROC scores the "
            "genuinely-held-out class against the same fit_only refused "
            "pool used to fit the direction, not a fully held-out contrast. "
            "See module docstring."
        ),
        "per_layer": per_layer,
    }


def cmd_score(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parent
    analysis_dir = root / "analysis" / args.cell_id
    committed_dir = root / "analysis-committed" / args.cell_id
    result = run_cell(analysis_dir, committed_dir, args.n_resamples, args.seed)
    out_path = committed_dir / "atlas_summary.json"
    write_json(out_path, result)
    print(f"[profile-and-read-panel] wrote {out_path}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_score = sub.add_parser("score", help="run profile + read panel for one captured cell")
    p_score.add_argument("--cell-id", required=True)
    p_score.add_argument("--n-resamples", type=int, default=2000)
    p_score.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    p_score.set_defaults(func=cmd_score)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
