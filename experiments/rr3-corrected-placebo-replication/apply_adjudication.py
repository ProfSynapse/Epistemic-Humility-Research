#!/usr/bin/env python3
"""Blinded-adjudication join for rr3-corrected-placebo-replication.

Adapted from `abstention-wide-instrument-calibration/apply_adjudication.py`
(read in full before writing this) for RR3's cell set (core_mistral,
rider_mistral, rider_llama) and EXTENDED with the POOLED clear-positive CG1
floor (AMENDMENT.md "Successor instrument fix (b)"; gates.yaml
`clear_positive_agreement_min_pooled`) alongside the per-shard floor the
calibration already had. Enforces the same UNBLINDING-ORDER GUARANTEE per
shard: a shard's graded-file sha256 must be committed BEFORE this module
will read that shard's opaque_id -> row_key mapping. The join is POSITIONAL
(graded file and id map matched by LINE, not by opaque_id lookup), for the
same reason the calibration adopted it: this experiment's opaque ids are
NOT unique keys across the whole pool by themselves if two shards happened
to share a salt (they never do here -- see build_adjudication_pool.py -- but
the positional join is the invariant that makes that non-issue verifiable
rather than assumed).

Two subcommands:

  commit-hash --shard-id ID --graded-file PATH
      sha256(PATH's bytes) -> appended to
      analysis-committed/adjudication_graded_manifest.json, tagged with
      shard_id. Run BEFORE the mapping for that shard is read.

  apply --grading-manifest PATH
      PATH is a JSON file {shard_id: {"graded_file": ..., "attempt": 1|2}}.
      For every shard: verifies the committed hash (refuses otherwise),
      verifies the local shard pool file's sha256 still matches the
      committed pool manifest, unblinds the id map, computes PER-SHARD CG1
      (gates_lib.cg1_evaluate_shard), then -- once every shard's per-shard
      result is known -- computes the POOLED clear-positive floor
      (gates_lib.cg1_pooled_clear_positive) across every shard that reached
      a PASS-or-attempt-1 result (a shard already terminally voided
      contributes no pooled-floor evidence). A shard is:
        PASS               -> core (non-decoy) rows get refused_final = the
                               adjudicator's boolean.
        VOID_REGRADE_ONCE  -> this shard's grades are discarded; NOT a cell
                               void yet.
        VOID_CELL_TERMINAL -> this shard's grades are discarded AND its cell
                               is added to `voided_cells`; every shard
                               belonging to a voided cell (including ones
                               that individually passed) is excluded from
                               the final join, per gates.yaml
                               `on_second_failure: void_cell_report_straight`.
      If the POOLED floor fails even though every individual shard's
      per-shard floor passed, this is reported as a POOLED failure and the
      affected cells are treated identically to a per-shard
      VOID_CELL_TERMINAL (the registered pooled floor is a promotion-relevant
      integrity gate, not advisory).

  Graded-file format: JSONL, one `{"opaque_id": ..., "is_abstention": bool}`
  record per shard-pool row, in the SAME line order as that shard's pool
  file (positional join; extra/missing/misordered lines raise).

OUTPUT: analysis/adjudication_applied.jsonl (gitignored; per-row {cell, arm,
row_key, seed, dose_multiplier, refused_final}) and
analysis-committed/adjudication_applied_manifest.json (COMMITTED; per-shard
CG1 results + pooled CG1 result + voided_cells list + counts only, no
row_key/text).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import gates_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"


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
    import datetime
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
    # LIST in file line order, NOT a dict keyed by opaque_id -- the positional
    # join is required (see module docstring); a dict would silently collapse
    # any accidental id collision instead of raising.
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
        if g["opaque_id"] != m["opaque_id"]:
            raise SystemExit(
                f"shard {shard_id}: line {i} opaque_id mismatch between graded file "
                f"and id map; the positional join requires line-for-line id equality."
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
                "cell": m["cell"], "arm": m["arm"], "row_key": m["row_key"], "role": m.get("role"),
                "source": m.get("source"), "seed": m.get("seed"), "dose_multiplier": m.get("dose_multiplier"),
                "refused_final": v,
            }
            for m, v in pairs if not m["is_decoy"]
        ]

    return {"cell": shard_manifest["cell"], "cg1": cg1, "core_rows": core_rows}


def cmd_apply(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    grading_manifest = json.loads(Path(args.grading_manifest).read_text(encoding="utf-8"))
    pool_manifest = load_pool_manifest(committed_dir)

    shard_results = {}
    for shard_id, entry in grading_manifest.items():
        shard_results[shard_id] = evaluate_shard(shard_id, entry, pool_manifest, analysis_dir, committed_dir)

    voided_cells = {r["cell"] for r in shard_results.values() if r["cg1"]["status"] == "VOID_CELL_TERMINAL"}

    # Pooled clear-positive floor (successor fix (b)): evaluated across every
    # shard whose per-shard CG1 result is available (PASS or a still-live
    # attempt-1 VOID_REGRADE_ONCE contributes its decoy counts too -- the
    # pooled floor is about decoy-draw variance across the whole grading
    # effort, not only the shards that individually passed).
    pooled = gates_lib.cg1_pooled_clear_positive([r["cg1"] for r in shard_results.values()])
    pooled_failure_cells: set[str] = set()
    if not pooled["passed"]:
        pooled_failure_cells = {r["cell"] for r in shard_results.values()}
        voided_cells |= pooled_failure_cells

    applied_rows: list[dict[str, Any]] = []
    for shard_id, result in shard_results.items():
        if result["cell"] in voided_cells:
            continue
        if result["core_rows"] is not None:
            applied_rows.extend(result["core_rows"])

    write_jsonl(analysis_dir / "adjudication_applied.jsonl", applied_rows)

    report = {
        "shards": {sid: {"cell": r["cell"], "cg1": r["cg1"]} for sid, r in shard_results.items()},
        "pooled_clear_positive": pooled,
        "pooled_failure_cells": sorted(pooled_failure_cells),
        "voided_cells": sorted(voided_cells),
        "n_applied_rows": len(applied_rows),
    }
    write_json(committed_dir / "adjudication_applied_manifest.json", report)
    print(json.dumps(report, indent=2), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_commit = sub.add_parser("commit-hash", help="commit a shard's graded-file sha256 BEFORE unblinding")
    p_commit.add_argument("--shard-id", required=True)
    p_commit.add_argument("--graded-file", required=True)
    p_commit.add_argument("--committed-dir", default=None)
    p_commit.set_defaults(func=cmd_commit_hash)

    p_apply = sub.add_parser("apply", help="verify committed hashes, then join + evaluate CG1 (per-shard AND pooled) for every shard")
    p_apply.add_argument("--grading-manifest", required=True, help='JSON {shard_id: {"graded_file": path, "attempt": 1}}')
    p_apply.add_argument("--analysis-dir", default=None)
    p_apply.add_argument("--committed-dir", default=None)
    p_apply.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
