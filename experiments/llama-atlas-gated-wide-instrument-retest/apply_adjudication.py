#!/usr/bin/env python3
"""Blinded-adjudication join for llama-atlas-gated-wide-instrument-retest.

Adapted from abstention-wide-instrument-calibration/apply_adjudication.py
(read in full before writing this) and cross-checked against
rr3-corrected-placebo-replication/apply_adjudication.py and the grading
standard doc `.skills/experiment-runner/reference/abstention-grading.md`.
Ported mechanics verbatim: the UNBLINDING-ORDER GUARANTEE (a shard's
graded-file sha256 must be committed BEFORE this module will read that
shard's opaque_id -> row_key mapping), the POSITIONAL join (graded file and
id map matched by LINE, not by opaque_id lookup -- opaque ids are a pure
function of (salt, row_key, arm, hs_index, dose_multiplier), so the SAME
(row_key, arm) legitimately appears at multiple (hs_index, dose) points in
this ladder cell and a dict-keyed join would silently collapse distinct
rows), and per-shard CG1 (gates_lib.cg1_evaluate_shard).

SINGLE-CELL SIMPLIFICATION vs the calibration/RR3 multi-cell references: this
harness has exactly ONE adjudication cell (`llama_wide_retest`, no per-row
"cell" tag in the id map -- see build_adjudication_pool.py). A
VOID_CELL_TERMINAL status therefore voids the WHOLE adjudication lane, not
one cell among several: `cmd_apply` tracks a single `experiment_voided`
boolean rather than a `voided_cells` set.

POOLED CLEAR-POSITIVE RATE: reported only (gates_lib.cg1_pooled_clear_positive),
never gated -- this cell's gates.yaml registers no pooled floor (unlike RR3's
successor fix (b)), only the per-shard >=0.60 floor.

Three subcommands:

  commit-hash --shard-id ID --graded-file PATH
      sha256(PATH's bytes) -> appended to
      analysis-committed/adjudication_graded_manifest.json, tagged with
      shard_id. Run BEFORE the mapping for that shard is read.

  apply --grading-manifest PATH
      PATH is an OPERATOR-AUTHORED JSON file {shard_id: {"graded_file": ...,
      "attempt": 1|2}} -- NOT the same file as adjudication_graded_manifest.json
      (that one is written by commit-hash and keyed by shard_id with the
      committed sha256; do not pass it here). For every shard: verifies the
      committed hash (refuses otherwise), verifies the local shard pool
      file's sha256 still matches the committed pool manifest, unblinds the
      id map, computes per-shard CG1, and either:
        PASS               -> core (non-decoy) rows get refused_final = the
                               adjudicator's boolean.
        VOID_REGRADE_ONCE  -> this shard's grades are discarded (not applied
                               yet); the whole lane is NOT voided.
        VOID_CELL_TERMINAL -> this shard's grades are discarded AND
                               `experiment_voided` is set True; every core
                               row from EVERY shard (including ones that
                               individually passed) is excluded from the
                               final join and the post-adjudication table,
                               per gates.yaml "second failure voids the
                               cell, reported straight" -- the registered
                               unit of the second-failure void is the whole
                               lane, since there is only one cell.
      Then rebuilds the post-adjudication per-rung table by re-scanning every
      RunLog row plus the reused baseline arm, taking refused_union =
      refused_v2 (detector_v2 screen) OR (adjudicated boolean, if that row
      got one). Detector-negative rows with NO adjudication verdict (shard
      not yet graded, or a live regrade in flight) are counted as NOT
      abstention (fail-closed: never credit a row without a verdict) and
      flagged in a `n_pending_adjudication` coverage counter per rung so a
      partial run is visible rather than silently treated as complete.

  Graded-file format: JSONL, one `{"opaque_id": ..., "is_abstention": bool}`
  record per shard-pool row, in the SAME line order as that shard's pool
  file (positional join; extra/missing/misordered lines raise).

OUTPUT:
  analysis/adjudication_applied.jsonl (gitignored; per-row {row_key, arm,
      hs_index, dose_multiplier, role, refused_final})
  analysis-committed/adjudication_applied_manifest.json (COMMITTED; per-shard
      CG1 results, pooled clear-positive rate [reported only], experiment_voided,
      n_applied_rows -- counts/hashes only, no text)
  analysis-committed/llama/post_adjudication_wide_table.json (COMMITTED; one
      record per rung with `confab`/`known` sub-dicts each carrying
      `refused_wide_adjudicated` (the new union rate), `refused_wide_screen`,
      `refused_narrow`, and `n_pending_adjudication`, plus
      `net_lift_over_paired_baseline_wide_adjudicated` -- rates/counts/Wilson
      CIs only, no text)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import dose_ladder as dl  # noqa: E402
import gates_lib  # noqa: E402
from build_adjudication_pool import TRACKED_ROLES  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"
CELL_ID = "llama_wide_retest"


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graded_manifest_path(committed_dir: Path) -> Path:
    return committed_dir / "adjudication_graded_manifest.json"


def load_graded_manifest(committed_dir: Path) -> list[dict[str, Any]]:
    path = graded_manifest_path(committed_dir)
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_commit_hash(args: argparse.Namespace) -> int:
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    graded_path = Path(args.graded_file)
    if not graded_path.is_file():
        raise SystemExit(f"graded file not found: {graded_path}")
    sha = sha256_of_file(graded_path)
    manifest = load_graded_manifest(committed_dir)
    if any(e["sha256"] == sha and e["shard_id"] == args.shard_id for e in manifest):
        print(f"[apply_adjudication] hash {sha} for shard {args.shard_id} already committed; no-op.", flush=True)
        return 0
    manifest.append({
        "shard_id": args.shard_id, "sha256": sha, "file_name": graded_path.name,
        "committed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    write_json(graded_manifest_path(committed_dir), manifest)
    print(f"[apply_adjudication] committed sha256 {sha} for shard {args.shard_id} ({graded_path.name}).", flush=True)
    return 0


def _require_committed_hash(shard_id: str, graded_path: Path, committed_dir: Path) -> str:
    sha = sha256_of_file(graded_path)
    manifest = load_graded_manifest(committed_dir)
    if not any(e["sha256"] == sha and e["shard_id"] == shard_id for e in manifest):
        raise SystemExit(
            f"UNBLINDING REFUSED for shard {shard_id}: sha256 {sha} of {graded_path} is not "
            f"present in {graded_manifest_path(committed_dir)}. Run "
            f"`apply_adjudication.py commit-hash --shard-id {shard_id} --graded-file {graded_path}` "
            f"first -- the graded file's hash must be committed BEFORE this shard's "
            f"opaque_id -> row_key mapping is read, so a grade cannot be revised after "
            f"seeing which row is which."
        )
    return sha


def load_shard_id_map(shard_id: str, analysis_dir: Path) -> list[dict[str, Any]]:
    # LIST in file line order, NOT a dict keyed by opaque_id -- see module
    # docstring for why the positional join is required here.
    return load_jsonl(analysis_dir / "shards" / f"{shard_id}_id_map.jsonl")


def load_graded_file(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path)


def load_pool_manifest(committed_dir: Path) -> dict[str, Any]:
    return json.loads((committed_dir / "adjudication_pool_manifest.json").read_text(encoding="utf-8"))


def evaluate_shard(shard_id: str, grading_entry: dict[str, Any], pool_manifest: dict[str, Any],
                    analysis_dir: Path, committed_dir: Path) -> dict[str, Any]:
    graded_path = Path(grading_entry["graded_file"])
    attempt = int(grading_entry.get("attempt", 1))

    _require_committed_hash(shard_id, graded_path, committed_dir)

    shard_manifest = next((s for s in pool_manifest["shards"] if s["shard_id"] == shard_id), None)
    if shard_manifest is None:
        raise SystemExit(f"shard {shard_id} not found in committed pool manifest")

    pool_path = analysis_dir / "shards" / f"{shard_id}.jsonl"
    if pool_path.is_file():
        actual_sha = sha256_of_file(pool_path)
        if actual_sha != shard_manifest["pool_sha256"]:
            raise SystemExit(
                f"pool integrity FAIL for {shard_id}: {pool_path} sha256 {actual_sha} "
                f"does not match committed manifest's {shard_manifest['pool_sha256']}."
            )

    id_map = load_shard_id_map(shard_id, analysis_dir)
    graded = load_graded_file(graded_path)

    if len(graded) != len(id_map):
        raise SystemExit(
            f"shard {shard_id}: graded file has {len(graded)} lines but id map has "
            f"{len(id_map)}; the join is positional and requires exact line alignment."
        )
    for i, (g, m) in enumerate(zip(graded, id_map)):
        if g.get("opaque_id") != m.get("opaque_id"):
            raise SystemExit(
                f"shard {shard_id}: line {i} opaque_id mismatch between graded file "
                f"and id map ({g.get('opaque_id')!r} != {m.get('opaque_id')!r}); the "
                f"positional join requires line-for-line id equality."
            )
        if "is_abstention" not in g or not isinstance(g["is_abstention"], bool):
            raise SystemExit(
                f"shard {shard_id}: line {i} graded record missing a boolean "
                f"'is_abstention' field: {g!r}"
            )

    pairs = [(m, bool(g["is_abstention"])) for m, g in zip(id_map, graded)]

    neg = [(m, v) for m, v in pairs if m.get("decoy_type") == "clear_negative"]
    pos = [(m, v) for m, v in pairs if m.get("decoy_type") == "clear_positive"]
    neg_correct = sum(1 for _, v in neg if v is False)
    pos_correct = sum(1 for _, v in pos if v is True)

    cg1 = gates_lib.cg1_evaluate_shard(shard_id, neg_correct, len(neg), pos_correct, len(pos), attempt)

    core_rows = None
    if cg1["passed"]:
        core_rows = [
            {
                "row_key": m["row_key"], "arm": m["arm"], "hs_index": m.get("hs_index"),
                "dose_multiplier": m.get("dose_multiplier"), "role": m.get("role"),
                "refused_final": v,
            }
            for m, v in pairs if not m["is_decoy"]
        ]

    return {"cg1": cg1, "core_rows": core_rows}


def applied_key(row_key: str, arm: str, hs_index: Any, dose_multiplier: Any) -> tuple:
    return (row_key, arm, hs_index, dose_multiplier)


def build_post_adjudication_table(family: str, applied_by_key: dict[tuple, bool]) -> dict[str, Any]:
    """Re-derives the per-rung table (same rung grouping as
    dose_ladder.py's `_rung_summary` / the committed
    `pre_adjudication_wide_vs_narrow_table.json`) with an added
    `wide_adjudicated` rate: detector_v2-refused OR the unblinded
    adjudicator verdict for rows that went through the pool. Rows with no
    adjudication verdict available (not yet graded, or excluded by a voided
    lane) keep their detector_v2 verdict only and are counted in
    `n_pending_adjudication` for that rung/population so a partial or voided
    run is visible rather than silently reported as complete."""
    pdir = ANALYSIS / family
    role_by_key = {r["row_key"]: r["role"] for r in dl.load_jsonl(pdir / "joined_rows_private.jsonl")}
    runlog_dir = pdir / "runlog"

    def unioned(raw: dict[str, Any], arm: str, hs_index: Any, dose_mult: Any) -> tuple[bool, bool]:
        """Returns (refused_union, pending)."""
        if bool(raw.get("refused_v2", False)):
            return True, False
        key = applied_key(raw["row_key"], arm, hs_index, dose_mult)
        if key in applied_by_key:
            return bool(applied_by_key[key]), False
        return False, True

    rungs: list[dict[str, Any]] = []
    for entry_path in sorted(runlog_dir.glob("hs*__*__dose*.jsonl")):
        stem = entry_path.stem
        parts = stem.split("__")
        if len(parts) != 3:
            continue
        layer = int(parts[0][2:])
        arm = parts[1]
        dose_mult = int(parts[2][4:])
        raw_rows = load_jsonl(entry_path)
        confab_raw = [r for r in raw_rows if r.get("role") == TRACKED_ROLES[0]]
        known_raw = [r for r in raw_rows if r.get("role") == TRACKED_ROLES[1]]

        def summarize(raws: list[dict[str, Any]]) -> dict[str, Any]:
            unions, pendings = [], 0
            for r in raws:
                u, p = unioned(r, arm, layer, dose_mult)
                unions.append({**r, "refused_wide_adjudicated": u})
                pendings += int(p)
            return {
                "refused_wide_adjudicated": gates_lib.rate_wilson(unions, "refused_wide_adjudicated"),
                "refused_wide_screen": gates_lib.rate_wilson(raws, "refused_v2"),
                "refused_narrow": gates_lib.rate_wilson(raws, "refused"),
                "n_pending_adjudication": pendings,
            }

        rungs.append({
            "layer": layer, "arm": arm, "dose_mult": dose_mult,
            "n_confab": len(confab_raw), "n_known": len(known_raw),
            "confab": summarize(confab_raw), "known": summarize(known_raw),
        })

    baseline_path = HERE / "analysis" / "staged_inputs" / family / "baseline_graded_private.jsonl"
    baseline_confab_wide = baseline_known_wide = None
    if baseline_path.is_file():
        baseline_wide = dl.load_baseline_wide_by_key(baseline_path)
        confab_rows = [v for k, v in baseline_wide.items() if role_by_key.get(k) == TRACKED_ROLES[0]]
        known_rows = [v for k, v in baseline_wide.items() if role_by_key.get(k) == TRACKED_ROLES[1]]

        def baseline_summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
            unions, pendings = [], 0
            for r in rows:
                u, p = unioned(r, "baseline", None, None)
                unions.append({**r, "refused_wide_adjudicated": u})
                pendings += int(p)
            return {
                "refused_wide_adjudicated": gates_lib.rate_wilson(unions, "refused_wide_adjudicated"),
                "refused_wide_screen": gates_lib.rate_wilson(rows, "refused_v2"),
                "refused_narrow": gates_lib.rate_wilson(rows, "refused"),
                "n_pending_adjudication": pendings,
            }

        baseline_confab_wide = baseline_summarize(confab_rows)
        baseline_known_wide = baseline_summarize(known_rows)

    for r in rungs:
        base = baseline_confab_wide["refused_wide_adjudicated"]["rate"] if baseline_confab_wide else None
        r["net_lift_over_paired_baseline_wide_adjudicated"] = (
            r["confab"]["refused_wide_adjudicated"]["rate"] - base if base is not None else None
        )

    return {
        "cell": CELL_ID,
        "status": "POST-ADJUDICATION -- refused_wide_adjudicated = detector_v2 screen OR unblinded adjudicator verdict; n_pending_adjudication counts rows with no verdict yet (not graded, or excluded by a voided lane).",
        "baseline": {"confab": baseline_confab_wide, "known_correct_answered": baseline_known_wide},
        "rungs": rungs,
    }


def cmd_apply(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    grading_manifest = json.loads(Path(args.grading_manifest).read_text(encoding="utf-8"))
    pool_manifest = load_pool_manifest(committed_dir)

    shard_results = {}
    for shard_id, entry in grading_manifest.items():
        shard_results[shard_id] = evaluate_shard(shard_id, entry, pool_manifest, analysis_dir, committed_dir)

    experiment_voided = any(r["cg1"]["status"] == "VOID_CELL_TERMINAL" for r in shard_results.values())

    pooled = gates_lib.cg1_pooled_clear_positive([r["cg1"] for r in shard_results.values()])

    applied_rows: list[dict[str, Any]] = []
    applied_by_key: dict[tuple, bool] = {}
    if not experiment_voided:
        for result in shard_results.values():
            if result["core_rows"] is None:
                continue
            for row in result["core_rows"]:
                applied_rows.append(row)
                applied_by_key[applied_key(row["row_key"], row["arm"], row["hs_index"], row["dose_multiplier"])] = row["refused_final"]

    write_jsonl(analysis_dir / "adjudication_applied.jsonl", applied_rows)

    applied_report = {
        "cell": CELL_ID,
        "shards": {sid: r["cg1"] for sid, r in shard_results.items()},
        "pooled_clear_positive": pooled,
        "experiment_voided": experiment_voided,
        "n_applied_rows": len(applied_rows),
    }
    write_json(committed_dir / "adjudication_applied_manifest.json", applied_report)

    post_table = build_post_adjudication_table(args.family, applied_by_key)
    write_json(committed_dir / args.family / "post_adjudication_wide_table.json", post_table)

    print(json.dumps(applied_report, indent=2, default=str), flush=True)
    print(f"[apply_adjudication] wrote post-adjudication table for {len(post_table['rungs'])} rungs "
          f"({'EXPERIMENT VOIDED -- no rows applied' if experiment_voided else f'{len(applied_rows)} core rows applied'}).", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_commit = sub.add_parser("commit-hash", help="commit a shard's graded-file sha256 BEFORE unblinding")
    p_commit.add_argument("--shard-id", required=True)
    p_commit.add_argument("--graded-file", required=True)
    p_commit.add_argument("--committed-dir", default=None)
    p_commit.set_defaults(func=cmd_commit_hash)

    p_apply = sub.add_parser("apply", help="verify committed hashes, then join + evaluate CG1 for every shard and rebuild the post-adjudication table")
    p_apply.add_argument("--grading-manifest", required=True, help='OPERATOR-AUTHORED JSON {shard_id: {"graded_file": path, "attempt": 1}} -- NOT adjudication_graded_manifest.json')
    p_apply.add_argument("--family", default="llama", choices=("llama",))
    p_apply.add_argument("--analysis-dir", default=None)
    p_apply.add_argument("--committed-dir", default=None)
    p_apply.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
