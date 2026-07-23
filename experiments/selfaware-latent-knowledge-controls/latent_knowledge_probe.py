#!/usr/bin/env python3
"""Internal-vs-expressed knowledge-boundary probe (GPU-free).

After the failure axis F and the knowledge-boundary axis K both turned out to be
anti-steerable refusal-correlated directions (not a separable causal uncertainty
dial), this shifts the search from a STEERABLE knob to a READ signal: does the
model's residual stream LINEARLY encode "do I know this?" — and does it encode it
MORE than the model's abstention behavior expresses?

Two readouts, both on the per-layer residual stream (h_lora, the active-adapter
activations at the final prompt token) joined to the GRPO v2 behavior_cell:

1. knowledge_boundary_auroc_by_layer: per layer, a cross-validated L2 logistic
   probe of activation -> ground-truth known/unknown. Locates WHERE the model
   linearly represents the knowledge boundary and how strong it is. This is the
   read-side existence test for an "uncertainty activation".

2. over_refusal_gap: the latent-vs-expressed test. Train the best-layer probe on
   CLEAN cells (known_correct_answered = knew+answered, unknown_refused =
   didn't-know+refused), then score the held-out OVER-REFUSALS (known_refused =
   the model knew but refused anyway). If the probe scores them like
   known_correct_answered (low p_unknown), the model internally represented the
   knowledge and the over-refusal is a behavioral-threshold problem, NOT an
   internal "I don't know" signal. If it scores them like unknown_refused, the
   over-refusal reflects a genuine internal uncertainty the behavior got right.

Note on power: "predict correctness among ANSWERED items" is intentionally NOT
the target here — this GRPO model answers-wrong too rarely (~15 known +
1 unknown) to train a 2560-dim correctness probe. The known/unknown boundary and
the 168-item over-refusal cell are the well-powered signals.

Tier 2 exploratory. AUROC is held-out (StratifiedKFold); no steering claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

# cells (GRPO v2 behavior_cell) used by the readouts
KNOWN_ANSWERED = "known_correct_answered"
KNOWN_REFUSED = "known_refused"
UNKNOWN_REFUSED = "unknown_refused"


class LatentProbeError(RuntimeError):
    pass


def row_key_to_tensor_file(extraction_dir: Path, row_key: str, *, source: str = "h_lora") -> Path:
    """probe_pool_row_key 'a::b::000000::c' -> 'a__b__000000__c__h_lora.safetensors'."""
    stem = row_key.replace("::", "__")
    return extraction_dir / f"{stem}__{source}.safetensors"


def load_layers(extraction_dir: Path, row_keys: list[str], layers: list[int], *,
                source: str = "h_lora") -> dict[int, np.ndarray]:
    """Open each row's safetensors ONCE, pull all requested layers -> {layer: [n, hidden]}.

    The per-row files live on a slow 9P mount, so we read each file a single time
    rather than once per layer.
    """
    from safetensors import safe_open  # local import: keep module importable without it

    keys = [f"L{L}" for L in layers]
    cols: dict[int, list] = {L: [] for L in layers}
    for rk in row_keys:
        path = row_key_to_tensor_file(extraction_dir, rk, source=source)
        if not path.is_file():
            raise LatentProbeError(f"missing activation file for {rk}: {path}")
        with safe_open(str(path), "pt") as h:
            for L, key in zip(layers, keys):
                cols[L].append(h.get_tensor(key).float().numpy())
    return {L: np.asarray(cols[L], dtype=np.float64) for L in layers}


def load_layer_matrix(extraction_dir: Path, row_keys: list[str], layer: int, *,
                      source: str = "h_lora") -> np.ndarray:
    """Single-layer convenience wrapper over load_layers."""
    return load_layers(extraction_dir, row_keys, [layer], source=source)[layer]


def cv_auroc(X: np.ndarray, y: np.ndarray, *, folds: int = 5, C: float = 0.5, seed: int = 0) -> float:
    """Held-out ROC-AUC of an L2 logistic probe over StratifiedKFold."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    y = np.asarray(y).astype(int)
    if len(np.unique(y)) < 2:
        raise LatentProbeError("need both classes present to compute AUROC")
    n_min = int(min(np.bincount(y)))
    k = max(2, min(folds, n_min))
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    scores = np.zeros(len(y), dtype=float)
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=C, max_iter=2000)
        clf.fit(sc.transform(X[tr]), y[tr])
        scores[te] = clf.decision_function(sc.transform(X[te]))
    return float(roc_auc_score(y, scores))


