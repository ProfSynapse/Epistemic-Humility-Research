#!/usr/bin/env python3
"""Blinded-adjudication join for idk-switch-naming-confirmatory.

Thin port of `form-judge-axis-g-rescore/apply_judge_grades.py` (source sha256
2c116e498e76f6530506f27c8034e0ab62b491472061099194e9463d457f712d, matching
that file's own pin; read in full before writing this), restricted per the
harness-build assignment to what THIS cell registers:

  - Only ONE grading role for the real payload: "judge" (AMENDMENT.md
    "Instruments": "one context-free opus-subagent judge per shard"). There
    is no "adjudicator" role here -- form-judge already earned construct
    validity; this cell only checks in-run decoy agreement against the
    judge, per AMENDMENT.md "Judge-lane in-run validity is gated by
    clear-positive decoys".
  - Decoys are NOT a separate calibration pool -- they are embedded inside
    the SAME full-pool shards as the real core rows (see
    build_judge_pool.py). `apply-full-pool` therefore does double duty in
    this cell: it both (a) unblinds and writes the {row_key, arm, form_label}
    payload for `axis_n1n2n3_arithmetic.py`, core rows only, AND (b)
    computes the in-run clear-positive decoy agreement rate from the SAME
    single grading pass -- one dispatch per shard, not a separate
    calibration dispatch.
  - A second role, "stability", exists ONLY for AMENDMENT.md's "One
    stability regrade shard, reported non-gating": one shard's pool is
    graded a second time by a fresh judge instance, and `apply-stability`
    reports the per-row label-flip rate between the two gradings. This
    number is NEVER gating and is never mixed into the N1/N2/N3 payload.

The UNBLINDING-ORDER GUARANTEE (a shard's graded-file sha256 must be
committed BEFORE this module will read that shard's opaque_id -> row_key
mapping) and the POSITIONAL join (graded file and id map matched by LINE, not
by opaque_id dict lookup) are both ported unchanged.

Two subcommands:

  commit-hash --shard-id ID --graded-file PATH --role judge|stability
      sha256(PATH's bytes) -> appended to analysis/graded_manifest.json
      (TODO post-sign: move to analysis-committed/), tagged with shard_id
      and role. Run BEFORE that shard+role's mapping is read.

  apply-full-pool --grading-manifest PATH
      PATH is an OPERATOR-AUTHORED JSON {shard_id: {"graded_file": path}}
      for the judge's full-pool grading (role "judge" only). Verifies
      committed hashes, joins, splits core (payload) rows from
      clear_positive decoy rows, computes in-run decoy agreement, and
      writes {row_key, arm, form_label} core rows -- the axis-N1/N2/N3
      payload.

  apply-stability --shard-id ID --primary-grading-manifest PATH --regrade-grading-manifest PATH
      Both PATHs are operator-authored JSON {shard_id: {"graded_file": path}}
      covering exactly the ONE registered stability shard, roles "judge" and
      "stability" respectively. Reports the per-row label-flip rate,
      non-gating.

  Graded-file format (all subcommands): JSONL, one
  `{"opaque_id": ..., "form_label": "F1"|"F2"|"F3"}` record per shard-pool
  row, in the SAME line order as that shard's pool file (positional join).

OUTPUT:
  analysis/isnc_full_pool_applied.jsonl (gitignored; per-row detail, core +
      decoy rows both present, `is_decoy`/`decoy_type` fields intact)
  analysis/isnc_full_pool_applied_manifest.json (TODO post-sign:
      analysis-committed/; per-shard row counts + pooled decoy agreement)
  analysis/isnc_axis_payload.jsonl (gitignored; core rows only --
      {row_key, arm, form_label} -- what axis_n1n2n3_arithmetic.py consumes)
  analysis/isnc_stability_report.json (TODO post-sign: analysis-committed/;
      per-row flip detail + pooled flip rate, non-gating)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"

VALID_FORM_LABELS = ("F1", "F2", "F3")
VALID_ROLES = ("judge", "stability")


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


def graded_manifest_path(analysis_dir: Path) -> Path:
    return analysis_dir / "graded_manifest.json"


def load_graded_manifest(analysis_dir: Path) -> list[dict[str, Any]]:
    path = graded_manifest_path(analysis_dir)
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_commit_hash(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    graded_path = Path(args.graded_file)
    if not graded_path.is_file():
        raise SystemExit(f"graded file not found: {graded_path}")
    if args.role not in VALID_ROLES:
        raise SystemExit(f"--role must be one of {VALID_ROLES}, got {args.role!r}")
    sha = sha256_of_file(graded_path)
    manifest = load_graded_manifest(analysis_dir)
    if any(e["sha256"] == sha and e["shard_id"] == args.shard_id and e["role"] == args.role for e in manifest):
        print(f"[apply_judge_grades] hash {sha} for shard {args.shard_id} role {args.role} already committed; no-op.", flush=True)
        return 0
    manifest.append({
        "shard_id": args.shard_id, "role": args.role, "sha256": sha, "file_name": graded_path.name,
        "committed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    write_json(graded_manifest_path(analysis_dir), manifest)
    print(f"[apply_judge_grades] committed sha256 {sha} for shard {args.shard_id} role {args.role} ({graded_path.name}).", flush=True)
    return 0


def _require_committed_hash(shard_id: str, role: str, graded_path: Path, analysis_dir: Path) -> str:
    sha = sha256_of_file(graded_path)
    manifest = load_graded_manifest(analysis_dir)
    if not any(e["sha256"] == sha and e["shard_id"] == shard_id and e["role"] == role for e in manifest):
        raise SystemExit(
            f"UNBLINDING REFUSED for shard {shard_id} role {role}: sha256 {sha} of {graded_path} "
            f"is not present in {graded_manifest_path(analysis_dir)}. Run `apply_judge_grades.py "
            f"commit-hash --shard-id {shard_id} --role {role} --graded-file {graded_path}` first -- "
            f"the graded file's hash must be committed BEFORE this shard's opaque_id -> row_key "
            f"mapping is read, so a grade cannot be revised after seeing which row is which."
        )
    return sha


def load_shard_id_map(shard_id: str, analysis_dir: Path) -> list[dict[str, Any]]:
    # LIST in file line order, NOT a dict keyed by opaque_id -- positional join.
    return load_jsonl(analysis_dir / "shards" / f"{shard_id}_id_map.jsonl")


def load_pool_manifest(analysis_dir: Path) -> dict[str, Any]:
    return json.loads((analysis_dir / "full_pool_manifest.json").read_text(encoding="utf-8"))


def _verify_pool_integrity(shard_id: str, pool_manifest: dict[str, Any], analysis_dir: Path) -> None:
    shard_manifest = next((s for s in pool_manifest["shards"] if s["shard_id"] == shard_id), None)
    if shard_manifest is None:
        raise SystemExit(f"shard {shard_id} not found in committed pool manifest")
    pool_path = analysis_dir / "shards" / f"{shard_id}.jsonl"
    if pool_path.is_file():
        actual_sha = sha256_of_file(pool_path)
        if actual_sha != shard_manifest["pool_sha256"]:
            raise SystemExit(
                f"pool integrity FAIL for {shard_id}: {pool_path} sha256 {actual_sha} does not "
                f"match committed manifest's {shard_manifest['pool_sha256']}."
            )


def _load_and_validate_graded(shard_id: str, role: str, graded_path: Path, id_map: list[dict[str, Any]], analysis_dir: Path) -> list[dict[str, Any]]:
    _require_committed_hash(shard_id, role, graded_path, analysis_dir)
    graded = load_jsonl(graded_path)
    if len(graded) != len(id_map):
        raise SystemExit(
            f"shard {shard_id} role {role}: graded file has {len(graded)} lines but id map has "
            f"{len(id_map)}; the join is positional and requires exact line alignment."
        )
    for i, (g, m) in enumerate(zip(graded, id_map)):
        if g.get("opaque_id") != m.get("opaque_id"):
            raise SystemExit(
                f"shard {shard_id} role {role}: line {i} opaque_id mismatch between graded file "
                f"and id map ({g.get('opaque_id')!r} != {m.get('opaque_id')!r}); the positional "
                f"join requires line-for-line id equality."
            )
        if g.get("form_label") not in VALID_FORM_LABELS:
            raise SystemExit(
                f"shard {shard_id} role {role}: line {i} graded record has an invalid "
                f"'form_label' {g.get('form_label')!r}; must be one of {VALID_FORM_LABELS}: {g!r}"
            )
    return graded


# ---------------------------------------------------------------------------
# apply-full-pool: unblind, split core vs decoy, compute in-run decoy agreement
# ---------------------------------------------------------------------------

def evaluate_full_pool_shard(shard_id: str, judge_entry: dict[str, Any], pool_manifest: dict[str, Any], analysis_dir: Path) -> dict[str, Any]:
    _verify_pool_integrity(shard_id, pool_manifest, analysis_dir)
    id_map = load_shard_id_map(shard_id, analysis_dir)
    judge_graded = _load_and_validate_graded(shard_id, "judge", Path(judge_entry["graded_file"]), id_map, analysis_dir)

    core_rows, decoy_pos_rows = [], []
    for m, jg in zip(id_map, judge_graded):
        label = jg["form_label"]
        record = {"row_key": m["row_key"], "arm": m["arm"], "form_label": label}
        if not m.get("is_decoy"):
            core_rows.append(record)
        elif m.get("decoy_type") == "clear_positive":
            decoy_pos_rows.append({**record, "judge_agrees_decoy": label != "F1"})

    n_pos = len(decoy_pos_rows)
    n_pos_agree = sum(1 for r in decoy_pos_rows if r["judge_agrees_decoy"])
    return {
        "shard_id": shard_id,
        "n_core": len(core_rows),
        "n_decoy_clear_positive": n_pos, "n_decoy_clear_positive_agree": n_pos_agree,
        "decoy_clear_positive_agreement_rate": (n_pos_agree / n_pos) if n_pos else 0.0,
        "core_rows": core_rows, "decoy_pos_rows": decoy_pos_rows,
    }


def pooled_full_pool_verdict(shard_results: list[dict[str, Any]]) -> dict[str, Any]:
    total_core = sum(r["n_core"] for r in shard_results)
    total_pos = sum(r["n_decoy_clear_positive"] for r in shard_results)
    total_pos_agree = sum(r["n_decoy_clear_positive_agree"] for r in shard_results)
    return {
        "n_core_total": total_core,
        "n_decoy_clear_positive_total": total_pos, "n_decoy_clear_positive_agree_total": total_pos_agree,
        "decoy_clear_positive_agreement_rate": (total_pos_agree / total_pos) if total_pos else 0.0,
        # NOTE: no PASS/FAIL here -- cell.yaml judge_lane floors
        # (n_decoys_clear_positive / min_clear_positive_agreement) are still
        # REGISTERED_AT_SIGN placeholders; the lead adjudicates against them
        # once pinned, per the binding invariant that this build must not
        # set gate numbers.
    }


def cmd_apply_full_pool(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    judge_manifest = json.loads(Path(args.grading_manifest).read_text(encoding="utf-8"))
    pool_manifest = load_pool_manifest(analysis_dir)

    shard_results = {}
    for shard_id in judge_manifest:
        shard_results[shard_id] = evaluate_full_pool_shard(shard_id, judge_manifest[shard_id], pool_manifest, analysis_dir)

    verdict = pooled_full_pool_verdict(list(shard_results.values()))

    applied_rows: list[dict[str, Any]] = []
    payload_rows: list[dict[str, Any]] = []
    for result in shard_results.values():
        applied_rows.extend(result["core_rows"])
        applied_rows.extend(result["decoy_pos_rows"])
        payload_rows.extend(result["core_rows"])
    write_jsonl(analysis_dir / "isnc_full_pool_applied.jsonl", applied_rows)
    write_jsonl(analysis_dir / "isnc_axis_payload.jsonl", payload_rows)

    per_shard_report = {sid: {k: v for k, v in r.items() if k not in ("core_rows", "decoy_pos_rows")} for sid, r in shard_results.items()}
    report = {
        "cell": "idk_switch_naming_confirmatory", "mode": "full-pool",
        "shards": per_shard_report, "pooled": verdict,
        "n_core_rows_applied": len(payload_rows),
    }
    write_json(analysis_dir / "isnc_full_pool_applied_manifest.json", report)
    print(json.dumps(report, indent=2, default=str), flush=True)
    print(
        f"[apply_judge_grades] full-pool: {len(payload_rows)} core (payload) rows; "
        f"in-run clear_positive decoy agreement {verdict['decoy_clear_positive_agreement_rate']:.4f} "
        f"over {verdict['n_decoy_clear_positive_total']}. Gate PASS/FAIL not evaluated "
        f"(cell.yaml judge_lane floors are REGISTERED_AT_SIGN).",
        flush=True,
    )
    return 0


# ---------------------------------------------------------------------------
# apply-stability: one shard, two gradings, per-row flip rate (non-gating)
# ---------------------------------------------------------------------------

def cmd_apply_stability(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    primary_manifest = json.loads(Path(args.primary_grading_manifest).read_text(encoding="utf-8"))
    regrade_manifest = json.loads(Path(args.regrade_grading_manifest).read_text(encoding="utf-8"))
    if set(primary_manifest) != {args.shard_id} or set(regrade_manifest) != {args.shard_id}:
        raise SystemExit(
            f"AMENDMENT.md registers exactly ONE stability regrade shard; both manifests "
            f"must cover exactly {{{args.shard_id!r}}}, got primary={sorted(primary_manifest)} "
            f"regrade={sorted(regrade_manifest)}"
        )
    pool_manifest = load_pool_manifest(analysis_dir)
    _verify_pool_integrity(args.shard_id, pool_manifest, analysis_dir)
    id_map = load_shard_id_map(args.shard_id, analysis_dir)

    primary_graded = _load_and_validate_graded(args.shard_id, "judge", Path(primary_manifest[args.shard_id]["graded_file"]), id_map, analysis_dir)
    regrade_graded = _load_and_validate_graded(args.shard_id, "stability", Path(regrade_manifest[args.shard_id]["graded_file"]), id_map, analysis_dir)

    rows = []
    n_flip = 0
    for m, p, r in zip(id_map, primary_graded, regrade_graded):
        flipped = p["form_label"] != r["form_label"]
        n_flip += int(flipped)
        rows.append({
            "row_key": m["row_key"], "arm": m["arm"], "is_decoy": m.get("is_decoy", False),
            "primary_label": p["form_label"], "regrade_label": r["form_label"], "flipped": flipped,
        })

    report = {
        "cell": "idk_switch_naming_confirmatory", "shard_id": args.shard_id,
        "n_rows": len(rows), "n_flip": n_flip,
        "flip_rate": (n_flip / len(rows)) if rows else 0.0,
        "non_gating": True,   # AMENDMENT.md: "reported non-gating"
        "rows": rows,
    }
    write_json(analysis_dir / "isnc_stability_report.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2, default=str), flush=True)
    print(f"[apply_judge_grades] stability (non-gating): {n_flip}/{len(rows)} = {report['flip_rate']:.4f} flip rate on shard {args.shard_id}.", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_commit = sub.add_parser("commit-hash", help="commit a shard+role's graded-file sha256 BEFORE unblinding")
    p_commit.add_argument("--shard-id", required=True)
    p_commit.add_argument("--role", required=True, choices=VALID_ROLES)
    p_commit.add_argument("--graded-file", required=True)
    p_commit.add_argument("--analysis-dir", default=None)
    p_commit.set_defaults(func=cmd_commit_hash)

    p_full = sub.add_parser("apply-full-pool", help="verify committed hashes, join judge grading, split core vs decoy, write payload rows")
    p_full.add_argument("--grading-manifest", required=True, help='operator-authored JSON {shard_id: {"graded_file": path}}, role judge')
    p_full.add_argument("--analysis-dir", default=None)
    p_full.set_defaults(func=cmd_apply_full_pool)

    p_stab = sub.add_parser("apply-stability", help="verify committed hashes, join two gradings of the ONE registered stability shard, report flip rate")
    p_stab.add_argument("--shard-id", required=True)
    p_stab.add_argument("--primary-grading-manifest", required=True, help='operator-authored JSON {shard_id: {"graded_file": path}}, role judge')
    p_stab.add_argument("--regrade-grading-manifest", required=True, help='operator-authored JSON {shard_id: {"graded_file": path}}, role stability')
    p_stab.add_argument("--analysis-dir", default=None)
    p_stab.set_defaults(func=cmd_apply_stability)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
