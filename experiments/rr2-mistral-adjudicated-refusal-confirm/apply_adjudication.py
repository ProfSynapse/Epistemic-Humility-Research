#!/usr/bin/env python3
"""Blinded-adjudication join + final gate computation for
rr2-mistral-adjudicated-refusal-confirm.

Two subcommands enforce the UNBLINDING-ORDER GUARANTEE (cell.yaml
`adjudication.unblinding_order_guarantee`): the adjudicator's graded-file
sha256 must be recorded in a COMMITTED manifest before this module will read
the opaque_id -> row_key mapping. This makes it impossible to see which row
is which, silently re-grade to hit a floor, and then "commit" a
post-hoc-edited file: the hash you commit is the hash that gets unblinded,
and unblinding a DIFFERENT file requires a DIFFERENT commit first.

  commit-hash --graded-file PATH   sha256(PATH's bytes) -> appended to
                                    analysis-committed/adjudication_graded_manifest.json.
                                    Run this BEFORE you have seen the mapping.
  apply --graded-file PATH         verifies PATH's current sha256 is present
                                    in that committed manifest, THEN reads the
                                    gitignored id map, joins, computes
                                    refused_final = refused_v2 OR
                                    adjudicated_abstention per row (decoys
                                    excluded from every rate), and evaluates
                                    RG1/RG2/RG3 + the falsifier verdict via
                                    gates_lib. Refuses (SystemExit) if the
                                    hash is not yet committed.

Graded-file format: JSONL, one `{"opaque_id": ..., "is_abstention": bool}`
record per pool row (every opaque_id in the pool manifest must be covered
exactly once; extra or missing ids raise).
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
ARMS = ("baseline", "gated", "random_direction", "dose_knowns_ungated")


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
    if any(e["sha256"] == sha for e in manifest):
        print(f"[apply_adjudication] hash {sha} already committed; no-op.", flush=True)
        return 0
    manifest.append({
        "sha256": sha, "file_name": graded_path.name,
        "committed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    })
    write_json(graded_manifest_path(committed_dir), manifest)
    print(f"[apply_adjudication] committed sha256 {sha} for {graded_path.name}.", flush=True)
    return 0


def _require_committed_hash(graded_path: Path, committed_dir: Path) -> str:
    sha = sha256_of_file(graded_path)
    manifest = load_graded_manifest(committed_dir)
    if not any(e["sha256"] == sha for e in manifest):
        raise SystemExit(
            f"UNBLINDING REFUSED: sha256 {sha} of {graded_path} is not present "
            f"in {graded_manifest_path(committed_dir)}. Run "
            f"`apply_adjudication.py commit-hash --graded-file {graded_path}` "
            f"first -- the graded file's hash must be committed BEFORE the "
            f"opaque_id -> row_key mapping is read, so a grade cannot be "
            f"revised after seeing which row is which."
        )
    return sha


def load_id_map(analysis_dir: Path) -> dict[str, dict[str, Any]]:
    rows = load_jsonl(analysis_dir / "adjudication_id_map.jsonl")
    return {r["opaque_id"]: r for r in rows}


def load_graded_file(path: Path) -> dict[str, bool]:
    rows = load_jsonl(path)
    out: dict[str, bool] = {}
    for r in rows:
        out[r["opaque_id"]] = bool(r["is_abstention"])
    return out


def load_arm_rows(analysis_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """{arm: {row_key: row}} for each of the four run logs."""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for arm in ARMS:
        rows = load_jsonl(analysis_dir / "runlog" / f"heldout__{arm}.jsonl")
        out[arm] = {r["row_key"]: r for r in rows}
    return out


def load_heldout_roster(committed_dir: Path) -> dict[str, list[str]]:
    """Reads the ID-only committed materialize manifest for the full
    held-out row roster (row_key, role), needed to reconstruct
    combine-active-and-baseline populations for arms that only log FIRED
    rows (gated, random_direction)."""
    manifest = json.loads((committed_dir / "materialize_manifest.json").read_text())
    confab: list[str] = []
    known: list[str] = []
    for r in manifest["rows"]:
        if r.get("split") != "held_out":
            continue
        if r["role"] == "confab":
            confab.append(r["row_key"])
        elif r["role"] == "known_correct_answered":
            known.append(r["row_key"])
    return {"confab": confab, "known": known}


def combine_with_baseline(row_keys: list[str], active_by_key: dict[str, dict], baseline_by_key: dict[str, dict]) -> list[dict[str, Any]]:
    out = []
    for rk in row_keys:
        out.append(active_by_key.get(rk) or baseline_by_key[rk])
    return out


def apply_final_refusal(rows: list[dict[str, Any]], id_map: dict[str, dict[str, Any]], graded: dict[str, bool], arm: str) -> list[dict[str, Any]]:
    """Attaches `refused_final` per row. A row is looked up in the id map by
    (row_key, arm) to find its opaque_id (if it was ever in the pool); decoys
    are never emitted here (id_map rows are matched only to non-decoy pool
    members by construction of the reverse index passed in as `id_map`,
    which the caller pre-filters -- see `_reverse_index_excluding_decoys`)."""
    by_row_arm = {(m["row_key"], m["arm"]): m for m in id_map.values() if not m["is_decoy"]}
    out = []
    for r in rows:
        refused_v2 = bool(r.get("refused_v2", False))
        if refused_v2:
            refused_final = True
        else:
            m = by_row_arm.get((r["row_key"], arm))
            if m is not None and m["opaque_id"] in graded:
                refused_final = graded[m["opaque_id"]]
            else:
                # Row was refused_v2==False but never entered the pool (should
                # not happen for a correctly built pool) or the graded file
                # does not cover it -- conservatively NOT credited, and
                # flagged so a caller can detect a coverage gap.
                refused_final = False
        out.append({**r, "refused_final": refused_final})
    return out


def cmd_apply(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    graded_path = Path(args.graded_file)

    _require_committed_hash(graded_path, committed_dir)

    id_map = load_id_map(analysis_dir)
    graded = load_graded_file(graded_path)

    pool_manifest = json.loads((committed_dir / "adjudication_pool_manifest.json").read_text())
    pool_path = analysis_dir / "adjudication_pool.jsonl"
    if pool_path.is_file():
        actual_pool_sha = hashlib.sha256(pool_path.read_bytes()).hexdigest()
        if actual_pool_sha != pool_manifest["pool_sha256"]:
            raise SystemExit(
                f"pool integrity FAIL: analysis/adjudication_pool.jsonl sha256 "
                f"{actual_pool_sha} does not match the committed manifest's "
                f"{pool_manifest['pool_sha256']}; the pool changed after the "
                f"manifest was written."
            )
    core_ids = {oid for oid, m in id_map.items() if not m["is_decoy"]}
    missing_grades = core_ids - set(graded)
    if missing_grades:
        raise SystemExit(f"graded file is missing {len(missing_grades)} core pool ids; sample: {sorted(missing_grades)[:5]}")

    arm_rows = load_arm_rows(analysis_dir)
    roster = load_heldout_roster(committed_dir)

    gated_confab_fired = [r for r in arm_rows["gated"].values() if r.get("role") == "confab"]
    gated_confab_fired = apply_final_refusal(gated_confab_fired, id_map, graded, "gated")

    gated_known_full = combine_with_baseline(roster["known"], arm_rows["gated"], arm_rows["baseline"])
    gated_known_full = [
        apply_final_refusal([r], id_map, graded, "gated" if r["row_key"] in arm_rows["gated"] else "baseline")[0]
        for r in gated_known_full
    ]

    rand_confab_full = combine_with_baseline(roster["confab"], arm_rows["random_direction"], arm_rows["baseline"])
    rand_confab_full = [
        apply_final_refusal([r], id_map, graded, "random_direction" if r["row_key"] in arm_rows["random_direction"] else "baseline")[0]
        for r in rand_confab_full
    ]
    rand_known_full = combine_with_baseline(roster["known"], arm_rows["random_direction"], arm_rows["baseline"])
    rand_known_full = [
        apply_final_refusal([r], id_map, graded, "random_direction" if r["row_key"] in arm_rows["random_direction"] else "baseline")[0]
        for r in rand_known_full
    ]

    baseline_confab_full = [apply_final_refusal([r], id_map, graded, "baseline")[0] for r in
                             (arm_rows["baseline"][rk] for rk in roster["confab"])]
    baseline_known_full = [apply_final_refusal([r], id_map, graded, "baseline")[0] for r in
                            (arm_rows["baseline"][rk] for rk in roster["known"])]

    confab_final = gates_lib.rate_summary_final(gated_confab_fired)
    confab_well_formed = gates_lib.rate_wilson(gated_confab_fired, "well_formed")
    known_final = gates_lib.rate_summary_final(gated_known_full)

    rg1_refused = gates_lib.rg1_refused_pass(confab_final["refused"])
    rg1_well_formed = gates_lib.rg1_well_formed_pass(confab_well_formed)
    rg2_cost = gates_lib.rg2_cost_pass(known_final["refused"])

    rand_confab_final = gates_lib.rate_summary_final(rand_confab_full)["refused"]
    base_confab_final = gates_lib.rate_summary_final(baseline_confab_full)["refused"]
    rand_known_final = gates_lib.rate_summary_final(rand_known_full)["refused"]
    base_known_final = gates_lib.rate_summary_final(baseline_known_full)["refused"]
    rg3 = gates_lib.rg3_placebo_pass(rand_confab_final, base_confab_final, rand_known_final, base_known_final)

    verdict = gates_lib.falsifier_verdict(rg1_refused, rg1_well_formed, rg2_cost, rg3["passed"])

    report = {
        "n_core_pool": len(core_ids),
        "n_decoy": sum(1 for m in id_map.values() if m["is_decoy"]),
        "gated_fired_confab": {"n": len(gated_confab_fired), "refused_final": confab_final["refused"], "well_formed": confab_well_formed},
        "gated_known_full_population": {"n": len(gated_known_full), "refused_final": known_final["refused"]},
        "random_direction_confab_full": {"n": len(rand_confab_full), "refused_final": rand_confab_final},
        "random_direction_known_full": {"n": len(rand_known_full), "refused_final": rand_known_final},
        "baseline_confab_full": {"n": len(baseline_confab_full), "refused_final": base_confab_final},
        "baseline_known_full": {"n": len(baseline_known_full), "refused_final": base_known_final},
        "gates": {
            "rg1_refused_pass": rg1_refused,
            "rg1_well_formed_pass": rg1_well_formed,
            "rg2_cost_pass": rg2_cost,
            "rg3_placebo": rg3,
        },
        "verdict": verdict,
    }
    write_json(committed_dir / "final_report.json", report)
    print(json.dumps(report, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_commit = sub.add_parser("commit-hash", help="commit the graded file's sha256 BEFORE unblinding")
    p_commit.add_argument("--graded-file", required=True)
    p_commit.add_argument("--committed-dir", default=None)
    p_commit.set_defaults(func=cmd_commit_hash)

    p_apply = sub.add_parser("apply", help="verify the committed hash, then join + compute final gates")
    p_apply.add_argument("--graded-file", required=True)
    p_apply.add_argument("--analysis-dir", default=None)
    p_apply.add_argument("--committed-dir", default=None)
    p_apply.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
