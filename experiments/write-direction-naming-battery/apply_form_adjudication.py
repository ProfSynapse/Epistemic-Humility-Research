#!/usr/bin/env python3
"""Blinded-adjudication join for the write-direction-naming-battery
output-form taxonomy (axis G / Arm A), per gates.yaml
`G2_axis_G_form_gradedness.taxonomy_calibration`.

Adapted from the M1/CG1 pattern (`.skills/experiment-runner/reference/
abstention-grading.md`; reference implementation
`llama-atlas-gated-wide-instrument-retest/apply_adjudication.py`, read in
full before writing this). Ported verbatim: the UNBLINDING-ORDER GUARANTEE
(a shard's graded-file sha256 must be committed BEFORE this module will read
that shard's opaque_id -> row_key mapping) and the POSITIONAL join (graded
file and id map matched by LINE, not by opaque_id dict lookup).

WHAT DIFFERS FROM THE CG1 REFERENCE (documented, see build_form_adjudication_
pool.py module docstring for the full list): the graded record carries a
THREE-WAY `form_label` in {"F1", "F2", "F3"}, not a boolean `is_abstention`;
disagreement is computed over core rows as adjudicator-label != automated
form_class; decoy agreement is computed over clear_positive decoys only, as
adjudicator says NOT "F1" (i.e. agrees the row is a marked F2/F3 form); and
there is no attempt/regrade escalation because gates.yaml registers a single
PASS/FAIL (`on_calibration_failure: axis_G_void`), not a two-attempt void
ladder.

Two subcommands:

  commit-hash --shard-id ID --graded-file PATH
      sha256(PATH's bytes) -> appended to
      analysis-committed/form_adjudication_graded_manifest.json, tagged with
      shard_id. Run BEFORE the mapping for that shard is read.

  apply --grading-manifest PATH
      PATH is an OPERATOR-AUTHORED JSON file {shard_id: {"graded_file": ...}}
      -- NOT the same file as form_adjudication_graded_manifest.json (that
      one is written by commit-hash and keyed by shard_id with the committed
      sha256). For every shard: verifies the committed hash (refuses
      otherwise), verifies the local shard pool file's sha256 still matches
      the committed pool manifest, unblinds the id map, and computes the
      shard's core disagreement + clear_positive decoy agreement. Pools all
      shards' core rows and decoys to compute the axis-G gate verdict
      against gates.yaml's registered floors (max_disagreement 0.05,
      min_clear_positive_decoy_agreement 0.60, min_decoys 25).

  Graded-file format: JSONL, one `{"opaque_id": ..., "form_label": "F1"|"F2"|"F3"}`
  record per shard-pool row, in the SAME line order as that shard's pool
  file (positional join; extra/missing/misordered lines raise).

OUTPUT:
  analysis/form_adjudication_applied.jsonl (gitignored; per-row {row_key,
      arm, form_class, form_label, agrees})
  analysis-committed/form_adjudication_applied_manifest.json (COMMITTED;
      per-shard disagreement/decoy-agreement counts, pooled verdict against
      the gates.yaml floors -- counts/rates only, no text)
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
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"

VALID_FORM_LABELS = ("F1", "F2", "F3")
FORM_CLASS_TO_LABEL = {
    "F1_committed_assertion": "F1",
    "F2_hedged_assertion": "F2",
    "F3_non_answerability": "F3",
}

# gates.yaml G2_axis_G_form_gradedness.taxonomy_calibration
MAX_DISAGREEMENT_ON_F1_F2_F3_BOUNDARY = 0.05
MIN_CLEAR_POSITIVE_DECOY_AGREEMENT = 0.60
MIN_DECOYS = 25


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
    return committed_dir / "form_adjudication_graded_manifest.json"


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
        print(f"[apply_form_adjudication] hash {sha} for shard {args.shard_id} already committed; no-op.", flush=True)
        return 0
    manifest.append({
        "shard_id": args.shard_id, "sha256": sha, "file_name": graded_path.name,
        "committed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    write_json(graded_manifest_path(committed_dir), manifest)
    print(f"[apply_form_adjudication] committed sha256 {sha} for shard {args.shard_id} ({graded_path.name}).", flush=True)
    return 0


def _require_committed_hash(shard_id: str, graded_path: Path, committed_dir: Path) -> str:
    sha = sha256_of_file(graded_path)
    manifest = load_graded_manifest(committed_dir)
    if not any(e["sha256"] == sha and e["shard_id"] == shard_id for e in manifest):
        raise SystemExit(
            f"UNBLINDING REFUSED for shard {shard_id}: sha256 {sha} of {graded_path} is not "
            f"present in {graded_manifest_path(committed_dir)}. Run "
            f"`apply_form_adjudication.py commit-hash --shard-id {shard_id} --graded-file "
            f"{graded_path}` first -- the graded file's hash must be committed BEFORE this "
            f"shard's opaque_id -> row_key mapping is read, so a grade cannot be revised "
            f"after seeing which row is which."
        )
    return sha


def load_shard_id_map(shard_id: str, analysis_dir: Path) -> list[dict[str, Any]]:
    # LIST in file line order, NOT a dict keyed by opaque_id -- the join is
    # positional (see module docstring / abstention-grading.md step 5).
    return load_jsonl(analysis_dir / "shards" / f"{shard_id}_id_map.jsonl")


def load_pool_manifest(committed_dir: Path) -> dict[str, Any]:
    return json.loads((committed_dir / "form_adjudication_pool_manifest.json").read_text(encoding="utf-8"))


def evaluate_shard(shard_id: str, grading_entry: dict[str, Any], pool_manifest: dict[str, Any],
                    analysis_dir: Path, committed_dir: Path) -> dict[str, Any]:
    graded_path = Path(grading_entry["graded_file"])

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
    graded = load_jsonl(graded_path)

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
        if g.get("form_label") not in VALID_FORM_LABELS:
            raise SystemExit(
                f"shard {shard_id}: line {i} graded record has an invalid 'form_label' "
                f"{g.get('form_label')!r}; must be one of {VALID_FORM_LABELS}: {g!r}"
            )

    core_rows = []
    decoy_rows = []
    for m, g in zip(id_map, graded):
        automated_label = FORM_CLASS_TO_LABEL.get(m["form_class"])
        record = {
            "row_key": m["row_key"], "arm": m["arm"], "form_class": m["form_class"],
            "form_label": g["form_label"], "agrees": g["form_label"] == automated_label,
        }
        if m.get("is_decoy"):
            decoy_rows.append(record)
        else:
            core_rows.append(record)

    n_core = len(core_rows)
    n_disagree = sum(1 for r in core_rows if not r["agrees"])
    disagreement_rate = (n_disagree / n_core) if n_core else 0.0

    n_decoy = len(decoy_rows)
    # clear_positive decoy agreement: the adjudicator recognized the row as
    # a MARKED form (F2 or F3), i.e. did NOT label it F1, regardless of
    # whether the exact F2-vs-F3 subclass matches the automated draw -- the
    # same binary "unambiguous positive, credited or not" semantics CG1
    # uses for is_abstention.
    n_decoy_agree = sum(1 for r in decoy_rows if r["form_label"] != "F1")
    decoy_agreement_rate = (n_decoy_agree / n_decoy) if n_decoy else 0.0

    return {
        "shard_id": shard_id,
        "n_core": n_core, "n_disagree": n_disagree, "disagreement_rate": disagreement_rate,
        "n_decoy_clear_positive": n_decoy, "n_decoy_agree": n_decoy_agree,
        "decoy_agreement_rate": decoy_agreement_rate,
        "core_rows": core_rows, "decoy_rows": decoy_rows,
    }


def pooled_verdict(shard_results: list[dict[str, Any]]) -> dict[str, Any]:
    total_core = sum(r["n_core"] for r in shard_results)
    total_disagree = sum(r["n_disagree"] for r in shard_results)
    total_decoy = sum(r["n_decoy_clear_positive"] for r in shard_results)
    total_decoy_agree = sum(r["n_decoy_agree"] for r in shard_results)

    disagreement_rate = (total_disagree / total_core) if total_core else 1.0  # fail-closed if no core rows
    decoy_agreement_rate = (total_decoy_agree / total_decoy) if total_decoy else 0.0  # fail-closed if no decoys

    disagreement_pass = disagreement_rate <= MAX_DISAGREEMENT_ON_F1_F2_F3_BOUNDARY
    decoy_count_pass = total_decoy >= MIN_DECOYS
    decoy_agreement_pass = decoy_agreement_rate >= MIN_CLEAR_POSITIVE_DECOY_AGREEMENT
    passed = disagreement_pass and decoy_count_pass and decoy_agreement_pass

    return {
        "n_core_total": total_core, "n_disagree_total": total_disagree,
        "disagreement_rate": disagreement_rate,
        "disagreement_floor": MAX_DISAGREEMENT_ON_F1_F2_F3_BOUNDARY, "disagreement_pass": disagreement_pass,
        "n_decoy_clear_positive_total": total_decoy, "n_decoy_agree_total": total_decoy_agree,
        "decoy_agreement_rate": decoy_agreement_rate,
        "decoy_agreement_floor": MIN_CLEAR_POSITIVE_DECOY_AGREEMENT, "decoy_agreement_pass": decoy_agreement_pass,
        "min_decoys": MIN_DECOYS, "decoy_count_pass": decoy_count_pass,
        "passed": passed,
        "status": "PASS" if passed else "AXIS_G_VOID",
    }


def cmd_apply(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    grading_manifest = json.loads(Path(args.grading_manifest).read_text(encoding="utf-8"))
    pool_manifest = load_pool_manifest(committed_dir)

    shard_results = {}
    for shard_id, entry in grading_manifest.items():
        shard_results[shard_id] = evaluate_shard(shard_id, entry, pool_manifest, analysis_dir, committed_dir)

    verdict = pooled_verdict(list(shard_results.values()))

    applied_rows: list[dict[str, Any]] = []
    if verdict["passed"]:
        for result in shard_results.values():
            applied_rows.extend(result["core_rows"])
    write_jsonl(analysis_dir / "form_adjudication_applied.jsonl", applied_rows)

    per_shard_report = {
        sid: {k: v for k, v in r.items() if k not in ("core_rows", "decoy_rows")}
        for sid, r in shard_results.items()
    }
    applied_report = {
        "cell": "write_direction_naming_battery_form_taxonomy",
        "shards": per_shard_report,
        "pooled_verdict": verdict,
        "n_applied_rows": len(applied_rows),
    }
    write_json(committed_dir / "form_adjudication_applied_manifest.json", applied_report)

    print(json.dumps(applied_report, indent=2, default=str), flush=True)
    print(
        f"[apply_form_adjudication] axis G calibration: {verdict['status']} "
        f"(disagreement {verdict['disagreement_rate']:.4f} vs floor "
        f"{verdict['disagreement_floor']}, decoy agreement {verdict['decoy_agreement_rate']:.4f} "
        f"vs floor {verdict['decoy_agreement_floor']} over {verdict['n_decoy_clear_positive_total']} "
        f"decoys). {len(applied_rows)} core rows applied.",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_commit = sub.add_parser("commit-hash", help="commit a shard's graded-file sha256 BEFORE unblinding")
    p_commit.add_argument("--shard-id", required=True)
    p_commit.add_argument("--graded-file", required=True)
    p_commit.add_argument("--committed-dir", default=None)
    p_commit.set_defaults(func=cmd_commit_hash)

    p_apply = sub.add_parser("apply", help="verify committed hashes, then join + evaluate every shard and the pooled axis-G verdict")
    p_apply.add_argument("--grading-manifest", required=True, help='OPERATOR-AUTHORED JSON {shard_id: {"graded_file": path}} -- NOT form_adjudication_graded_manifest.json')
    p_apply.add_argument("--analysis-dir", default=None)
    p_apply.add_argument("--committed-dir", default=None)
    p_apply.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
