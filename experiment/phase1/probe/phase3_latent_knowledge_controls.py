#!/usr/bin/env python3
"""Hardening controls for the latent-knowledge READ probe (GPU-free).

The latent-knowledge probe (`phase3_latent_knowledge_probe.py`) found that the
residual stream linearly encodes known/unknown at AUROC ~0.997 (peak L35) and
that the 168 over-refusals look internally KNOWN. Before that becomes a claim it
must survive two controls, both GPU-free over activations + behavior already on
disk:

- **A1 lexical baseline.** A bag-of-words / TF-IDF logistic on the QUESTION TEXT,
  scored on the same known/unknown labels. The residual AUROC only carries
  *internal state* to the extent it BEATS what a classifier sees in the surface
  question vocabulary. known/unknown here is dataset-defined (e.g. TriviaQA vs
  SelfAware), so topic/lexicon could trivially separate the classes; if the
  lexical baseline already hits ~0.99, the residual "code" is largely
  re-encoding question vocabulary, not memory-retrieval state. Verdict =
  residual_auroc - lexical_auroc (the internal-state margin).

- **A2 within-known refused-vs-answered probe.** Restrict to KNOWN rows only and
  predict refused (known_refused) vs answered (known_correct_answered +
  known_answered_wrong) from the residual. This is the over-refusal gap as a
  direct supervised axis, built on a contrast ORTHOGONAL to the known/unknown
  labels theta was trained on: a positive held-out AUROC means over-refusal has
  its own internal signature among items the model knows. Paired with a lexical
  baseline on the same split (does question vocabulary alone predict which knowns
  get refused?).

Tier 2 exploratory; held-out AUROC (StratifiedKFold); no steering claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

import phase3_latent_knowledge_probe as lkp

KNOWN_ANSWERED = lkp.KNOWN_ANSWERED
KNOWN_REFUSED = lkp.KNOWN_REFUSED


class ControlError(RuntimeError):
    pass


def load_rows(behavior_rows: Path) -> list[dict[str, Any]]:
    """Behavior rows carrying probe_pool_row_key + label + behavior_cell + question."""
    rows: list[dict[str, Any]] = []
    for line in behavior_rows.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rk = r.get("probe_pool_row_key")
        if rk is None:
            continue
        rows.append({
            "row_key": rk,
            "label": r.get("label"),
            "behavior_cell": r.get("behavior_cell"),
            "question": r.get("question") or "",
        })
    if not rows:
        raise ControlError(f"no rows in {behavior_rows}")
    return rows


def lexical_cv_auroc(texts: list[str], y: np.ndarray, *, folds: int = 5,
                     C: float = 1.0, seed: int = 0) -> float:
    """Held-out ROC-AUC of a TF-IDF + L2-logistic classifier on raw text."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold

    y = np.asarray(y).astype(int)
    if len(np.unique(y)) < 2:
        raise ControlError("need both classes present to compute AUROC")
    texts = list(texts)
    n_min = int(min(np.bincount(y)))
    k = max(2, min(folds, n_min))
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    scores = np.zeros(len(y), dtype=float)
    for tr, te in skf.split(texts, y):
        vec = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2)
        Xtr = vec.fit_transform([texts[i] for i in tr])
        Xte = vec.transform([texts[i] for i in te])
        clf = LogisticRegression(C=C, max_iter=2000)
        clf.fit(Xtr, y[tr])
        scores[te] = clf.decision_function(Xte)
    return float(roc_auc_score(y, scores))


def _verdict_margin(residual: float, lexical: float, *, tol: float = 0.03) -> tuple[str, str]:
    margin = residual - lexical
    if margin > tol:
        v = "INTERNAL-STATE"
        msg = (f"residual probe BEATS the lexical baseline by {margin:+.3f} "
               f"({residual:.3f} vs {lexical:.3f}); the boundary code carries internal "
               f"state beyond surface question vocabulary.")
    elif margin < -tol:
        v = "LEXICAL-DOMINATES"
        msg = (f"lexical baseline BEATS the residual probe by {-margin:+.3f} "
               f"({lexical:.3f} vs {residual:.3f}); question vocabulary alone is the better "
               f"separator — the residual claim is not supported on this split.")
    else:
        v = "LEXICAL-CONFOUND"
        msg = (f"residual ({residual:.3f}) ~ lexical ({lexical:.3f}) within {tol:.2f}; "
               f"the boundary may be largely surface question vocabulary, not internal state.")
    return v, msg


