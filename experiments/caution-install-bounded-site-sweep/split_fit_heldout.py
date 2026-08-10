#!/usr/bin/env python3
"""Stage 1b (CPU): FIT / HELD-OUT split over the pool `mine_pool.py` wrote.

Ported from `experiments/j-space-cross-family-layer-contrast/split_fit_heldout.py`
(itself from `doubt-gated-caution-tighten/split_fit_heldout.py`): deterministic,
stratified-by-category split at seed 20260707, FIT_FRAC 0.40, over the two
gate-relevant roles (confab, known_correct_answered). `unknown_refused` is
FIT-only scaffold and is never split (cell.yaml `surface.split.never_split`).

Output: `analysis-committed/split_manifest.json` (ID-only: row_key, role,
category, split -- no question text, no aliases).
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    load_cell,
    load_jsonl,
    rows_with_text_path,
    split_manifest_path,
    write_json,
)

# This stage splits the TRAINED substrate's pool only (mine_pool.py mines
# trained exclusively; see sweep_lib.rows_with_text_path/split_manifest_path
# docstrings, F8). ROWS_WITH_TEXT/SPLIT_MANIFEST below are identical to the
# pre-fix hardcoded paths -- cell.yaml's registered surface.rows_path /
# surface.split_manifest are unchanged.
ROWS_WITH_TEXT = rows_with_text_path("trained")
SPLIT_MANIFEST = split_manifest_path("trained")

GATE_ROLES = ("confab", "known_correct_answered")


def stratified_split(rows: list[dict], fit_frac: float, seed: int) -> dict[str, str]:
    by_cat: dict[str, list[str]] = {}
    for r in rows:
        by_cat.setdefault(r.get("category") or "unknown", []).append(r["row_key"])
    assignment: dict[str, str] = {}
    for cat in sorted(by_cat):
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
    cell = load_cell()
    fit_frac = float(cell["surface"]["split"]["fit_frac"])
    seed = int(cell["surface"]["split"]["split_seed"])
    never_split = set(cell["surface"]["split"].get("never_split", []))

    rows = load_jsonl(args.rows_path or ROWS_WITH_TEXT)
    if not rows:
        print(f"[split] ERROR: no rows at {args.rows_path or ROWS_WITH_TEXT}. "
              "Run mine_pool.py first.", file=sys.stderr)
        return 1

    by_role: dict[str, list[dict]] = {}
    for r in rows:
        by_role.setdefault(r["role"], []).append(r)

    out_rows = []
    counts = {}
    for role in GATE_ROLES:
        role_rows = by_role.get(role, [])
        assignment = stratified_split(role_rows, fit_frac, seed)
        n_fit = sum(1 for v in assignment.values() if v == "fit")
        n_held = sum(1 for v in assignment.values() if v == "held_out")
        counts[role] = {"n_total": len(role_rows), "n_fit": n_fit, "n_held_out": n_held}
        print(f"[split] {role}: total={len(role_rows)} fit={n_fit} held_out={n_held}", flush=True)
        for r in role_rows:
            out_rows.append({
                "row_key": r["row_key"], "role": role,
                "category": r.get("category"), "split": assignment[r["row_key"]],
            })

    n_scaffold = 0
    for role in never_split:
        scaffold_rows = by_role.get(role, [])
        n_scaffold += len(scaffold_rows)
        for r in scaffold_rows:
            out_rows.append({"row_key": r["row_key"], "role": role, "category": r.get("category"), "split": "fit"})
    print(f"[split] {sorted(never_split)}: total={n_scaffold} (100% fit-only scaffold, never split)", flush=True)

    out = {
        "seed": seed, "fit_frac": fit_frac, "gate_roles": list(GATE_ROLES),
        "never_split": sorted(never_split), "counts": counts,
        "n_scaffold_fit_only": n_scaffold, "rows": out_rows,
    }
    write_json(SPLIT_MANIFEST, out)
    print(f"[split] wrote {SPLIT_MANIFEST} ({len(out_rows)} row assignments)", flush=True)

    g0a_confab = counts.get("confab", {}).get("n_held_out", 0) >= 150
    g0a_known = counts.get("known_correct_answered", {}).get("n_held_out", 0) >= 250
    print(f"[split] G0a pool power: held_out confab >= 150: {g0a_confab} "
          f"({counts.get('confab', {}).get('n_held_out', 0)}); "
          f"held_out known_correct_answered >= 250: {g0a_known} "
          f"({counts.get('known_correct_answered', {}).get('n_held_out', 0)})", flush=True)
    return 0 if (g0a_confab and g0a_known) else 1


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows-path", default=None)
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
