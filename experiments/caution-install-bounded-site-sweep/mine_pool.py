#!/usr/bin/env python3
"""Stage 1 (AMENDMENT.md Run plan): mine and grade the trained-substrate pool,
reusing the feasibility probe's rows. GPU (resumable), G0a/G0b gated.

Reuse, not re-derivation (D4: role labels are behavior-dependent and are
re-mined per checkpoint; nothing from the raw-base pool or the archived L35
work ports):

  - UNKNOWN-label side is COMPLETE from the probe: Stage B's 400 draws
    (`analysis/probe_generations_private.jsonl`) plus the PI-approved full-
    corpus census extension (`analysis/probe_census_generations_private.jsonl`,
    NOTEBOOK.md 2026-08-09T02:15Z) together cover the full M_u=3496 gold-
    unanswerable corpus with 260 confab >= the registered 250 floor. This
    stage does NOT regenerate on the unknown side; it only re-reads those two
    private files and reapplies `sweep_lib.grade_role` (byte-identical to
    `probe_stage_b.grade_row`) so the harness owns one grading call site.
  - KNOWN-label side is INCOMPLETE from the probe: Stage B drew only 400 of
    the M_a=10000 candidates, yielding 89 known_correct_answered -- far short
    of the >= 417 total this cell's G0a needs (150/250 held-out at FIT_FRAC
    0.40, feasibility_probe.yaml pass_criterion.derivation). This stage mines
    ADDITIONAL known-label rows, in deterministic row_key order, excluding
    the 400 already probed, using the IDENTICAL generation contract and
    grading as the probe (imports `generate_one` from `probe_stage_b.py`
    rather than re-deriving it), until `--target-known-correct` is reached or
    the candidate pool is exhausted.

Output: `analysis/rows_with_text.jsonl` (gitignored; cell.yaml
`surface.rows_path`), one row per selected confab / known_correct_answered /
unknown_refused row: {row_key, role, question, aliases, source, category}.
Public: `analysis-committed/pool_manifest.json` (ID/role/count only, no text).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    REPO_ROOT,
    grade_role,
    load_jsonl,
    rows_with_text_path,
    write_json,
    write_jsonl_row,
)

# F16 fix: was hardcoded as Path("/home/profsynapse/code/Epistemic-Humility-Research"),
# a machine-local absolute path absent from experiment.yaml `inputs:` and
# unresolvable inside the container's /workspace mount. REPO_ROOT (sweep_lib.py)
# is computed relative to sweep_lib.py's own __file__, so it resolves correctly
# both on the host canonical checkout and under the container's /workspace bind
# mount. Resolved input path (relative to repo root, for the lead to add to
# experiment.yaml inputs at pin time):
#   experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl
EXPANSION_CANDIDATES = (
    REPO_ROOT
    / "experiments/divergent-pool-own-readout/analysis/phase1-migrated"
    / "probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl"
)

PROBE_STAGE_B = ANALYSIS / "probe_generations_private.jsonl"
PROBE_CENSUS = ANALYSIS / "probe_census_generations_private.jsonl"
MINED_KNOWN = ANALYSIS / "mined_known_generations_private.jsonl"

ROWS_WITH_TEXT = rows_with_text_path("trained")  # mine_pool.py mines the trained substrate only
POOL_MANIFEST = COMMITTED / "pool_manifest.json"

# feasibility_probe.yaml pass_criterion.derivation, restated: FIT_FRAC 0.40,
# held-out floors 150 confab / 250 known_correct_answered => total floors
# 250 / 417. --target-known-correct defaults to a modest margin over the
# floor (mining stops once the total known-correct pool clears it with room
# for the stratified split's rounding, not exactly at the floor).
REQUIRED_TOTAL_CONFAB = 250
REQUIRED_TOTAL_KNOWN_CORRECT = 417
# F22: derive the default margin from REQUIRED_TOTAL_KNOWN_CORRECT itself
# (traceable to the registered floor) instead of a bare literal (previously
# 460, disconnected from the 417 it was meant to pad) -- no governed doc
# registers 460 as a number, so this is a documentation/derivation fix, not a
# registered-threshold change.
KNOWN_CORRECT_TARGET_MARGIN_FRAC = 0.10
DEFAULT_TARGET_KNOWN_CORRECT = math.ceil(REQUIRED_TOTAL_KNOWN_CORRECT * (1 + KNOWN_CORRECT_TARGET_MARGIN_FRAC))


def load_known_candidates() -> list[dict]:
    """Deterministic row_key-sorted known-label candidates with aliases,
    matching probe_stage_a.py's `load_candidates()` known-side filter."""
    rows = []
    with EXPANSION_CANDIDATES.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("label") == "known" and row.get("aliases"):
                rows.append(row)
    rows.sort(key=lambda r: r["row_key"])
    return rows