def _select(mats_all: dict[int, np.ndarray], keys_all: list[str],
            wanted: list[str]) -> dict[int, np.ndarray]:
    """Sub-matrix of a preloaded {layer: [n_all, hidden]} for an ordered key subset."""
    idx = {k: i for i, k in enumerate(keys_all)}
    rows = [idx[k] for k in wanted]
    return {L: M[rows] for L, M in mats_all.items()}


def a1_lexical_baseline(extraction_dir: Path, rows: list[dict[str, Any]], *,
                        layers: list[int], source: str = "h_lora",
                        preloaded: tuple[list[str], dict[int, np.ndarray]] | None = None) -> dict[str, Any]:
    """A1: residual known/unknown AUROC vs a TF-IDF lexical baseline on question text."""
    keys = [r["row_key"] for r in rows]
    y = np.array([1 if r["label"] == "unknown" else 0 for r in rows])
    texts = [r["question"] for r in rows]

    if preloaded is not None:
        keys_all, mats_all = preloaded
        mats = _select(mats_all, keys_all, keys)
    else:
        mats = lkp.load_layers(extraction_dir, keys, layers, source=source)
    residual_by_layer = [{"layer": L, "auroc": round(lkp.cv_auroc(mats[L], y), 4)} for L in layers]
    best = max(residual_by_layer, key=lambda d: d["auroc"])
    lexical = round(lexical_cv_auroc(texts, y), 4)
    verdict, msg = _verdict_margin(best["auroc"], lexical)
    return {
        "control": "a1_lexical_baseline",
        "source": source,
        "n_rows": len(rows),
        "label_counts": {"known": int((y == 0).sum()), "unknown": int((y == 1).sum())},
        "residual_auroc_by_layer": residual_by_layer,
        "residual_best": best,
        "lexical_auroc": lexical,
        "internal_state_margin": round(best["auroc"] - lexical, 4),
        "verdict": verdict,
        "verdict_msg": msg,
    }


def a2_within_known(extraction_dir: Path, rows: list[dict[str, Any]], *,
                    layers: list[int], source: str = "h_lora",
                    preloaded: tuple[list[str], dict[int, np.ndarray]] | None = None) -> dict[str, Any]:
    """A2: among KNOWN rows, residual refused-vs-answered AUROC vs lexical baseline."""
    known = [r for r in rows if r["label"] == "known"]
    refused = [r for r in known if r["behavior_cell"] == KNOWN_REFUSED]
    answered = [r for r in known if r["behavior_cell"] != KNOWN_REFUSED]
    if not refused or not answered:
        raise ControlError(
            f"within-known split degenerate: refused={len(refused)} answered={len(answered)}")
    sub = refused + answered
    keys = [r["row_key"] for r in sub]
    y = np.array([1] * len(refused) + [0] * len(answered))  # 1 == over-refused
    texts = [r["question"] for r in sub]

    if preloaded is not None:
        keys_all, mats_all = preloaded
        mats = _select(mats_all, keys_all, keys)
    else:
        mats = lkp.load_layers(extraction_dir, keys, layers, source=source)
    residual_by_layer = [{"layer": L, "auroc": round(lkp.cv_auroc(mats[L], y), 4)} for L in layers]
    best = max(residual_by_layer, key=lambda d: d["auroc"])
    lexical = round(lexical_cv_auroc(texts, y), 4)
    verdict, msg = _verdict_margin(best["auroc"], lexical)
    return {
        "control": "a2_within_known_refused_vs_answered",
        "source": source,
        "n_known_refused": len(refused),
        "n_known_answered": len(answered),
        "residual_auroc_by_layer": residual_by_layer,
        "residual_best": best,
        "lexical_auroc": lexical,
        "internal_state_margin": round(best["auroc"] - lexical, 4),
        "verdict": verdict,
        "verdict_msg": msg,
    }