def fit_score_probe(X_train: np.ndarray, y_train: np.ndarray, X_eval: np.ndarray, *,
                    C: float = 0.5) -> np.ndarray:
    """Train on (X_train,y_train), return P(class=1) for X_eval. class 1 == unknown."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    sc = StandardScaler().fit(X_train)
    clf = LogisticRegression(C=C, max_iter=2000)
    clf.fit(sc.transform(X_train), np.asarray(y_train).astype(int))
    return clf.predict_proba(sc.transform(X_eval))[:, 1]


def load_behavior(behavior_rows: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in behavior_rows.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rk = r.get("probe_pool_row_key")
        if rk is None:
            continue
        out[rk] = {"label": r.get("label"), "behavior_cell": r.get("behavior_cell")}
    if not out:
        raise LatentProbeError(f"no rows in {behavior_rows}")
    return out


def analyze(extraction_dir: Path, behavior: dict[str, dict[str, Any]], *,
            layers: list[int], source: str = "h_lora") -> dict[str, Any]:
    keys = sorted(behavior)
    labels = np.array([1 if behavior[k]["label"] == "unknown" else 0 for k in keys])
    cells = [behavior[k]["behavior_cell"] for k in keys]

    mats = load_layers(extraction_dir, keys, layers, source=source)

    # Readout 1: per-layer knowledge-boundary AUROC (ground-truth known/unknown).
    by_layer = []
    for L in layers:
        auroc = cv_auroc(mats[L], labels)
        by_layer.append({"layer": L, "auroc": round(auroc, 4)})
    best = max(by_layer, key=lambda d: d["auroc"])

    # Readout 2: over-refusal gap at the best layer.
    Xb = mats[best["layer"]]
    idx = {k: i for i, k in enumerate(keys)}
    cell_idx = {c: [idx[k] for k in keys if behavior[k]["behavior_cell"] == c]
                for c in (KNOWN_ANSWERED, KNOWN_REFUSED, UNKNOWN_REFUSED)}
    gap: dict[str, Any] = {"layer": best["layer"], "n": {c: len(v) for c, v in cell_idx.items()}}
    if cell_idx[KNOWN_ANSWERED] and cell_idx[UNKNOWN_REFUSED] and cell_idx[KNOWN_REFUSED]:
        tr = cell_idx[KNOWN_ANSWERED] + cell_idx[UNKNOWN_REFUSED]
        ytr = np.array([0] * len(cell_idx[KNOWN_ANSWERED]) + [1] * len(cell_idx[UNKNOWN_REFUSED]))
        p_known_ref = fit_score_probe(Xb[tr], ytr, Xb[cell_idx[KNOWN_REFUSED]])
        # in-sample anchors for reference (mean p_unknown of each training cell)
        p_known_ans = fit_score_probe(Xb[tr], ytr, Xb[cell_idx[KNOWN_ANSWERED]])
        p_unk_ref = fit_score_probe(Xb[tr], ytr, Xb[cell_idx[UNKNOWN_REFUSED]])
        m_kr = float(np.mean(p_known_ref))
        m_ka = float(np.mean(p_known_ans))
        m_ur = float(np.mean(p_unk_ref))
        # position of over-refusals between the known-answered and unknown-refused anchors
        denom = (m_ur - m_ka) if abs(m_ur - m_ka) > 1e-9 else 1e-9
        position = (m_kr - m_ka) / denom  # 0 == looks known-answered, 1 == looks unknown-refused
        gap.update({
            "p_unknown_known_answered": round(m_ka, 4),
            "p_unknown_unknown_refused": round(m_ur, 4),
            "p_unknown_known_refused": round(m_kr, 4),
            "over_refusal_position": round(position, 3),
            "verdict": _gap_verdict(position),
        })
    else:
        gap["verdict"] = "INSUFFICIENT: need known_correct_answered, unknown_refused, known_refused cells."

    return {
        "ok": True,
        "analysis_type": "latent_knowledge_probe",
        "source": source,
        "n_rows": len(keys),
        "label_counts": {"known": int((labels == 0).sum()), "unknown": int((labels == 1).sum())},
        "knowledge_boundary_auroc_by_layer": by_layer,
        "best_layer": best,
        "over_refusal_gap": gap,
    }


def _gap_verdict(position: float) -> str:
    if position < 0.33:
        return (f"LATENT-KNOWLEDGE: over-refusals (known_refused) look INTERNALLY KNOWN "
                f"(position {position:.2f} ~ known_answered). The model represented the answer "
                f"but refused anyway — over-abstention is a behavioral-threshold gap, not an "
                f"internal 'I don't know' signal.")
    if position > 0.66:
        return (f"INTERNAL-UNCERTAINTY: over-refusals look INTERNALLY UNKNOWN (position "
                f"{position:.2f} ~ unknown_refused). The abstention tracks a genuine internal "
                f"uncertainty signal; the refusal was epistemically appropriate.")
    return (f"MIXED: over-refusals sit between the anchors (position {position:.2f}); the "
            f"internal knowledge signal partially explains the over-abstention.")


def run(extraction_dir: Path, behavior_rows: Path, *, layers: list[int], source: str = "h_lora") -> dict[str, Any]:
    behavior = load_behavior(behavior_rows)
    return analyze(extraction_dir, behavior, layers=layers, source=source)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extraction-dir", required=True, type=Path, help="dir of per-row *_h_lora.safetensors")
    p.add_argument("--behavior-rows", required=True, type=Path, help="rows.jsonl with probe_pool_row_key + behavior_cell")
    p.add_argument("--layers", default="all", help="comma-separated layer ints, or 'all' for 0..36")
    p.add_argument("--source", default="h_lora", choices=["h_lora", "h_base", "delta"])
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    layers = list(range(37)) if args.layers == "all" else [int(x) for x in args.layers.split(",")]
    result = run(args.extraction_dir, args.behavior_rows, layers=layers, source=args.source)
    for d in result["knowledge_boundary_auroc_by_layer"]:
        print(f"  L{d['layer']:>2}  known/unknown AUROC={d['auroc']:.4f}", file=sys.stderr)
    b = result["best_layer"]
    print(f"\nBEST LAYER L{b['layer']} AUROC={b['auroc']:.4f}", file=sys.stderr)
    g = result["over_refusal_gap"]
    print(f"OVER-REFUSAL GAP [{g.get('verdict','')}]", file=sys.stderr)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
