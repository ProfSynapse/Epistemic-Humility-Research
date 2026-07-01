#!/usr/bin/env python3
"""Persist gate and dial probe directions from an Amendment-Z-style extraction dir.

CPU-ONLY. Given a completed extraction dir (produced by amendment_x_cross_model_extract.py
or any Amendment-Z-compatible extractor) containing:
  - rows.jsonl  (per-row metadata with `outcome` in {correct, wrong, hallucination,
                  known_answered} and `answered` flag)
  - <row_key>__pre.safetensors  (pre-anchor hidden states, all layers)
  - <row_key>__post.safetensors (post-answer hidden states, all layers)
  - manifest.json

Fits TWO probes (reusing the Amendment S/X scorer recipe exactly):
  GATE  — pre-anchor activation, binary: known_answered(1) vs hallucination(0)
           = answerability signal (Amendment X / W gate)
  DIAL  — post-answer activation, binary: correct(1) vs wrong(0)
           = correctness / trust signal (Amendment S / T / X dial)

For each probe, at the layer with the best OOF AUROC (swept across all available layers):
  1. Fits a FULL logistic regression (StandardScaler + LogisticRegression, C=1.0)
  2. Extracts the coefficient vector and UNIT-NORMS it -> probe direction d
  3. Records: layer index, calibration stats (mean/std of P(positive) for each class),
     provenance (source x_dir, model_tag, config_sha from manifest)

Outputs (per signal):
  direction_gate.safetensors  — {"d": float32 unit-norm direction vector}
  direction_gate.json         — layer, auroc, calibration, provenance
  direction_dial.safetensors  — {"d": float32 unit-norm direction vector}
  direction_dial.json         — layer, auroc, calibration, provenance

Alpha-scaling recipe: at inference, use
  alpha = base_alpha * (uncertainty_scale)
where uncertainty_scale is derived from the calibration stats so alpha=1 corresponds to
a 1-sigma shift relative to the correct/known class mean.

Design doc: docs/plans/confidence-steering-experiment.md
Pre-registration: NOT yet signed (Tier-2 Amendment required before any GPU run).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

try:
    from safetensors.torch import save_file as _torch_save_file
    import torch as _torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

try:
    from safetensors.numpy import load_file as _np_load_file
    _NUMPY_ST_AVAILABLE = True
except ImportError:
    _NUMPY_ST_AVAILABLE = False

try:
    from safetensors.torch import load_file as _torch_load_file
    _TORCH_ST_AVAILABLE = True
except ImportError:
    _TORCH_ST_AVAILABLE = False


# ---------------------------------------------------------------------------
# I/O helpers (reuse Amendment X position loading pattern)
# ---------------------------------------------------------------------------

def _safe_key(row_key: str) -> str:
    """Replicate the safe-key transform from the extractor."""
    return str(row_key).replace("::", "__").replace("|", "_")


def _load_shard(path: Path) -> dict[str, np.ndarray]:
    """Load a safetensors shard as numpy arrays (float64)."""
    if _TORCH_ST_AVAILABLE:
        t = _torch_load_file(str(path))
        return {k: np.asarray(v, dtype=np.float64) for k, v in t.items()}
    if _NUMPY_ST_AVAILABLE:
        t = _np_load_file(str(path))
        return {k: np.asarray(v, dtype=np.float64) for k, v in t.items()}
    raise ImportError("Neither safetensors.torch nor safetensors.numpy is available.")


def load_position_data(
    ext_dir: Path,
    position: str,
    positive_outcome: str,
    negative_outcome: str,
) -> tuple[dict[int, np.ndarray], np.ndarray]:
    """Load hidden states for rows matching positive/negative outcome labels.

    Mirrors the Amendment X `load_x_positions` logic but filters to a specific
    binary classification surface (e.g. known_answered vs hallucination).

    Returns
    -------
    X : dict[layer_idx -> np.ndarray shape (n, d)]
    y : np.ndarray of int (1=positive, 0=negative), length n
    """
    rows_path = ext_dir / "rows.jsonl"
    rows = [json.loads(ln) for ln in rows_path.open(encoding="utf-8") if ln.strip()]

    by_layer: dict[int, list] = {}
    labels: list[int] = []

    for r in rows:
        if not r.get("answered"):
            continue
        outcome = r.get("outcome")
        if outcome not in (positive_outcome, negative_outcome):
            continue
        sk = _safe_key(r["row_key"])
        shard = ext_dir / f"{sk}__{position}.safetensors"
        if not shard.exists():
            continue
        tensors = _load_shard(shard)
        for name, vec in tensors.items():
            li = int(name[1:])  # 'L35' -> 35
            by_layer.setdefault(li, []).append(vec)
        labels.append(1 if outcome == positive_outcome else 0)

    if not labels:
        raise ValueError(
            f"No rows found for ({positive_outcome}, {negative_outcome}) at position={position} "
            f"in {ext_dir}. Check that the extraction dir has the correct outcome labels."
        )

    X = {layer: np.vstack(vs) for layer, vs in by_layer.items()}
    y = np.asarray(labels, dtype=int)
    return X, y


# ---------------------------------------------------------------------------
# Probe fitting (verbatim recipe from Amendment S `oof_probe`)
# ---------------------------------------------------------------------------

def oof_probe(X: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """5-fold stratified CV logistic regression; out-of-fold P(positive).

    Identical recipe to Amendment S / X oof_probe: StandardScaler + C=1.0 logistic,
    so directions are comparable across probe families.
    """
    p = np.full(len(y), np.nan)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=1.0, max_iter=2000)
        clf.fit(sc.transform(X[tr]), y[tr])
        p[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    assert not np.isnan(p).any(), "NaN in OOF scores — check for degenerate classes"
    return p


def sweep_layers(
    X_by_layer: dict[int, np.ndarray],
    y: np.ndarray,
    seed: int,
) -> dict[int, float]:
    """Sweep all layers, returning {layer: oof_auroc}."""
    surface: dict[int, float] = {}
    for layer in sorted(X_by_layer):
        oof = oof_probe(X_by_layer[layer], y, seed)
        surface[layer] = float(roc_auc_score(y, oof))
    return surface


def fit_full_probe(
    X: np.ndarray, y: np.ndarray
) -> tuple[StandardScaler, LogisticRegression]:
    """Full-data fit (not OOF) for direction extraction and cold application."""
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(C=1.0, max_iter=2000)
    clf.fit(sc.transform(X), y)
    return sc, clf


def extract_unit_direction(clf: LogisticRegression) -> np.ndarray:
    """Extract and unit-norm the logistic coefficient vector.

    The coefficient vector points in the direction of increasing P(positive=1)
    in standardized space. Unit-norming makes alpha-scaling interpretable as
    "number of sigma shifts along the probe axis."
    """
    coef = clf.coef_[0]  # shape (d,)
    norm = np.linalg.norm(coef)
    if norm < 1e-12:
        raise ValueError("Probe coefficient vector is nearly zero — degenerate fit.")
    return (coef / norm).astype(np.float32)


def calibration_stats(
    sc: StandardScaler,
    clf: LogisticRegression,
    X: np.ndarray,
    y: np.ndarray,
) -> dict:
    """Compute mean/std of P(positive) per class for alpha calibration.

    The steer harness can use these to set alpha proportional to distance
    from the positive-class mean (measured uncertainty).
    """
    probs = clf.predict_proba(sc.transform(X))[:, 1]
    pos_probs = probs[y == 1]
    neg_probs = probs[y == 0]
    return {
        "positive_mean": float(pos_probs.mean()),
        "positive_std": float(pos_probs.std()),
        "negative_mean": float(neg_probs.mean()),
        "negative_std": float(neg_probs.std()),
        "separation": float(pos_probs.mean() - neg_probs.mean()),
        "n_positive": int((y == 1).sum()),
        "n_negative": int((y == 0).sum()),
    }


# ---------------------------------------------------------------------------
# Saving helpers
# ---------------------------------------------------------------------------

def _save_direction_safetensors(path: Path, d: np.ndarray) -> None:
    """Save the unit-norm direction vector to safetensors format."""
    if _TORCH_AVAILABLE:
        import torch
        save_dict = {"d": torch.from_numpy(d.astype(np.float32))}
        _torch_save_file(save_dict, str(path))
    else:
        # Fallback: numpy raw save (not safetensors; log a warning)
        np.save(str(path).replace(".safetensors", ".npy"), d)
        print(f"[persist_probe_direction] WARNING: torch not available; "
              f"saved {path.stem} as .npy instead of .safetensors", flush=True)


# ---------------------------------------------------------------------------
# Per-signal persistence entry point
# ---------------------------------------------------------------------------

def persist_signal(
    signal_name: str,
    ext_dir: Path,
    out_dir: Path,
    position: str,
    positive_outcome: str,
    negative_outcome: str,
    manifest: dict,
    seed: int,
    forced_layer: Optional[int] = None,
) -> dict:
    """Fit, sweep, and persist one probe direction.

    Parameters
    ----------
    signal_name : 'gate' or 'dial'
    ext_dir     : Amendment-Z extraction dir
    out_dir     : where to write direction_<signal>.{safetensors,json}
    position    : 'pre' or 'post'
    positive_outcome, negative_outcome : outcome labels for binary fit
    manifest    : parsed manifest.json from ext_dir
    seed        : RNG seed (matches scorer convention)
    forced_layer: if set, skip sweep and use this layer

    Returns
    -------
    result dict (mirrored to direction_<signal>.json)
    """
    print(f"[persist_probe_direction] {signal_name}: loading {position} at {ext_dir} ...",
          flush=True)
    X_by_layer, y = load_position_data(
        ext_dir, position, positive_outcome, negative_outcome
    )
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    print(f"[persist_probe_direction] {signal_name}: n={len(y)} "
          f"(+={n_pos} -= {n_neg})", flush=True)

    if forced_layer is not None:
        best_layer = forced_layer
        surface = {forced_layer: None}
        print(f"[persist_probe_direction] {signal_name}: using forced layer {best_layer}",
              flush=True)
    else:
        print(f"[persist_probe_direction] {signal_name}: sweeping {len(X_by_layer)} layers ...",
              flush=True)
        surface = sweep_layers(X_by_layer, y, seed)
        best_layer = max(surface, key=surface.get)
        best_auroc = surface[best_layer]
        print(f"[persist_probe_direction] {signal_name}: best layer={best_layer} "
              f"auroc={best_auroc:.4f}", flush=True)

    X_best = X_by_layer[best_layer]
    sc, clf = fit_full_probe(X_best, y)
    d = extract_unit_direction(clf)
    cal = calibration_stats(sc, clf, X_best, y)
    best_auroc = surface[best_layer]

    result = {
        "signal": signal_name,
        "position": position,
        "positive_outcome": positive_outcome,
        "negative_outcome": negative_outcome,
        "best_layer": best_layer,
        "auroc_surface": {str(k): round(v, 4) for k, v in sorted(surface.items())
                          if v is not None},
        "auroc_at_best_layer": round(float(best_auroc), 4) if best_auroc is not None else None,
        "calibration": cal,
        "direction_shape": list(d.shape),
        "direction_norm": float(np.linalg.norm(d)),
        "provenance": {
            "source_x_dir": str(ext_dir),
            "model_tag": manifest.get("model_tag", "unknown"),
            "base_model": manifest.get("base_model", "unknown"),
            "config_sha": manifest.get("config_sha", "unknown"),
            "amendment": manifest.get("amendment", "unknown"),
            "persist_seed": seed,
        },
    }

    st_path = out_dir / f"direction_{signal_name}.safetensors"
    json_path = out_dir / f"direction_{signal_name}.json"
    _save_direction_safetensors(st_path, d)
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[persist_probe_direction] {signal_name}: wrote {st_path} + {json_path}",
          flush=True)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--x-dir", required=True, type=Path,
        help="Amendment-Z-style extraction dir (rows.jsonl + safetensors + manifest.json)"
    )
    ap.add_argument(
        "--out-dir", type=Path, default=None,
        help="Output dir for direction_*.{safetensors,json}. Default: <x-dir>/directions/"
    )
    ap.add_argument(
        "--gate-layer", type=int, default=None,
        help="Force gate probe to this layer (skip sweep). Default: sweep all layers."
    )
    ap.add_argument(
        "--dial-layer", type=int, default=None,
        help="Force dial probe to this layer (skip sweep). Default: sweep all layers."
    )
    ap.add_argument(
        "--seed", type=int, default=20260630,
        help="RNG seed for CV (matches scorer convention)"
    )
    ap.add_argument(
        "--gate-pos-outcome", default="known_answered",
        help="Positive class label for the gate (default: known_answered)"
    )
    ap.add_argument(
        "--gate-neg-outcome", default="hallucination",
        help="Negative class label for the gate (default: hallucination)"
    )
    ap.add_argument(
        "--dial-pos-outcome", default="correct",
        help="Positive class label for the dial (default: correct)"
    )
    ap.add_argument(
        "--dial-neg-outcome", default="wrong",
        help="Negative class label for the dial (default: wrong)"
    )
    a = ap.parse_args(argv)

    x_dir = a.x_dir.resolve()
    out_dir = (a.out_dir or x_dir / "directions").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = x_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"[persist_probe_direction] ERROR: manifest.json not found at {x_dir}",
              flush=True)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_tag = manifest.get("model_tag", "unknown")
    print(f"[persist_probe_direction] model_tag={model_tag}", flush=True)

    # GATE: pre-anchor answerability (known_answered vs hallucination)
    gate_result = persist_signal(
        signal_name="gate",
        ext_dir=x_dir,
        out_dir=out_dir,
        position="pre",
        positive_outcome=a.gate_pos_outcome,
        negative_outcome=a.gate_neg_outcome,
        manifest=manifest,
        seed=a.seed,
        forced_layer=a.gate_layer,
    )

    # DIAL: post-answer correctness (correct vs wrong)
    dial_result = persist_signal(
        signal_name="dial",
        ext_dir=x_dir,
        out_dir=out_dir,
        position="post",
        positive_outcome=a.dial_pos_outcome,
        negative_outcome=a.dial_neg_outcome,
        manifest=manifest,
        seed=a.seed,
        forced_layer=a.dial_layer,
    )

    summary = {
        "model_tag": model_tag,
        "gate": {
            "layer": gate_result["best_layer"],
            "auroc": gate_result["auroc_at_best_layer"],
        },
        "dial": {
            "layer": dial_result["best_layer"],
            "auroc": dial_result["auroc_at_best_layer"],
        },
        "out_dir": str(out_dir),
    }
    print(f"\n[persist_probe_direction] DONE:\n{json.dumps(summary, indent=2)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
