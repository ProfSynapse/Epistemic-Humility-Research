#!/usr/bin/env python3
"""Per-head read-sign consistency on the failure axis F (GPU-free).

The Tier-2 read-trajectory runner records, per row, each target head's prompt-token
projection onto F in ``prompt_read_per_head`` (``{"L{layer}H{head}": value}``).
This reads that existing ``rows.jsonl`` and asks a mechanism question the
aggregate trajectory cannot answer: do ALL target heads read F with the same
sign, or is the axis a sum over heads that disagree?

For each head it computes the read separation
``mean(unknown_answered_wrong) - mean(unknown_refused)`` at the prompt token. A
positive separation means that head reads the wrong-answer pole HIGH (the
direction F was built to point). The verdict is:

- ``unanimous`` : every head has the same separation sign. The aggregate read is
  not an artifact of cancelling heads; any steering inversion (A.4) is a
  write-side property on top of a clean, uniform read (cf. Tan 2407.12404
  anti-steerability — read sign != steer sign).
- ``split`` : heads disagree in sign; the aggregate read masks heterogeneity and
  a per-head steering sweep is needed before reading F as one axis.

This is screening evidence (Tier 2). It does NOT establish steering sign — that
needs the per-head intervention sweep.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path
from typing import Any


class ReadSignError(RuntimeError):
    pass


def group_of(row: dict[str, Any]) -> str | None:
    """unknown + refused -> 'refused'; unknown + answered + wrong -> 'answered_wrong'."""
    if row.get("label") != "unknown":
        return None
    if row.get("refused"):
        return "refused"
    if not row.get("correct"):
        return "answered_wrong"
    return None


def per_head_separations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pos = [r for r in rows if group_of(r) == "answered_wrong"]
    neg = [r for r in rows if group_of(r) == "refused"]
    if not pos or not neg:
        raise ReadSignError(
            f"need both groups; got answered_wrong={len(pos)} refused={len(neg)}"
        )
    sample = pos[0].get("prompt_read_per_head")
    if not isinstance(sample, dict) or not sample:
        raise ReadSignError("rows have no prompt_read_per_head dict")
    heads = list(sample.keys())
    per_head = []
    for h in heads:
        wrong = [float(r["prompt_read_per_head"][h]) for r in pos if h in r.get("prompt_read_per_head", {})]
        refuse = [float(r["prompt_read_per_head"][h]) for r in neg if h in r.get("prompt_read_per_head", {})]
        mw, mr = st.mean(wrong), st.mean(refuse)
        sep = mw - mr
        per_head.append({
            "head": h,
            "wrong_mean": round(mw, 4),
            "refuse_mean": round(mr, 4),
            "separation": round(sep, 4),
            "sign": "+" if sep > 0 else "-",
        })
    return {"per_head": per_head, "n_answered_wrong": len(pos), "n_refused": len(neg)}


def classify(per_head: list[dict[str, Any]]) -> dict[str, Any]:
    seps = [h["separation"] for h in per_head]
    n_pos = sum(1 for s in seps if s > 0)
    n_neg = sum(1 for s in seps if s < 0)
    n = len(seps)
    agg = st.mean(seps) if seps else 0.0
    minority = min(n_pos, n_neg)
    if minority == 0:
        sign = "+" if n_pos else "-"
        return {
            "classification": "unanimous",
            "verdict": (
                f"UNANIMOUS read: all {n}/{n} heads separate wrong-vs-refuse with the "
                f"same sign ({sign}), mean separation {agg:+.3f}. The aggregate read is "
                f"not cancelling heads; any A.4 steering inversion is a write-side "
                f"property on a clean uniform read (cf. Tan 2407.12404 anti-steerability)."
            ),
            "detail": {"n_heads": n, "n_pos": n_pos, "n_neg": n_neg, "agg_separation": round(agg, 4)},
        }
    return {
        "classification": "split",
        "verdict": (
            f"SPLIT read: {n_pos}/{n} heads read +, {n_neg}/{n} read - (mean {agg:+.3f}). "
            f"The aggregate axis masks per-head disagreement; a per-head steering sweep is "
            f"needed before treating F as a single read axis."
        ),
        "detail": {"n_heads": n, "n_pos": n_pos, "n_neg": n_neg, "agg_separation": round(agg, 4)},
    }


def run_from_rows(rows: list[dict[str, Any]], *, source: str | None = None) -> dict[str, Any]:
    if not rows:
        raise ReadSignError("no rows")
    sep = per_head_separations(rows)
    verdict = classify(sep["per_head"])
    return {
        "ok": True,
        "analysis_type": "mechinterp_head_read_sign_consistency",
        "rows": source,
        "n_rows": len(rows),
        **sep,
        **verdict,
    }


def run(rows_path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ReadSignError(f"no rows in {rows_path}")
    return run_from_rows(rows, source=str(rows_path))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", required=True, type=Path, help="read-trajectory rows.jsonl")
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run(args.rows)
    for h in result["per_head"]:
        print(f"  {h['head']:>8}  wrong={h['wrong_mean']:>8.3f}  refuse={h['refuse_mean']:>8.3f}"
              f"  sep={h['separation']:>8.3f}  [{h['sign']}]", file=sys.stderr)
    print(f"\nVERDICT [{result['classification']}]: {result['verdict']}", file=sys.stderr)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
