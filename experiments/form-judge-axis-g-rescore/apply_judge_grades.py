#!/usr/bin/env python3
"""Blinded-adjudication join for form-judge-axis-g-rescore.

Ports `apply_form_adjudication.py` (read in full before writing this;
itself the naming battery's own port of `.skills/experiment-runner/
reference/abstention-grading.md`'s CG1 pattern). Ported verbatim: the
UNBLINDING-ORDER GUARANTEE (a shard's graded-file sha256 must be committed
BEFORE this module will read that shard's opaque_id -> row_key mapping) and
the POSITIONAL join (graded file and id map matched by LINE, not by
opaque_id dict lookup).

WHAT DIFFERS FROM THE NAMING-BATTERY REFERENCE (documented):

  - `form_label` is graded by TWO independent roles during calibration,
    "judge" and "adjudicator" (AMENDMENT.md: "the calibration adjudicator is
    a second independent model agent"), not one grader against an automated
    `form_class`. `commit-hash` therefore takes `--role judge|adjudicator`
    and tags each committed hash with its role, so a shard's judge hash and
    adjudicator hash are tracked separately and both must be committed
    before that shard unblinds.
  - Calibration disagreement (G1) is JUDGE label vs ADJUDICATOR label on
    core rows (there is no automated F1/F2/F3 classifier any more -- that
    instrument was voided; see AMENDMENT.md "Motivation and posture").
  - Two decoy types (G2): clear_positive (agreement = judge says NOT "F1")
    and clear_negative (agreement = judge says "F1"), computed against the
    JUDGE's grading -- the judge is the instrument under validation; the
    adjudicator's role is the core-agreement calibration partner, not a
    second instrument the decoy floors gate. FLAGGED DESIGN CHOICE (not
    stated explicitly in AMENDMENT.md "Gates"): the adjudicator's own decoy
    performance is computed and reported for both roles when both are
    present, for transparency, but only the judge's decoy rates are the
    registered G2 numbers.
  - The ordered-label-pair disagreement-direction breakdown (per
    AMENDMENT.md item 1 / gates.yaml-to-be, and the standing rule in
    abstention-grading.md "Register the disagreement-direction analysis")
    is computed over core rows as Counter[(judge_label, adjudicator_label)].
  - A separate `apply-full-pool` subcommand handles the payload phase: one
    grading role (the judge), no adjudicator, no decoy math -- it only
    unblinds and writes {row_key, arm, form_label} rows for
    `axis_g_arithmetic.py` to consume. This subcommand does not check any
    gate; the payload only runs after `apply-calibration` reports PASS
    (that authorization check lives with the operator/lead, not in code
    here, since gates.yaml floors are not registered on this draft cell).

Three subcommands:

  commit-hash --shard-id ID --graded-file PATH --role judge|adjudicator
      sha256(PATH's bytes) -> appended to
      analysis/graded_manifest.json (TODO post-sign: move to
      analysis-committed/), tagged with shard_id and role. Run BEFORE that
      shard+role's mapping is read.

  apply-calibration --judge-grading-manifest PATH --adjudicator-grading-manifest PATH
      Both PATHs are OPERATOR-AUTHORED JSON files {shard_id: {"graded_file":
      path}} -- NOT the same file as graded_manifest.json (that one is
      written by commit-hash). For every shard: verifies both committed
      hashes (refuses otherwise), verifies the local shard pool file's
      sha256 still matches the committed pool manifest, unblinds the id
      map, computes core disagreement (judge vs adjudicator), decoy
      agreement (both types, judge-scored), and the disagreement-direction
      breakdown. Pools all shards for the pooled verdict numbers (gates.yaml
      floors are read if present; this cell's gates.yaml is still the
      unsigned placeholder, so `apply-calibration` reports the raw rates and
      leaves PASS/FAIL adjudication to gates.yaml once it is signed).

  apply-full-pool --grading-manifest PATH
      PATH is an operator-authored JSON {shard_id: {"graded_file": path}}
      for the judge's full-pool grading. Verifies committed hashes, joins,
      and writes {row_key, arm, form_label} rows -- no gate evaluation.

  Graded-file format (both subcommands): JSONL, one
  `{"opaque_id": ..., "form_label": "F1"|"F2"|"F3"}` record per shard-pool
  row, in the SAME line order as that shard's pool file (positional join;
  extra/missing/misordered lines raise).

OUTPUT:
  analysis/form_judge_calibration_applied.jsonl (gitignored; per-row detail)
  analysis/form_judge_calibration_applied_manifest.json (TODO post-sign:
      analysis-committed/; per-shard rates, pooled numbers, direction
      breakdown -- counts/rates only, no text)
  analysis/form_judge_full_pool_applied.jsonl (gitignored; per-row
      {row_key, arm, form_label} -- this is the axis-G rescore payload)
  analysis/form_judge_full_pool_applied_manifest.json (TODO post-sign:
      analysis-committed/; per-shard row counts only)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
SHARDS_DIR = ANALYSIS / "shards"

VALID_FORM_LABELS = ("F1", "F2", "F3")
VALID_ROLES = ("judge", "adjudicator")


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
    # TODO(post-sign): move to analysis-committed/graded_manifest.json.
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


def load_pool_manifest(analysis_dir: Path, mode: str) -> dict[str, Any]:
    name = "calibration_pool_manifest.json" if mode == "calibration" else "full_pool_manifest.json"
    return json.loads((analysis_dir / name).read_text(encoding="utf-8"))


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
# apply-calibration
# ---------------------------------------------------------------------------

def evaluate_calibration_shard(
    shard_id: str, judge_entry: dict[str, Any], adjudicator_entry: dict[str, Any],
    pool_manifest: dict[str, Any], analysis_dir: Path,
) -> dict[str, Any]:
    _verify_pool_integrity(shard_id, pool_manifest, analysis_dir)
    id_map = load_shard_id_map(shard_id, analysis_dir)

    judge_graded = _load_and_validate_graded(shard_id, "judge", Path(judge_entry["graded_file"]), id_map, analysis_dir)
    adjudicator_graded = _load_and_validate_graded(shard_id, "adjudicator", Path(adjudicator_entry["graded_file"]), id_map, analysis_dir)

    core_rows, decoy_pos_rows, decoy_neg_rows = [], [], []
    direction_counts: Counter[tuple[str, str]] = Counter()

    for m, jg, ag in zip(id_map, judge_graded, adjudicator_graded):
        judge_label, adj_label = jg["form_label"], ag["form_label"]
        record = {
            "row_key": m["row_key"], "arm": m["arm"],
            "judge_label": judge_label, "adjudicator_label": adj_label,
            "agrees": judge_label == adj_label,
        }
        if not m.get("is_decoy"):
            core_rows.append(record)
            direction_counts[(judge_label, adj_label)] += 1
        elif m.get("decoy_type") == "clear_positive":
            decoy_pos_rows.append({**record, "judge_agrees_decoy": judge_label != "F1"})
        elif m.get("decoy_type") == "clear_negative":
            decoy_neg_rows.append({**record, "judge_agrees_decoy": judge_label == "F1"})

    n_core = len(core_rows)
    n_disagree = sum(1 for r in core_rows if not r["agrees"])
    n_pos = len(decoy_pos_rows)
    n_pos_agree = sum(1 for r in decoy_pos_rows if r["judge_agrees_decoy"])
    n_neg = len(decoy_neg_rows)
    n_neg_agree = sum(1 for r in decoy_neg_rows if r["judge_agrees_decoy"])

    return {
        "shard_id": shard_id,
        "n_core": n_core, "n_disagree": n_disagree,
        "disagreement_rate": (n_disagree / n_core) if n_core else 0.0,
        "n_decoy_clear_positive": n_pos, "n_decoy_clear_positive_agree": n_pos_agree,
        "decoy_clear_positive_agreement_rate": (n_pos_agree / n_pos) if n_pos else 0.0,
        "n_decoy_clear_negative": n_neg, "n_decoy_clear_negative_agree": n_neg_agree,
        "decoy_clear_negative_agreement_rate": (n_neg_agree / n_neg) if n_neg else 0.0,
        "direction_counts": {f"{j}->{a}": c for (j, a), c in direction_counts.items()},
        "core_rows": core_rows, "decoy_pos_rows": decoy_pos_rows, "decoy_neg_rows": decoy_neg_rows,
    }


def pooled_calibration_verdict(shard_results: list[dict[str, Any]]) -> dict[str, Any]:
    total_core = sum(r["n_core"] for r in shard_results)
    total_disagree = sum(r["n_disagree"] for r in shard_results)
    total_pos = sum(r["n_decoy_clear_positive"] for r in shard_results)
    total_pos_agree = sum(r["n_decoy_clear_positive_agree"] for r in shard_results)
    total_neg = sum(r["n_decoy_clear_negative"] for r in shard_results)
    total_neg_agree = sum(r["n_decoy_clear_negative_agree"] for r in shard_results)

    pooled_direction: Counter[str] = Counter()
    for r in shard_results:
        pooled_direction.update(r["direction_counts"])

    return {
        "n_core_total": total_core, "n_disagree_total": total_disagree,
        "disagreement_rate": (total_disagree / total_core) if total_core else 1.0,  # fail-closed
        "n_decoy_clear_positive_total": total_pos, "n_decoy_clear_positive_agree_total": total_pos_agree,
        "decoy_clear_positive_agreement_rate": (total_pos_agree / total_pos) if total_pos else 0.0,
        "n_decoy_clear_negative_total": total_neg, "n_decoy_clear_negative_agree_total": total_neg_agree,
        "decoy_clear_negative_agreement_rate": (total_neg_agree / total_neg) if total_neg else 0.0,
        "direction_counts_pooled": dict(pooled_direction),
        # NOTE: no PASS/FAIL here -- gates.yaml G1/G2 floors are not yet
        # registered on this draft cell (lead sets them at sign, per the
        # binding invariant that this build must not touch gate numbers).
    }


def cmd_apply_calibration(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    judge_manifest = json.loads(Path(args.judge_grading_manifest).read_text(encoding="utf-8"))
    adjudicator_manifest = json.loads(Path(args.adjudicator_grading_manifest).read_text(encoding="utf-8"))
    if set(judge_manifest) != set(adjudicator_manifest):
        raise SystemExit(
            f"judge and adjudicator grading manifests cover different shard sets: "
            f"judge={sorted(judge_manifest)} adjudicator={sorted(adjudicator_manifest)}"
        )
    pool_manifest = load_pool_manifest(analysis_dir, "calibration")

    shard_results = {}
    for shard_id in judge_manifest:
        shard_results[shard_id] = evaluate_calibration_shard(
            shard_id, judge_manifest[shard_id], adjudicator_manifest[shard_id], pool_manifest, analysis_dir,
        )

    verdict = pooled_calibration_verdict(list(shard_results.values()))

    applied_rows: list[dict[str, Any]] = []
    for result in shard_results.values():
        applied_rows.extend(result["core_rows"])
    write_jsonl(analysis_dir / "form_judge_calibration_applied.jsonl", applied_rows)

    per_shard_report = {
        sid: {k: v for k, v in r.items() if k not in ("core_rows", "decoy_pos_rows", "decoy_neg_rows")}
        for sid, r in shard_results.items()
    }
    report = {
        "cell": "form_judge_axis_g_rescore", "mode": "calibration",
        "shards": per_shard_report, "pooled": verdict, "n_core_rows_applied": len(applied_rows),
    }
    write_json(analysis_dir / "form_judge_calibration_applied_manifest.json", report)
    print(json.dumps(report, indent=2, default=str), flush=True)
    print(
        f"[apply_judge_grades] calibration: disagreement {verdict['disagreement_rate']:.4f} over "
        f"{verdict['n_core_total']} core rows; clear_positive decoy agreement "
        f"{verdict['decoy_clear_positive_agreement_rate']:.4f} over {verdict['n_decoy_clear_positive_total']}; "
        f"clear_negative decoy agreement {verdict['decoy_clear_negative_agreement_rate']:.4f} over "
        f"{verdict['n_decoy_clear_negative_total']}. Gate PASS/FAIL not evaluated (gates.yaml unsigned).",
        flush=True,
    )
    return 0


# ---------------------------------------------------------------------------
# apply-full-pool
# ---------------------------------------------------------------------------

def cmd_apply_full_pool(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    grading_manifest = json.loads(Path(args.grading_manifest).read_text(encoding="utf-8"))
    pool_manifest = load_pool_manifest(analysis_dir, "full-pool")

    applied_rows: list[dict[str, Any]] = []
    per_shard_report: dict[str, Any] = {}
    for shard_id, entry in grading_manifest.items():
        _verify_pool_integrity(shard_id, pool_manifest, analysis_dir)
        id_map = load_shard_id_map(shard_id, analysis_dir)
        graded = _load_and_validate_graded(shard_id, "judge", Path(entry["graded_file"]), id_map, analysis_dir)
        rows = [{"row_key": m["row_key"], "arm": m["arm"], "form_label": g["form_label"]} for m, g in zip(id_map, graded)]
        applied_rows.extend(rows)
        per_shard_report[shard_id] = {"n_rows": len(rows)}

    write_jsonl(analysis_dir / "form_judge_full_pool_applied.jsonl", applied_rows)
    report = {
        "cell": "form_judge_axis_g_rescore", "mode": "full-pool",
        "shards": per_shard_report, "n_rows_applied": len(applied_rows),
    }
    write_json(analysis_dir / "form_judge_full_pool_applied_manifest.json", report)
    print(json.dumps(report, indent=2, default=str), flush=True)
    print(f"[apply_judge_grades] full-pool: {len(applied_rows)} rows applied.", flush=True)
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

    p_calib = sub.add_parser("apply-calibration", help="verify committed hashes, join judge+adjudicator, compute calibration numbers")
    p_calib.add_argument("--judge-grading-manifest", required=True, help='operator-authored JSON {shard_id: {"graded_file": path}}')
    p_calib.add_argument("--adjudicator-grading-manifest", required=True, help='operator-authored JSON {shard_id: {"graded_file": path}}')
    p_calib.add_argument("--analysis-dir", default=None)
    p_calib.set_defaults(func=cmd_apply_calibration)

    p_full = sub.add_parser("apply-full-pool", help="verify committed hashes, join judge grading, write payload rows")
    p_full.add_argument("--grading-manifest", required=True, help='operator-authored JSON {shard_id: {"graded_file": path}}')
    p_full.add_argument("--analysis-dir", default=None)
    p_full.set_defaults(func=cmd_apply_full_pool)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
