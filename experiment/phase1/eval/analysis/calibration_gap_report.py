#!/usr/bin/env python3
"""Calibration-gap report: emitted response-confidence vs internal doubt axis.

GPU-free. Two analyses, both the Amendment J / GRPO-v3 (section 5) metric set, so
the same script re-runs on a B0 ``scored_rows.jsonl`` for an apples-to-apples
table against the v2 baseline.

Analysis A -- EMITTED-confidence calibration (pure scored_rows):
  Treat the emitted ``stated_confidence`` (= schema ``response_confidence``) as a
  forecast of *response appropriateness*. A row is appropriate iff it answered a
  known question correctly OR abstained on a true unknown:

      appropriate = (not refused and correct) or (refused and label == "unknown")

  Reports: emitted std / unique-count / range, ECE and Brier vs appropriateness,
  correct-vs-wrong AUROC among answered known rows, and per-cell mean emitted
  confidence. A collapsed scalar fails ECE/AUROC even at full JSON coverage.

Analysis B -- INTERNAL doubt axis vs EMITTED scalar (needs --extraction + --overlay):
  Build the L35 knowledge/doubt axis the same way as the caution_perp builder:

      doubt_u = unit(mean(known_correct_answered) - mean(unknown_refused))

  Score every behavior row's L35 activation onto doubt_u, then compare the
  INTERNAL axis against the EMITTED scalar on the SAME rows for the well-powered
  targets (known/unknown boundary; response appropriateness), plus their
  rank correlation. The headline "model knows but doesn't say" = internal AUROC
  high, emitted AUROC ~0.5, correlation ~0. doubt_u is a known/unknown contrast
  (both source cells are *appropriate*), so it is not trained to separate
  appropriate from inappropriate -- the appropriateness AUROC is a fair read, not
  a circular one. Correct-vs-wrong is intentionally de-emphasised (only ~15 known
  wrong rows; underpowered, see phase3_latent_knowledge_probe.py).

Tier 2 exploratory. AUROC is threshold-free (Mann-Whitney); no steering claim.

Usage:
  python experiment/phase1/eval/analysis/calibration_gap_report.py \
    --scored <scored_rows.jsonl> \
    [--overlay <behavior rows.jsonl> --extraction <hidden_states extraction dir>] \
    [--layer 35] [--out <report.json>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parents[2] / "probe"
sys.path.insert(0, str(PROBE_DIR))

APPROPRIATE_CELLS = {"known_correct_answered", "unknown_refused"}


# ----------------------------------------------------------------------------- metrics
def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUROC (P[score(pos) > score(neg)]); ties at 0.5. nan if degenerate."""
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1)
    # average ranks for ties
    s_sorted = scores[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    r_pos = ranks[labels == 1].sum()
    n_pos, n_neg = len(pos), len(neg)
    return float((r_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def ece(conf: np.ndarray, correct: np.ndarray, n_bins: int = 10) -> float:
    """Expected calibration error, equal-width bins on [0,1]."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    n = len(conf)
    total = 0.0
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        mask = (conf >= lo) & (conf < hi) if b < n_bins - 1 else (conf >= lo) & (conf <= hi)
        if not mask.any():
            continue
        total += mask.sum() / n * abs(conf[mask].mean() - correct[mask].mean())
    return float(total)


def brier(conf: np.ndarray, correct: np.ndarray) -> float:
    return float(np.mean((conf - correct) ** 2))


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    def rank(x):
        order = np.argsort(x, kind="mergesort")
        r = np.empty(len(x))
        r[order] = np.arange(len(x))
        return r
    ra, rb = rank(a), rank(b)
    ra -= ra.mean(); rb -= rb.mean()
    d = float(np.sqrt((ra ** 2).sum() * (rb ** 2).sum()))
    return float((ra * rb).sum() / d) if d else float("nan")


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean(); b = b - b.mean()
    d = float(np.sqrt((a ** 2).sum() * (b ** 2).sum()))
    return float((a * b).sum() / d) if d else float("nan")


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


# ----------------------------------------------------------------------------- loaders
def load_scored(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open() if l.strip()]


def appropriate_from_scored(r: dict) -> int:
    refused = bool(r.get("refused"))
    correct = bool(r.get("correct"))
    label = str(r.get("label", "")).lower()
    return int((not refused and correct) or (refused and label == "unknown"))


# ----------------------------------------------------------------------------- analysis A
def analysis_a(rows: list[dict], cell_of: dict | None = None) -> dict:
    conf = np.array([float(r["stated_confidence"]) for r in rows], dtype=np.float64)
    appr = np.array([appropriate_from_scored(r) for r in rows], dtype=np.float64)
    out = {
        "n": len(rows),
        "emitted_mean": float(conf.mean()),
        "emitted_std": float(conf.std()),
        "emitted_min": float(conf.min()),
        "emitted_max": float(conf.max()),
        "emitted_unique": int(np.unique(np.round(conf, 4)).size),
        "appropriateness_rate": float(appr.mean()),
        "ece_vs_appropriateness": ece(conf, appr),
        "brier_vs_appropriateness": brier(conf, appr),
        "auroc_emitted_to_appropriateness": auroc(conf, appr),
    }
    # correct-vs-wrong AUROC among ANSWERED known rows
    ans_known = [r for r in rows
                 if str(r.get("label", "")).lower() == "known" and not r.get("refused")]
    if ans_known:
        c = np.array([float(r["stated_confidence"]) for r in ans_known])
        y = np.array([int(bool(r.get("correct"))) for r in ans_known])
        out["answered_known_n"] = len(ans_known)
        out["answered_known_n_wrong"] = int((y == 0).sum())
        out["auroc_emitted_correct_vs_wrong_answered_known"] = auroc(c, y)
    # per-cell emitted mean (cells from overlay if provided, else derived)
    cells: dict[str, list[float]] = {}
    for r in rows:
        if cell_of is not None:
            cell = cell_of.get(_scored_id(r))
            if cell is None:
                continue
        else:
            cell = _derive_cell(r)
        cells.setdefault(cell, []).append(float(r["stated_confidence"]))
    out["per_cell_emitted_mean"] = {
        k: {"n": len(v), "mean": float(np.mean(v)), "std": float(np.std(v))}
        for k, v in sorted(cells.items())
    }
    return out


def _scored_id(r: dict) -> str:
    return str(r.get("id"))


def _derive_cell(r: dict) -> str:
    label = str(r.get("label", "")).lower()
    refused = bool(r.get("refused"))
    correct = bool(r.get("correct"))
    if refused:
        return f"{label}_refused"
    return f"{label}_{'correct_answered' if correct else 'answered_wrong'}"


# ----------------------------------------------------------------------------- analysis B
def analysis_b(scored: list[dict], overlay_path: Path, extraction: Path, layer: int) -> dict:
    from phase3_latent_knowledge_probe import load_layers

    overlay = [json.loads(l) for l in overlay_path.open() if l.strip()]
    sc_by_id = {_scored_id(r): r for r in scored}

    keys, cells, emitted, appr, known = [], [], [], [], []
    for o in overlay:
        rk = o["probe_pool_row_key"]
        sid = rk.split("::")[-1]
        s = sc_by_id.get(sid)
        if s is None:
            continue
        keys.append(rk)
        cells.append(o["behavior_cell"])
        emitted.append(float(s["stated_confidence"]))
        appr.append(int(o["behavior_cell"] in APPROPRIATE_CELLS))
        known.append(int(str(o.get("label", "")).lower() == "known"))

    print(f"analysis B: joined {len(keys)} behavior rows; loading L{layer} activations...",
          file=sys.stderr)
    X = load_layers(extraction, keys, [layer])[layer]
    cells_arr = np.array(cells)
    Xka = X[cells_arr == "known_correct_answered"]
    Xur = X[cells_arr == "unknown_refused"]
    doubt_u = unit(Xka.mean(0) - Xur.mean(0))      # known(+) - unknown(-)
    proj = X @ doubt_u                              # internal doubt score per row

    emitted = np.asarray(emitted); appr = np.asarray(appr); known = np.asarray(known)
    out = {
        "n_joined": len(keys),
        "layer": layer,
        # known/unknown boundary: internal axis vs emitted scalar
        "auroc_internal_to_known": auroc(proj, known),
        "auroc_emitted_to_known": auroc(emitted, known),
        # appropriateness: internal axis vs emitted scalar
        "auroc_internal_to_appropriateness": auroc(proj, appr),
        "auroc_emitted_to_appropriateness": auroc(emitted, appr),
        # do the two confidence currencies agree?
        "pearson_internal_emitted": pearson(proj, emitted),
        "spearman_internal_emitted": spearman(proj, emitted),
        # over-refusal read: where do known_refused sit on the internal axis?
        "internal_mean_by_cell": {
            c: {"n": int((cells_arr == c).sum()),
                "internal_mean": float(proj[cells_arr == c].mean()),
                "emitted_mean": float(emitted[cells_arr == c].mean())}
            for c in sorted(set(cells))
        },
    }
    return out


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scored", type=Path, required=True)
    ap.add_argument("--overlay", type=Path, default=None)
    ap.add_argument("--extraction", type=Path, default=None)
    ap.add_argument("--layer", type=int, default=35)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    scored = load_scored(args.scored)
    report: dict = {"scored_rows": str(args.scored), "n_scored": len(scored)}

    # build cell_of from overlay if present (for per-cell emitted means on the subset)
    cell_of = None
    overlay_ids = None
    if args.overlay and args.overlay.is_file():
        overlay = [json.loads(l) for l in args.overlay.open() if l.strip()]
        cell_of = {o["probe_pool_row_key"].split("::")[-1]: o["behavior_cell"] for o in overlay}
        overlay_ids = set(cell_of)

    report["A_full_eval"] = analysis_a(scored)
    if overlay_ids is not None:
        subset = [r for r in scored if _scored_id(r) in overlay_ids]
        report["A_behavior_subset"] = analysis_a(subset, cell_of=cell_of)

    if args.overlay and args.extraction:
        report["B_internal_vs_emitted"] = analysis_b(
            scored, args.overlay, args.extraction, args.layer)

    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
