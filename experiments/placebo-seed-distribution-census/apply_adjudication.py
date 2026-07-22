#!/usr/bin/env python3
"""Blinded-adjudication join for placebo-seed-distribution-census.

Ported from `rr3-corrected-placebo-replication/apply_adjudication.py` (read
in full before writing this; that module's docstring explains the mechanism
in depth, including the `--grading-manifest` operator-authored-dict format
gotcha documented in `.skills/experiment-runner/reference/
abstention-grading.md` "Operator gotcha"). Enforces the same UNBLINDING-ORDER
GUARANTEE per shard: a shard's graded-file sha256 must be committed BEFORE
this module will read that shard's opaque_id -> row_key mapping. The join is
POSITIONAL (graded file and id map matched by LINE, not by opaque_id
lookup).

Two subcommands:

  commit-hash --shard-id ID --graded-file PATH
      sha256(PATH's bytes) -> appended to
      analysis-committed/adjudication_graded_manifest.json, tagged with
      shard_id. Run BEFORE the mapping for that shard is read.

  apply --grading-manifest PATH
      PATH is an OPERATOR-AUTHORED JSON file {shard_id: {"graded_file": ...,
      "attempt": 1|2}} -- NOT the hash-commitment manifest `commit-hash`
      writes; the operator authors this file by hand after grading. For
      every shard: verifies the committed hash (refuses otherwise), verifies
      the local shard pool file's sha256 still matches the committed pool
      manifest, unblinds the id map, computes PER-SHARD CG1
      (gates_lib.cg1_evaluate_shard), then computes the POOLED clear-positive
      floor (gates_lib.cg1_pooled_clear_positive) across every shard that
      reached a PASS-or-attempt-1 result.

OUTPUT: analysis/adjudication_applied.jsonl (gitignored; per-row {cell, arm,
row_key, seed, refused_final}) and analysis-committed/
adjudication_applied_manifest.json (COMMITTED; per-shard CG1 results +
pooled CG1 result + voided_cells list + counts only, no row_key/text).
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402
import gates_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def graded_manifest_path(committed_dir: Path) -> Path:
    return committed_dir / "adjudication_graded_manifest.json"


def load_graded_manifest(committed_dir: Path) -> list[dict[str, Any]]:
    path = graded_manifest_path(committed_dir)
    if not path.is_file():
        return []
    return common.load_json(path)


def cmd_commit_hash(args: argparse.Namespace) -> int:
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    graded_path = Path(args.graded_file)
    if not graded_path.is_file():
        raise SystemExit(f"graded file not found: {graded_path}")
    sha = common.sha256_of_file(graded_path)
    manifest = load_graded_manifest(committed_dir)
    if any(e["sha256"] == sha and e["shard_id"] == args.shard_id for e in manifest):
        print(f"[apply_adjudication] hash {sha} for shard {args.shard_id} already committed; no-op.", flush=True)
        return 0
    manifest.append({
        "shard_id": args.shard_id, "sha256": sha, "file_name": graded_path.name,
        "committed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    common.write_json(graded_manifest_path(committed_dir), manifest)
    print(f"[apply_adjudication] committed sha256 {sha} for shard {args.shard_id} ({graded_path.name}).", flush=True)
    return 0


def _require_committed_hash(shard_id: str, graded_path: Path, committed_dir: Path) -> str:
    sha = common.sha256_of_file(graded_path)
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
    return common.load_jsonl(analysis_dir / "shards" / f"{shard_id}_id_map.jsonl")


def load_pool_manifest(committed_dir: Path) -> dict[str, Any]:
    return common.load_json(committed_dir / "pool_manifest.json")


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
        actual_sha = common.sha256_of_file(pool_path)
        if actual_sha != shard_manifest["pool_sha256"]:
            raise SystemExit(
                f"pool integrity FAIL for {shard_id}: {pool_path} sha256 {actual_sha} "
                f"does not match committed manifest's {shard_manifest['pool_sha256']}."
            )

    id_map = load_shard_id_map(shard_id, analysis_dir)
    graded = common.load_jsonl(graded_path)

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
                "source": m.get("source"), "seed": m.get("seed"), "refused_final": v,
            }
            for m, v in pairs if not m["is_decoy"]
        ]

    return {"cell": shard_manifest["cell"], "cg1": cg1, "core_rows": core_rows}


def cmd_apply(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    grading_manifest = common.load_json(Path(args.grading_manifest))
    pool_manifest = load_pool_manifest(committed_dir)

    shard_results = {}
    for shard_id, entry in grading_manifest.items():
        shard_results[shard_id] = evaluate_shard(shard_id, entry, pool_manifest, analysis_dir, committed_dir)

    voided_cells = {r["cell"] for r in shard_results.values() if r["cg1"]["status"] == "VOID_CELL_TERMINAL"}

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

    common.write_jsonl(analysis_dir / "adjudication_applied.jsonl", applied_rows)

    report = {
        "shards": {sid: {"cell": r["cell"], "cg1": r["cg1"]} for sid, r in shard_results.items()},
        "pooled_clear_positive": pooled,
        "pooled_failure_cells": sorted(pooled_failure_cells),
        "voided_cells": sorted(voided_cells),
        "n_applied_rows": len(applied_rows),
    }
    common.write_json(committed_dir / "adjudication_applied_manifest.json", report)
    print(report, flush=True)
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