def load_all_candidates() -> dict[str, dict]:
    """F2 fix: the full expansion-candidates corpus (question/aliases/
    category/source), keyed by row_key, covering BOTH known and unknown rows.
    This is the ONLY place question text lives for the 227-of-260 confab rows
    (and the bulk of unknown_refused) that come from the 3096-row census:
    `probe_stage_b.py`'s and `probe_census_extension.py`'s written generation
    records carry only {row_key, label, source, completion, n_new_tokens,
    terminated_naturally, <grade fields>} -- no question text at all (verified
    by reading both record-building blocks in full) -- and
    `probe_sampled_rows_private.jsonl` only covers the 800 Stage-B-probed
    rows, which are disjoint from the census's 3096 by construction
    (NOTEBOOK.md 2026-08-09T02:15Z). Reading metadata from the 800-row sample
    alone left 227 of 260 confab rows with an empty question field."""
    out: dict[str, dict] = {}
    with EXPANSION_CANDIDATES.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rk = row.get("row_key")
            if rk:
                out[rk] = row
    return out


def role_rows_from_generations(gens: list[dict]) -> list[dict]:
    """Reapply sweep_lib.grade_role to already-generated completions.
    Byte-identical to probe_stage_b.grade_row/probe_census_extension's reuse
    of it -- this stage owns one grading call site rather than trusting the
    probe's own stored `role` field, so a grading-logic change is caught
    everywhere at once."""
    out = []
    for rec in gens:
        row = {"row_key": rec["row_key"], "label": rec["label"], "aliases": rec.get("aliases", [])}
        grade = grade_role(row, rec.get("completion", ""))
        out.append({**rec, **grade})
    return out


def select_role_rows(graded: list[dict], candidates_by_key: dict[str, dict]) -> list[dict]:
    """F2 fix: `candidates_by_key` must be the FULL expansion-candidates
    corpus (`load_all_candidates()`), not just the 800-row probe sample --
    see that function's docstring for why the probe sample alone left most
    census rows with an empty question."""
    out = []
    for rec in graded:
        role = rec.get("role")
        if role not in ("confab", "known_correct_answered", "unknown_refused"):
            continue
        meta = candidates_by_key.get(rec["row_key"], {})
        out.append({
            "row_key": rec["row_key"], "role": role,
            "question": meta.get("question", ""),
            "aliases": meta.get("aliases", []) if role == "known_correct_answered" else [],
            "source": meta.get("source") or rec.get("source"),
            "category": meta.get("category", meta.get("source", "unknown")),
        })
    return out


