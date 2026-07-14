#!/usr/bin/env python3
"""Blinded-adjudication join for abstention-wide-instrument-calibration.

Adapted from rr2-mistral-adjudicated-refusal-confirm/apply_adjudication.py
for the SHARDED, CELL-SCOPED, multi-cell pool `build_adjudication_pool.py`
builds. Enforces the same UNBLINDING-ORDER GUARANTEE per shard (cell.yaml
`adjudication.unblinding_order_guarantee`, ported): a shard's graded-file
sha256 must be committed BEFORE this module will read that shard's
opaque_id -> row_key mapping.

Two subcommands:

  commit-hash --shard-id ID --graded-file PATH
      sha256(PATH's bytes) -> appended to
      analysis-committed/adjudication_graded_manifest.json, tagged with
      shard_id. Run BEFORE the mapping for that shard is read.

  apply --grading-manifest PATH
      PATH is a JSON file {shard_id: {"graded_file": ..., "attempt": 1|2}}.
      For every shard: verifies the committed hash (refuses otherwise),
      verifies the local shard pool file's sha256 still matches the
      committed pool manifest, unblinds the id map, computes CG1 decoy
      calibration (gates_lib.cg1_evaluate_shard), and either:
        PASS               -> core (non-decoy) rows get refused_final =
                               the adjudicator's boolean (all core pool
                               rows entered the pool BECAUSE detector_v2
                               marked them non-refused, so no OR is needed
                               here; the OR happens in calibration_scorer.py
                               against rows that never entered the pool at
                               all because detector_v2 already marked them
                               refused).
        VOID_REGRADE_ONCE  -> this shard's grades are discarded (not
                               applied); NOT a cell void yet.
        VOID_CELL_TERMINAL -> this shard's grades are discarded AND the
                               shard's cell is added to `voided_cells`;
                               every shard belonging to a voided cell
                               (including ones that individually passed
                               CG1) is excluded from the final join, per
                               gates.yaml `on_second_failure:
                               void_cell_report_straight` -- the registered
                               unit of the second-failure void is the CELL,
                               not the shard.

  Graded-file format: JSONL, one `{"opaque_id": ..., "is_abstention": bool}`
  record per shard-pool row (every opaque_id in that shard's pool manifest
  entry must be covered exactly once; extra or missing ids raise).

OUTPUT: analysis/adjudication_applied.jsonl (gitignored; per-row
{cell, row_key, arm, refused_final}) and
analysis-committed/adjudication_applied_manifest.json (COMMITTED; per-shard
CG1 results + voided_cells list + counts only, no row_key/text).
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


def load_shard_id_map(shard_id: str, analysis_dir: Path) -> dict[str, dict[str, Any]]:
    rows = load_jsonl(analysis_dir / "shards" / f"{shard_id}_id_map.jsonl")
    return {r["opaque_id"]: r for r in rows}


def load_graded_file(path: Path) -> dict[str, bool]:
    rows = load_jsonl(path)
    out: dict[str, bool] = {}
    for r in rows:
        out[r["opaque_id"]] = bool(r["is_abstention"])
    return out


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

    core_ids = {oid for oid, m in id_map.items() if not m["is_decoy"]}
    missing = core_ids - set(graded)
    if missing:
        raise SystemExit(f"shard {shard_id}: graded file missing {len(missing)} core ids; sample: {sorted(missing)[:5]}")

    neg_ids = [oid for oid, m in id_map.items() if m.get("decoy_type") == "clear_negative"]
    pos_ids = [oid for oid, m in id_map.items() if m.get("decoy_type") == "clear_positive"]
    neg_correct = sum(1 for oid in neg_ids if oid in graded and graded[oid] is False)
    pos_correct = sum(1 for oid in pos_ids if oid in graded and graded[oid] is True)

    cg1 = gates_lib.cg1_evaluate_shard(shard_id, neg_correct, len(neg_ids), pos_correct, len(pos_ids), attempt)

    core_rows = None
    if cg1["passed"]:
        core_rows = [
            {"cell": m["cell"], "row_key": m["row_key"], "arm": m["arm"], "refused_final": graded[oid]}
            for oid, m in id_map.items() if not m["is_decoy"]
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

    applied_rows: list[dict[str, Any]] = []
    for shard_id, result in shard_results.items():
        if result["cell"] in voided_cells:
            continue
        if result["core_rows"] is not None:
            applied_rows.extend(result["core_rows"])

    write_jsonl(analysis_dir / "adjudication_applied.jsonl", applied_rows)

    report = {
        "shards": {
            sid: {"cell": r["cell"], "cg1": r["cg1"]} for sid, r in shard_results.items()
        },
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

    p_apply = sub.add_parser("apply", help="verify committed hashes, then join + evaluate CG1 for every shard")
    p_apply.add_argument("--grading-manifest", required=True, help='JSON {shard_id: {"graded_file": path, "attempt": 1}}')
    p_apply.add_argument("--analysis-dir", default=None)
    p_apply.add_argument("--committed-dir", default=None)
    p_apply.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
