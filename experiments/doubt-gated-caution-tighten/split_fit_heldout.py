#!/usr/bin/env python3
"""Doubt-gated caution snap -- FIT / HELD-OUT split (CPU-only, no GPU).

Builds ONE deterministic, stratified-by-category_canon FIT/HELD-OUT split
over the two gate-relevant roles (confab, known_correct_answered) and writes
it as an ID-ONLY manifest (row_key + role + category_canon + split -- no
question text, no aliases) under analysis-committed/, so the split itself is
committed and auditable without ever holding row text in git.

FIT (40%): used to (a) refit u_d / pos_ctrl / neg_ctrl / c_hat
(build_directions.py) and (b) choose tau (gate_fit.py). HELD-OUT (60%): used
for EVERY reported gate number (pipeline.py) -- the gate decides who gets
dosed on rows the direction fit and tau choice never touched.

unknown_refused (the doubt axis's "unknown" pole and part of the AK Stage-1
pos_ctrl/neg_ctrl fit population) is NOT split: it is never itself a gated/
graded row in this instrument, only fitting scaffold, so 100% of it is
available to the FIT stage.

Split fraction (40/60) and seed are THIS harness's own implementation
choice (not specified by the locked design, which only requires "a FIT split
... and HELD-OUT ... every gate number ... on HELD-OUT"); documented here and
in AMENDMENT.md rather than tuned after seeing any gate result.

Output: analysis-committed/split_manifest.json
  {"seed": ..., "fit_frac": ..., "rows": [{"row_key", "role",
   "category_canon", "split": "fit"|"held_out"}, ...]}
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

EXTRACT_MANIFEST = ANALYSIS / "l34_anchor_extract_manifest.json"
OUT_PATH = COMMITTED / "split_manifest.json"

SPLIT_SEED = 20260707
FIT_FRAC = 0.40
GATE_ROLES = ("confab", "known_correct_answered")


def stratified_split(rows: list[dict], fit_frac: float, seed: int) -> dict[str, str]:
    """Deterministic stratified split by category_canon. Within each
    category, rows are sorted by row_key (deterministic order independent of
    on-disk row order), then a fixed-seed RNG shuffles the per-category order
    and the first round(fit_frac * n_cat) rows in that shuffled order go to
    "fit", the rest to "held_out". Returns {row_key: "fit"|"held_out"}."""
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit-frac", type=float, default=FIT_FRAC)
    ap.add_argument("--seed", type=int, default=SPLIT_SEED)
    args = ap.parse_args()

    manifest = json.loads(EXTRACT_MANIFEST.read_text())
    assert manifest["substrate"] == "bf16"
    assert manifest["base_model"] == "unsloth/Qwen3-4B"

    rows_by_role: dict[str, list[dict]] = {}
    for rm in manifest["rows"]:
        rows_by_role.setdefault(rm["role"], []).append(rm)

    out_rows: list[dict] = []
    counts: dict[str, dict[str, int]] = {}
    for role in GATE_ROLES:
        role_rows = rows_by_role.get(role, [])
        assignment = stratified_split(role_rows, args.fit_frac, args.seed)
        n_fit = sum(1 for v in assignment.values() if v == "fit")
        n_held = sum(1 for v in assignment.values() if v == "held_out")
        counts[role] = {"n_total": len(role_rows), "n_fit": n_fit, "n_held_out": n_held}
        print(f"[split] {role}: total={len(role_rows)} fit={n_fit} held_out={n_held}")
        # category_canon lookup for the manifest rows in this role.
        cat_by_key = {rm["row_key"]: None for rm in role_rows}
        for rm in role_rows:
            cat_by_key[rm["row_key"]] = rm.get("category_canon")
        for rm in role_rows:
            out_rows.append({
                "row_key": rm["row_key"],
                "role": role,
                "split": assignment[rm["row_key"]],
            })

    n_unknown_refused = len(rows_by_role.get("unknown_refused", []))
    print(f"[split] unknown_refused: total={n_unknown_refused} (100% fit-only scaffold, not split)")

    out = {
        "seed": args.seed,
        "fit_frac": args.fit_frac,
        "gate_roles": list(GATE_ROLES),
        "counts": counts,
        "n_unknown_refused_fit_only": n_unknown_refused,
        "extract_manifest_n_rows_extracted": manifest["n_rows_extracted"],
        "rows": out_rows,
    }
    COMMITTED.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"[split] wrote {OUT_PATH} ({len(out_rows)} row assignments)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
