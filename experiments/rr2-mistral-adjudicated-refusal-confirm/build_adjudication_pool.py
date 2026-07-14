#!/usr/bin/env python3
"""Blinded adjudication pool builder for
rr2-mistral-adjudicated-refusal-confirm.

Per AMENDMENT.md "Design" item 2 and cell.yaml `adjudication`: after
generation, builds a deterministic pool of bare, label-stripped texts for a
human (or context-free agent) adjudicator to grade against the registered
rubric, ONCE, before any label is revealed.

CORE POOL: every held-out row, across the four registered arms (baseline,
gated, random_direction, dose_knowns_ungated -- cell.yaml
`adjudication.pool_source_arms`), both populations (fired confab, known
-correct), that the already-persisted `refused_v2` field (written by
`gen_lib.grade_row` at generation time, per the data-exhaust rule) marks
False. Deduplicated on (row_key, arm) -- NOT on row_key alone, because
`gated` and `random_direction` write two DIFFERENT generation texts for the
same fired row_key (real instrument vs. placebo direction), and both are
legitimate, distinct pool candidates. Non-fired rows are NOT synthesized
into the `gated`/`random_direction` pool under a duplicate-of-baseline entry:
their text there would be byte-identical to their own `baseline` row (the
gate did not fire, so no dose was applied), so including them again would
only pad the pool with a no-information duplicate of a row already present
under the `baseline` arm.

DECOYS (interpretation of AMENDMENT.md's "decoy rows drawn from the placebo
and known-correct sets" made at harness-build time, recorded in cell.yaml
`adjudication.decoys` and NOTEBOOK.md):
  clear_negative  sampled from the `baseline` arm's known_correct_answered
                  rows that are well_formed_correct AND refused_v2 is False
                  -- an unambiguous committed, correct answer. Calibration
                  check against OVER-crediting (the adjudicator should not
                  mark these as abstentions).
  clear_positive  sampled from the `random_direction` (placebo) arm's rows
                  (either population) where refused_v2 IS True -- an
                  unambiguous abstention, already credited without
                  adjudication. Calibration check against UNDER-crediting.
Decoys are NEVER part of the scored population (`apply_adjudication.py`
excludes every row the mapping marks `is_decoy: true` from every rate); they
exist only to make the pool's composition unguessable from its size/shape and
to give the lead a way to sanity-check adjudicator behavior without touching
the core pool's blinding.

OUTPUTS:
  analysis/adjudication_pool.jsonl              gitignored; [{opaque_id, text}]
  analysis/adjudication_id_map.jsonl             gitignored; full mapping
      {opaque_id, row_key, arm, role, is_decoy, decoy_type}
  analysis-committed/adjudication_pool_manifest.json   COMMITTED; ONLY
      {pool_sha256, row_count, seed, id_salt_sha256, opaque_ids (sorted)} --
      no text, no row_key, no arm/role, per this experiment's containment
      rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
ARMS = ("baseline", "gated", "random_direction", "dose_knowns_ungated")
DECOY_FRACTION = 0.15  # of the core pool size, split evenly between the two decoy types


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def runlog_path(arm: str, analysis_dir: Path) -> Path:
    return analysis_dir / "runlog" / f"heldout__{arm}.jsonl"


def load_arm_rows(analysis_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {arm: load_jsonl(runlog_path(arm, analysis_dir)) for arm in ARMS}


def build_core_pool(arm_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """One entry per (row_key, arm) where `refused_v2` is False. Each entry
    keeps the FULL underlying row (not just the blinded fields) so
    `build_decoys` can carve `clear_negative` candidates OUT of this exact
    set without creating a duplicate (row_key, arm) elsewhere -- the blinded
    pool file strips everything except opaque_id/text at write time."""
    core: list[dict[str, Any]] = []
    for arm, rows in arm_rows.items():
        for r in rows:
            if not r.get("refused_v2", False):
                core.append({**r, "arm": arm})
    return core


def build_decoys(
    core: list[dict[str, Any]], arm_rows: dict[str, list[dict[str, Any]]], rng: random.Random,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (remaining_core, decoys). Decoys are carved OUT of `core`
    (never sampled independently and re-added), which is what guarantees no
    (row_key, arm) pair -- and therefore no opaque_id, since the id is a pure
    function of (salt, row_key, arm) -- can appear twice in the combined pool:

      clear_negative  drawn FROM core: baseline-arm known_correct_answered
                      rows that are well_formed_correct (an unambiguous
                      committed, correct answer). These already satisfy
                      core's own refused_v2==False criterion, so they are
                      REMOVED from core and re-labeled as decoys rather than
                      counted twice.
      clear_positive  drawn from the random_direction arm's rows where
                      refused_v2 IS True -- disjoint from core by
                      construction (core requires refused_v2==False), so no
                      removal is needed for this half.
    """
    n_each = max(1, round(len(core) * DECOY_FRACTION / 2)) if core else 0
    decoys: list[dict[str, Any]] = []

    neg_candidates_idx = [
        i for i, r in enumerate(core)
        if r["arm"] == "baseline" and r.get("role") == "known_correct_answered" and r.get("well_formed_correct")
    ]
    rng.shuffle(neg_candidates_idx)
    chosen_neg = set(neg_candidates_idx[:n_each])
    remaining_core = [r for i, r in enumerate(core) if i not in chosen_neg]
    for i in sorted(chosen_neg):
        r = core[i]
        decoys.append({**r, "decoy_type": "clear_negative"})

    placebo_refused = [r for r in arm_rows.get("random_direction", []) if r.get("refused_v2", False)]
    pool_pos = placebo_refused[:]
    rng.shuffle(pool_pos)
    for r in pool_pos[:n_each]:
        decoys.append({**r, "arm": "random_direction", "decoy_type": "clear_positive"})

    return remaining_core, decoys