def _fit_direction(X: np.ndarray, y: np.ndarray, *, C: float = 0.5) -> np.ndarray:
    """Unit normal of an L2-logistic hyperplane on standardized X (whitened coords)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    sc = StandardScaler().fit(X)
    clf = LogisticRegression(C=C, max_iter=2000)
    clf.fit(sc.transform(X), np.asarray(y).astype(int))
    w = clf.coef_[0]
    n = np.linalg.norm(w)
    return w / n if n > 0 else w


def axis_geometry(rows: list[dict[str, Any]], *, layer: int,
                  preloaded: tuple[list[str], dict[int, np.ndarray]]) -> dict[str, Any]:
    """Is the within-known over-refusal axis the SAME direction as the known/unknown axis?

    Fits both probe normals at one layer in a shared whitened (StandardScaler-on-all-rows)
    coordinate frame and reports |cos|. Near 0 => the over-refusal 'caution' axis is
    distinct from the knowledge axis (a separate internal signal, consistent with
    over-refusals reading as KNOWN on the knowledge axis); near 1 => A2 is just re-reading
    the knowledge boundary.
    """
    from sklearn.preprocessing import StandardScaler

    keys_all, mats_all = preloaded
    idx = {k: i for i, k in enumerate(keys_all)}
    order = [r for r in rows if r["row_key"] in idx]
    X = mats_all[layer][[idx[r["row_key"]] for r in order]]
    sc = StandardScaler().fit(X)  # shared frame for both directions
    Xw = sc.transform(X)

    y_ku = np.array([1 if r["label"] == "unknown" else 0 for r in order])
    known_mask = np.array([r["label"] == "known" for r in order])
    y_or = np.array([1 if r["behavior_cell"] == KNOWN_REFUSED else 0 for r in order])

    from sklearn.linear_model import LogisticRegression

    def _dir(Xsub, ysub):
        w = LogisticRegression(C=0.5, max_iter=2000).fit(Xsub, ysub).coef_[0]
        n = np.linalg.norm(w)
        return w / n if n > 0 else w

    d_ku = _dir(Xw, y_ku)
    d_or = _dir(Xw[known_mask], y_or[known_mask])
    cos = float(abs(np.dot(d_ku, d_or)))
    if cos < 0.2:
        verdict = "ORTHOGONAL"
        msg = (f"|cos|={cos:.3f}: the over-refusal 'caution' axis is DISTINCT from the "
               f"known/unknown axis — a separate internal signal, not a re-read of knowledge.")
    elif cos > 0.6:
        verdict = "ALIGNED"
        msg = (f"|cos|={cos:.3f}: the over-refusal axis largely RE-READS the known/unknown "
               f"boundary; not an independent caution signal.")
    else:
        verdict = "PARTIAL"
        msg = (f"|cos|={cos:.3f}: the over-refusal axis partially overlaps the knowledge axis.")
    return {"control": "axis_geometry", "layer": layer, "abs_cosine": round(cos, 4),
            "verdict": verdict, "verdict_msg": msg}


def run(extraction_dir: Path, behavior_rows: Path, *, layers: list[int],
        source: str = "h_lora") -> dict[str, Any]:
    rows = load_rows(behavior_rows)
    # single file-read pass over all rows/layers (9P mount is the cost), reused by all readouts
    keys_all = [r["row_key"] for r in rows]
    mats_all = lkp.load_layers(extraction_dir, keys_all, layers, source=source)
    preloaded = (keys_all, mats_all)
    a1 = a1_lexical_baseline(extraction_dir, rows, layers=layers, source=source, preloaded=preloaded)
    a2 = a2_within_known(extraction_dir, rows, layers=layers, source=source, preloaded=preloaded)
    geom = axis_geometry(rows, layer=a1["residual_best"]["layer"], preloaded=preloaded)
    return {
        "ok": True,
        "analysis_type": "phase3_latent_knowledge_controls",
        "source": source,
        "extraction_dir": str(extraction_dir),
        "a1_lexical_baseline": a1,
        "a2_within_known": a2,
        "axis_geometry": geom,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extraction-dir", required=True, type=Path)
    p.add_argument("--behavior-rows", required=True, type=Path)
    p.add_argument("--layers", default="all", help="comma-separated layer ints, or 'all' for 0..36")
    p.add_argument("--source", default="h_lora", choices=["h_lora", "h_base", "delta"])
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def _print_control(c: dict[str, Any]) -> None:
    print(f"\n[{c['control']}] source={c['source']}", file=sys.stderr)
    b = c["residual_best"]
    print(f"  residual best L{b['layer']} AUROC={b['auroc']:.4f}  "
          f"lexical AUROC={c['lexical_auroc']:.4f}  margin={c['internal_state_margin']:+.4f}",
          file=sys.stderr)
    print(f"  VERDICT [{c['verdict']}]: {c['verdict_msg']}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    layers = list(range(37)) if args.layers == "all" else [int(x) for x in args.layers.split(",")]
    result = run(args.extraction_dir, args.behavior_rows, layers=layers, source=args.source)
    _print_control(result["a1_lexical_baseline"])
    _print_control(result["a2_within_known"])
    g = result["axis_geometry"]
    print(f"\n[axis_geometry] L{g['layer']}  |cos(knowledge, over-refusal)|={g['abs_cosine']:.4f}",
          file=sys.stderr)
    print(f"  VERDICT [{g['verdict']}]: {g['verdict_msg']}", file=sys.stderr)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
