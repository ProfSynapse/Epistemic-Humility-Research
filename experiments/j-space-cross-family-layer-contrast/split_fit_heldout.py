#!/usr/bin/env python3
"""Cross-family J-space layer contrast -- FIT / HELD-OUT split (CPU-only).

Ported from `experiments/doubt-gated-caution-tighten/split_fit_heldout.py`,
parameterized by `--family`. Builds ONE deterministic, stratified-by-
category_canon FIT/HELD-OUT split over the two gate-relevant roles (confab,
known_correct_answered) per family, from that family's own
`mine_eval_pool.py` output, and writes it as an ID-ONLY manifest under
`analysis-committed/<family>/split_manifest.json`.

FIT (40%): used to (a) refit u_d / pos_ctrl / neg_ctrl / c_hat
(build_directions.py) and (b) choose tau (gate_fit.py). HELD-OUT (60%): used
for the OUTCOME layer contrast (run_contrast.py).

unknown_refused is NOT split: it is never itself a gated/graded row in this
instrument, only fitting scaffold (matches the predecessor's own rationale).

Split fraction (40/60) and seed are the SAME implementation choice as the
Qwen3-4B predecessor, kept identical across families for comparability, not
re-tuned per family.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402

sys.path.insert(0, str(HERE))
from family_config import FAMILY_SLUGS  # noqa: E402

SPLIT_SEED = 20260707
FIT_FRAC = 0.40
GATE_ROLES = ("confab", "known_correct_answered")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def stratified_split(rows: list[dict], fit_frac: float, seed: int) -> dict[str, str]:
    """Deterministic stratified split by category_canon, identical method to
    the Qwen3-4B predecessor's own `stratified_split`."""
    by_cat: dict[str, list[str]] = {}
    for r in rows:
        by_cat.setdefault(r.get("category_canon"), []).append(r["row_key"])

    assignment: dict[str, str] = {}
    for cat in sorted(by_cat, key=lambda c: (c is None, c)):
        keys = sorted(by_cat[cat])
        rng = random.Random(f"{seed}:{cat}")
        rng.shuffle(keys)
        n_fit = round(fit_frac * len(keys))
        for k in keys[:n_fit]:
            assignment[k] = "fit"
        for k in keys[n_fit:]:
            assignment[k] = "held_out"
    return assignment


def run(args: argparse.Namespace) -> int:
    family = args.family
    rows_path = HERE / "analysis" / family / "eval_rows.jsonl"
    out_path = HERE / "analysis-committed" / family / "split_manifest.json"
    if not rows_path.is_file():
        print(f"[split:{family}] ERROR: {rows_path} not found. Run mine_eval_pool.py "
              f"--family {family} first.", file=sys.stderr)
        return 1

    rows = load_jsonl(rows_path)
    rows_by_role: dict[str, list[dict]] = {}
    for r in rows:
        rows_by_role.setdefault(r["role"], []).append(r)

    out_rows: list[dict] = []
    counts: dict[str, dict[str, int]] = {}
    for role in GATE_ROLES:
        role_rows = rows_by_role.get(role, [])
        assignment = stratified_split(role_rows, args.fit_frac, args.seed)
        n_fit = sum(1 for v in assignment.values() if v == "fit")
        n_held = sum(1 for v in assignment.values() if v == "held_out")
        counts[role] = {"n_total": len(role_rows), "n_fit": n_fit, "n_held_out": n_held}
        print(f"[split:{family}] {role}: total={len(role_rows)} fit={n_fit} held_out={n_held}")
        for r in role_rows:
            out_rows.append({
                "row_key": r["row_key"], "role": role,
                "category_canon": r.get("category_canon"),
                "split": assignment[r["row_key"]],
            })

    n_unknown_refused = len(rows_by_role.get("unknown_refused", []))
    print(f"[split:{family}] unknown_refused: total={n_unknown_refused} "
          "(100% fit-only scaffold, not split)")

    out = {
        "family": family, "seed": args.seed, "fit_frac": args.fit_frac,
        "gate_roles": list(GATE_ROLES), "counts": counts,
        "n_unknown_refused_fit_only": n_unknown_refused,
        "rows": out_rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[split:{family}] wrote {out_path} ({len(out_rows)} row assignments)")
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    ap.add_argument("--fit-frac", type=float, default=FIT_FRAC)
    ap.add_argument("--seed", type=int, default=SPLIT_SEED)
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