def salted_opaque_id(salt: str, row_key: str, arm: str) -> str:
    return hashlib.sha256(f"{salt}:{row_key}:{arm}".encode("utf-8")).hexdigest()[:16]


def build_pool(
    arm_rows: dict[str, list[dict[str, Any]]], seed: int, salt: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (blinded_pool, id_map). `blinded_pool` entries are
    {opaque_id, text} ONLY, in the seeded-shuffle order. `id_map` entries
    carry the full unblinded record, written to a SEPARATE gitignored file,
    never merged into the blinded pool."""
    core = build_core_pool(arm_rows)
    remaining_core, decoys = build_decoys(core, arm_rows, random.Random(seed))

    combined = remaining_core + decoys
    # Deterministic shuffle keyed on the registered seed: same input list,
    # same seed -> same order, every time (test_shuffle_deterministic_under_seed).
    random.Random(seed).shuffle(combined)

    blinded_pool = []
    id_map = []
    for item in combined:
        opaque_id = salted_opaque_id(salt, item["row_key"], item["arm"])
        blinded_pool.append({"opaque_id": opaque_id, "text": item.get("answer_text", "")})
        id_map.append({
            "opaque_id": opaque_id, "row_key": item["row_key"], "arm": item["arm"],
            "role": item.get("role"), "is_decoy": "decoy_type" in item,
            "decoy_type": item.get("decoy_type"),
        })
    return blinded_pool, id_map


def cmd_build(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    arm_rows = load_arm_rows(analysis_dir)
    missing_arms = [arm for arm, rows in arm_rows.items() if not rows and arm != "gated" and arm != "random_direction"]
    # gated/random_direction may legitimately be empty if the doubt gate never
    # fired on this held-out pool (an extreme but possible outcome); baseline
    # and dose_knowns_ungated should never be empty for a completed run.
    if "baseline" not in arm_rows or not arm_rows["baseline"]:
        raise SystemExit(f"missing/empty baseline run log at {runlog_path('baseline', analysis_dir)}; run heldout_scorer.py first.")
    if not arm_rows.get("dose_knowns_ungated"):
        raise SystemExit(f"missing/empty dose_knowns_ungated run log at {runlog_path('dose_knowns_ungated', analysis_dir)}; run heldout_scorer.py first.")

    salt = args.salt or secrets.token_hex(32)
    blinded_pool, id_map = build_pool(arm_rows, args.seed, salt)

    pool_path = analysis_dir / "adjudication_pool.jsonl"
    write_jsonl(pool_path, blinded_pool)
    write_jsonl(analysis_dir / "adjudication_id_map.jsonl", id_map)

    pool_bytes = pool_path.read_bytes()
    manifest = {
        "pool_sha256": hashlib.sha256(pool_bytes).hexdigest(),
        "row_count": len(blinded_pool),
        "seed": args.seed,
        "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "opaque_ids": sorted(item["opaque_id"] for item in blinded_pool),
        "n_core": sum(1 for m in id_map if not m["is_decoy"]),
        "n_decoy": sum(1 for m in id_map if m["is_decoy"]),
    }
    write_json(committed_dir / "adjudication_pool_manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != "opaque_ids"}, indent=2), flush=True)
    print(
        f"\n[build_adjudication_pool] wrote {len(blinded_pool)} bare texts to "
        f"{pool_path} (gitignored). Send this file to the adjudicator. The "
        f"opaque_id -> row_key mapping stays in {analysis_dir / 'adjudication_id_map.jsonl'} "
        f"(gitignored) and must NOT be read until apply_adjudication.py verifies "
        f"the adjudicator's graded-file hash is committed (see apply_adjudication.py --help).",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=20260713)
    ap.add_argument("--salt", default=None, help="override the random id salt (test hook; omit for a fresh random salt)")
    ap.add_argument("--analysis-dir", default=None)
    ap.add_argument("--committed-dir", default=None)
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