def mine_additional_known(target_known_correct: int, max_new_tokens: int, flush_every: int) -> list[dict]:
    """Mine known-label rows beyond the probe's 400-row Stage B draw,
    deterministic order, resumable via MINED_KNOWN."""
    from probe_stage_b import generate_one, grade_row, load_model_and_tokenizer  # noqa: E402

    candidates = load_known_candidates()
    probed = load_jsonl(HERE / "analysis" / "probe_sampled_rows_private.jsonl")
    already = {r["row_key"] for r in probed if r.get("label") == "known"}
    remaining = [c for c in candidates if c["row_key"] not in already]
    print(f"[mine-pool] known-label candidates total={len(candidates)} "
          f"already_probed={len(already)} remaining={len(remaining)}", flush=True)

    prior = {r["row_key"]: r for r in load_jsonl(MINED_KNOWN)}
    have_known_correct = sum(1 for r in prior.values() if r.get("role") == "known_correct_answered")
    print(f"[mine-pool] resume: {len(prior)} known-label rows already mined "
          f"({have_known_correct} known_correct_answered so far)", flush=True)

    if have_known_correct >= target_known_correct:
        print("[mine-pool] target already met from a prior run; skipping generation.", flush=True)
        return list(prior.values())

    model, tokenizer, eos_ids = load_model_and_tokenizer()
    t0 = time.time()
    n_this_run = 0
    try:
        for idx, row in enumerate(remaining, start=1):
            if row["row_key"] in prior:
                continue
            gen = generate_one(model, tokenizer, eos_ids, row["question"])
            grade = grade_row({"row_key": row["row_key"], "label": "known", "aliases": row.get("aliases", [])},
                               gen["completion"])
            record = {
                "row_key": row["row_key"], "label": "known", "source": row.get("source"),
                "category": row.get("category", row.get("source", "unknown")),
                "question": row["question"], "aliases": row.get("aliases", []),
                "completion": gen["completion"], "n_new_tokens": gen["n_new_tokens"],
                "terminated_naturally": gen["terminated_naturally"], **grade,
            }
            write_jsonl_row(MINED_KNOWN, record)
            prior[row["row_key"]] = record
            n_this_run += 1
            if grade["role"] == "known_correct_answered":
                have_known_correct += 1
            if idx % flush_every == 0 or have_known_correct >= target_known_correct:
                elapsed_min = (time.time() - t0) / 60.0
                rpm = n_this_run / elapsed_min if elapsed_min > 0 else float("nan")
                print(f"[mine-pool] known scanned={idx}/{len(remaining)} "
                      f"known_correct_answered={have_known_correct}/{target_known_correct} "
                      f"rows/min={rpm:.1f}", flush=True)
            if have_known_correct >= target_known_correct:
                break
    finally:
        del model
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass
    return list(prior.values())


