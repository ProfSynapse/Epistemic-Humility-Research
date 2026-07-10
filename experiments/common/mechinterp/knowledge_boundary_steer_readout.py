#!/usr/bin/env python3
"""Belief-vs-action readout for the knowledge-boundary (K) steering sweep (GPU-free).

The K sweep (mechinterp_head_intervention_runner with the knowledge_boundary artifact)
saves per-row ``generated_answer``, ``label``, ``refused`` across symmetric alpha.
K's positive pole is "unknown", negative pole is "known". This re-reads the sweep
``rows.jsonl`` and asks whether K behaves like a knowledge-BELIEF monitor or merely
like the refusal/action lever F:

Per (alpha, label) it computes refusal rate and mean parsed ``response_confidence``.
Then it classifies the causal signature:

- ``belief_monitor`` : steering toward "known" (alpha<0) LOWERS unknown_refusal_rate
  AND raises stated confidence; steering toward "unknown" (alpha>0) RAISES
  over_refusal_on_known AND lowers confidence. The known and unknown sides move
  in OPPOSITE behavioral senses relative to the boundary, and the graded
  confidence tracks alpha. This is the separable "do I know this?" signal F was not.
- ``refusal_like`` : refusal moves in the SAME direction on both labels (a uniform
  action shift, like F) and/or confidence is flat. K is another refusal-correlated
  direction, not a distinct belief monitor.
- ``inert`` : neither refusal nor confidence moves beyond tolerance with alpha.

Screening (Tier 2). The verdict is a directional read of the curve, not a claim
about every input.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from pathlib import Path
from typing import Any

_CONF_RE = re.compile(r'"response_confidence"\s*:\s*([0-9]*\.?[0-9]+)')


class KSteerReadoutError(RuntimeError):
    pass


def parse_confidence(generated_answer: str) -> float | None:
    """Best-effort parse of response_confidence from the JSON answer text."""
    if not generated_answer:
        return None
    try:
        obj = json.loads(generated_answer)
        if isinstance(obj, dict) and "response_confidence" in obj:
            return float(obj["response_confidence"])
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    m = _CONF_RE.search(generated_answer)
    if m is not None:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def cells_by_alpha_label(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[float, str], dict[str, list]] = {}
    for r in rows:
        alpha = float(r["alpha"])
        label = r.get("label")
        if label not in ("known", "unknown"):
            continue
        b = buckets.setdefault((alpha, label), {"refused": [], "conf": []})
        b["refused"].append(bool(r.get("refused")))
        c = parse_confidence(r.get("generated_answer", ""))
        if c is not None:
            b["conf"].append(c)
    out = []
    for (alpha, label), b in sorted(buckets.items()):
        n = len(b["refused"])
        out.append({
            "alpha": alpha,
            "label": label,
            "n": n,
            "refusal_rate": round(100.0 * sum(b["refused"]) / n, 2) if n else None,
            "mean_confidence": round(st.mean(b["conf"]), 4) if b["conf"] else None,
            "n_confidence": len(b["conf"]),
        })
    return out


def _series(cells, label, field):
    pts = [(c["alpha"], c[field]) for c in cells if c["label"] == label and c[field] is not None]
    pts.sort()
    return pts


def _slope_sign(pts) -> int:
    """+1 if value rises with alpha, -1 if falls, 0 if flat/insufficient."""
    if len(pts) < 2:
        return 0
    lo, hi = pts[0][1], pts[-1][1]
    if hi - lo > 1e-9:
        return 1
    if hi - lo < -1e-9:
        return -1
    return 0


def classify(cells: list[dict[str, Any]], *, refusal_tol: float = 5.0, conf_tol: float = 0.03) -> dict[str, Any]:
    """Belief-consistency test under sign convention +alpha = "unknown" pole.

    A genuine knowledge dial predicts that steering toward "unknown" (alpha>0)
    makes the model BEHAVE as if it knows less: refusal rises (esp. on knowns,
    which have headroom) AND stated confidence falls. Both F and a belief monitor
    can move refusal in the same direction on both labels, so uniformity is NOT
    the discriminator — the SIGN of the effect relative to K's pole is. An effect
    that is belief-INCONSISTENT (refusal falls toward "unknown", or confidence
    rises toward "unknown") is F-like / anti-steerable, not a working monitor.
    """
    unk_ref = _series(cells, "unknown", "refusal_rate")
    kn_ref = _series(cells, "known", "refusal_rate")
    unk_conf = _series(cells, "unknown", "mean_confidence")
    kn_conf = _series(cells, "known", "mean_confidence")

    def span(pts):
        return (pts[-1][1] - pts[0][1]) if len(pts) >= 2 else 0.0

    d_unk_ref, d_kn_ref = span(unk_ref), span(kn_ref)
    d_unk_conf, d_kn_conf = span(unk_conf), span(kn_conf)
    # Confidence span: prefer whichever label has the larger magnitude move.
    d_conf = d_kn_conf if abs(d_kn_conf) >= abs(d_unk_conf) else d_unk_conf

    detail = {
        "unknown_refusal_span": round(d_unk_ref, 2),
        "known_refusal_span": round(d_kn_ref, 2),
        "unknown_confidence_span": round(d_unk_conf, 4),
        "known_confidence_span": round(d_kn_conf, 4),
        "refusal_endpoints": {"unknown": unk_ref, "known": kn_ref},
    }

    # Known-side refusal has the most headroom (low baseline), so it is the
    # primary belief signal; confidence is the graded corroborator.
    refusal_moves = abs(d_unk_ref) > refusal_tol or abs(d_kn_ref) > refusal_tol
    conf_moves = abs(d_conf) > conf_tol
    if not refusal_moves and not conf_moves:
        return {"classification": "inert",
                "verdict": (f"INERT: steering K moves neither refusal (Δunk {d_unk_ref:+.1f}, "
                            f"Δknown {d_kn_ref:+.1f} pts) nor confidence (Δ {d_conf:+.3f}) beyond "
                            f"tolerance. K is causally weak here; a separable knowledge representation, "
                            f"if present, is not this steerable axis."),
                "detail": detail}

    # belief-consistent: refusal up toward "unknown" (known side) and/or confidence down.
    refusal_consistent = d_kn_ref > refusal_tol or d_unk_ref > refusal_tol
    refusal_inconsistent = d_kn_ref < -refusal_tol or d_unk_ref < -refusal_tol
    conf_consistent = d_conf < -conf_tol
    conf_inconsistent = d_conf > conf_tol

    consistent = (refusal_consistent or conf_consistent) and not (refusal_inconsistent or conf_inconsistent)
    inconsistent = (refusal_inconsistent or conf_inconsistent) and not (refusal_consistent or conf_consistent)

    if consistent:
        return {"classification": "belief_monitor",
                "verdict": (f"BELIEF-MONITOR-like: steering toward the 'unknown' pole is belief-CONSISTENT "
                            f"— known-side refusal Δ {d_kn_ref:+.1f} pts (headroom side), unknown-side Δ "
                            f"{d_unk_ref:+.1f}, confidence Δ {d_conf:+.3f}. K causally moves the model's "
                            f"knowledge belief in the direction of its read — the separable 'do I know "
                            f"this?' dial F (the anti-steerable refusal axis) was not."),
                "detail": detail}
    if inconsistent:
        return {"classification": "anti_steer",
                "verdict": (f"ANTI-STEER / INCONSISTENT: steering toward 'unknown' moves behavior the "
                            f"WRONG way (known refusal Δ {d_kn_ref:+.1f}, confidence Δ {d_conf:+.3f}). "
                            f"Like F, K's steering sign is inverted vs its read; it is not a working "
                            f"knowledge dial (cf. Tan 2407.12404 anti-steerability)."),
                "detail": detail}
    return {"classification": "mixed",
            "verdict": (f"MIXED: refusal Δknown {d_kn_ref:+.1f}/Δunk {d_unk_ref:+.1f}, confidence "
                        f"Δ {d_conf:+.3f} point in conflicting directions; inspect cells."),
            "detail": detail}


def run_from_rows(rows: list[dict[str, Any]], *, source: str | None = None) -> dict[str, Any]:
    if not rows:
        raise KSteerReadoutError("no rows")
    cells = cells_by_alpha_label(rows)
    verdict = classify(cells)
    return {
        "ok": True,
        "analysis_type": "mechinterp_knowledge_boundary_steer_readout",
        "rows": source,
        "n_rows": len(rows),
        "cells": cells,
        **verdict,
    }


def run(rows_path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise KSteerReadoutError(f"no rows in {rows_path}")
    return run_from_rows(rows, source=str(rows_path))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", required=True, type=Path, help="K-steering sweep rows.jsonl")
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run(args.rows)
    for c in result["cells"]:
        print(f"  alpha {c['alpha']:>5g}  {c['label']:>7}  n={c['n']:>3}  "
              f"refusal={c['refusal_rate']:>6}  conf={c['mean_confidence']}", file=sys.stderr)
    print(f"\nVERDICT [{result['classification']}]: {result['verdict']}", file=sys.stderr)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