def run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("Refusing to run a GPU verb without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2
    if args.substrate != "trained":
        print(f"[mine-pool] ERROR: mine_pool.py mines and grades the TRAINED-substrate "
              f"pool only (AMENDMENT.md Run plan row 1); got --substrate {args.substrate!r}. "
              "raw_base has no registered mining stage in this harness (see harness "
              "remediation report, finding F8).", file=sys.stderr)
        return 2

    # F2 fix: the full expansion-candidates corpus (question/aliases/category
    # for every row_key, known and unknown), NOT just the 800-row probe
    # sample -- see load_all_candidates()'s docstring.
    all_candidates = load_all_candidates()

    stage_b = load_jsonl(PROBE_STAGE_B)
    census = load_jsonl(PROBE_CENSUS)
    unknown_gens = [r for r in stage_b if r.get("label") == "unknown"] + census
    graded_unknown = role_rows_from_generations(unknown_gens)

    unknown_selected = select_role_rows(graded_unknown, all_candidates)
    n_confab = sum(1 for r in unknown_selected if r["role"] == "confab")
    print(f"[mine-pool] unknown side (probe Stage B + census, full M_u): "
          f"confab={n_confab}", flush=True)
    if n_confab < REQUIRED_TOTAL_CONFAB:
        print(f"[mine-pool] ERROR: confab={n_confab} < required {REQUIRED_TOTAL_CONFAB} "
              "even after the full census. This should have been caught by the "
              "feasibility probe; refusing to proceed.", file=sys.stderr)
        return 1

    known_gens = mine_additional_known(args.target_known_correct, args.max_new_tokens, args.flush_every)
    stage_b_known = [r for r in stage_b if r.get("label") == "known"]
    graded_known = role_rows_from_generations(stage_b_known) + role_rows_from_generations(known_gens)
    known_selected = select_role_rows(graded_known, all_candidates)
    n_known_correct = sum(1 for r in known_selected if r["role"] == "known_correct_answered")
    print(f"[mine-pool] known side: known_correct_answered={n_known_correct}", flush=True)

    all_rows = unknown_selected + known_selected
    # De-duplicate defensively (row_key should be unique per label already).
    seen = set()
    deduped = []
    for r in all_rows:
        if r["row_key"] in seen:
            continue
        seen.add(r["row_key"])
        deduped.append(r)

    # F2 fix: HARD-FAIL, no partial pool file, if any selected row still has
    # empty question text after the metadata join -- this is the check that
    # would have caught the 227-of-260-empty-question pool before it ever
    # reached extraction/steering.
    empty_question = [r["row_key"] for r in deduped if not r.get("question")]
    if empty_question:
        print(f"[mine-pool] ERROR: {len(empty_question)} of {len(deduped)} selected rows "
              f"have EMPTY question text after the candidate-corpus metadata join "
              f"(first 5 row_keys: {empty_question[:5]}). Refusing to write "
              f"{ROWS_WITH_TEXT} with unrenderable rows.", file=sys.stderr)
        return 1

    ROWS_WITH_TEXT.parent.mkdir(parents=True, exist_ok=True)
    ROWS_WITH_TEXT.write_text("", encoding="utf-8")
    for r in deduped:
        write_jsonl_row(ROWS_WITH_TEXT, r)

    n_unknown_refused = sum(1 for r in deduped if r["role"] == "unknown_refused")
    manifest = {
        "stage": "caution_install_bounded_site_sweep_mine_pool",
        "unknown_side_source": "probe Stage B (400) + census extension (3096), full M_u=3496",
        "known_side_probe_draw": len(stage_b_known),
        "known_side_mined_additional": len(known_gens),
        "required_total_confab": REQUIRED_TOTAL_CONFAB,
        "required_total_known_correct": REQUIRED_TOTAL_KNOWN_CORRECT,
        "target_known_correct": args.target_known_correct,
        "counts": {
            "confab": sum(1 for r in deduped if r["role"] == "confab"),
            "known_correct_answered": sum(1 for r in deduped if r["role"] == "known_correct_answered"),
            "unknown_refused": n_unknown_refused,
            "total_rows": len(deduped),
        },
        "g0a_pool_power_confab_floor_met": n_confab >= REQUIRED_TOTAL_CONFAB,
        "g0a_pool_power_known_floor_met": n_known_correct >= REQUIRED_TOTAL_KNOWN_CORRECT,
        "rows_with_text_path": str(ROWS_WITH_TEXT),
        "containment_note": "counts/roles only; question text and aliases stay under gitignored analysis/",
    }
    write_json(POOL_MANIFEST, manifest)
    print(json.dumps(manifest, indent=2), flush=True)
    if n_known_correct < REQUIRED_TOTAL_KNOWN_CORRECT:
        print(f"[mine-pool] ERROR: known_correct_answered={n_known_correct} < required "
              f"{REQUIRED_TOTAL_KNOWN_CORRECT}. G0a will fail; increase --target-known-correct "
              "or scan more candidates.", file=sys.stderr)
        return 1
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    # F5 fix: run_sweep.py's driver appends --substrate and
    # --i-know-this-runs-on-gpu to every GPU stage invocation (STAGES["1"] is
    # device="gpu"); this script must declare both or the driver's own first
    # call fails with "unrecognized arguments".
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    ap.add_argument("--target-known-correct", type=int, default=DEFAULT_TARGET_KNOWN_CORRECT,
                     help="stop mining once known_correct_answered reaches this many "
                          f"(default: required {REQUIRED_TOTAL_KNOWN_CORRECT} + "
                          f"{int(KNOWN_CORRECT_TARGET_MARGIN_FRAC * 100)}%% margin for split rounding)")
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--flush-every", type=int, default=25)
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
