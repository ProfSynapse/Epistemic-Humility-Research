#!/usr/bin/env python3
"""SC0 (provenance and staging) stage-in for margin-separation-fine-ladder
(M1b).

CPU-only, no model, no GPU. Adapted (logic ported) from
`margin-mapping/staging.py` (read in full before writing this), with ONE
deliberate change per this task's binding invariants: sources are COPIED
(never symlinked) into this experiment's own gitignored
`analysis/staged_inputs/qwen35_4b/...` -- M1 itself symlinked; M1b copies.

Every one of the 7 pinned inputs in `config.PINNED_INPUTS` is verified by
sha256 against the LITERAL digest transcribed in `config.py` (which cites,
for each entry, either the exact cell.yaml line it was restated from, or --
for `c_hat_direction` and `question_pool`, both flagged `cell_yaml_pin:
False` -- the M1-precedent staging_manifest.json entry it was transcribed
from). A mismatch on ANY entry is a hard SystemExit, never a warning.

`question_pool` in particular is NOT named anywhere in cell.yaml/
experiment.yaml (see config.py's docstring for the full ambiguity note):
generation needs the actual question TEXT keyed by row_key to render any
prompt at all, and M1's own staging.py established the precedent of staging
this as a build necessity without a spec-level pin. This build follows that
precedent and FLAGS it in the harness-build report rather than silently
treating it as fully spec-covered.

Then derives the 53-row refined subset from the staged margin_dataset
(cell.yaml `population.refined_subset.rule`: confab role, tipping_idx == 5,
partitioned on tipping_censored FIRST per cell.yaml's explicit warning
against a bare `tipping_idx >= 6` comparison), asserts the full partition
against the pre-committed 181/53/166 counts (Decision record item 2), and
writes the OPAQUE row_key list (no question/answer text) to
`analysis-committed/refined_subset_ids_qwen35_4b.json` -- committed BEFORE
any new generation (gates.yaml SC0_provenance_staging).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
ANALYSIS = EXPERIMENT_DIR / "analysis"
STAGED = ANALYSIS / "staged_inputs"
COMMITTED = EXPERIMENT_DIR / "analysis-committed"

sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

DETECTOR_STACK_FILES = ("detector_v2.py", "detector_v2_patterns.yaml", "grader.py")
M1_HARNESS_DIR = config.M1_DIR / "harness"


def stage_input(name: str, entry: dict[str, Any]) -> dict[str, Any]:
    src: Path = Path(entry["path"])
    if not src.is_file():
        raise SystemExit(f"SC0 FAILED: missing source file for {name!r}: {src}")
    sha = common.sha256_of_file(src)
    if sha != entry["sha256"]:
        raise SystemExit(
            f"SC0 FAILED: {name!r} sha256 {sha} does NOT match the pinned "
            f"digest {entry['sha256']} in config.PINNED_INPUTS. Do not proceed."
        )
    dest = STAGED / entry["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        dest.unlink()
    shutil.copy2(src, dest)  # LOCAL COPY, never a symlink (binding invariant)
    dest_sha = common.sha256_of_file(dest)
    if dest_sha != sha:
        raise SystemExit(f"SC0 FAILED: copied file {dest} sha256 {dest_sha} != source sha256 {sha}.")
    return {
        "name": name, "source_path": str(src), "dest_path": str(dest.relative_to(EXPERIMENT_DIR)),
        "sha256": sha, "cell_yaml_pin": bool(entry.get("cell_yaml_pin")),
    }


def verify_detector_stack_byte_identical() -> dict[str, Any]:
    """Live check that the detector-stack CODE files copied into this
    harness/ at build time are still byte-identical to M1's own copies
    (which are the byte-identical pins cell.yaml's `readout.primary` field
    cites: "detector_v2 (byte-identical pins from the M1/factorial
    stack)")."""
    results = {}
    all_pass = True
    for fname in DETECTOR_STACK_FILES:
        mine = HERE / fname
        theirs = M1_HARNESS_DIR / fname
        if not mine.is_file():
            raise SystemExit(f"SC0 FAILED: detector-stack file missing in this harness: {mine}")
        if not theirs.is_file():
            raise SystemExit(f"SC0 FAILED: M1 detector-stack source missing: {theirs}")
        sha_mine = common.sha256_of_file(mine)
        sha_theirs = common.sha256_of_file(theirs)
        passed = sha_mine == sha_theirs
        all_pass = all_pass and passed
        results[fname] = {"sha256_mine": sha_mine, "sha256_m1": sha_theirs, "byte_identical": passed}
    if not all_pass:
        raise SystemExit(f"SC0 FAILED: detector stack is NOT byte-identical to M1's copies: {results}")
    return {"pass": all_pass, "files": results}


def _partition_bucket(row: dict[str, Any]) -> str:
    """cell.yaml `population.merge_rule`: "partition on tipping_censored
    FIRST, then on the integer index, never on a bare tipping_idx >= 6
    comparison" (censored rows carry tipping_idx null)."""
    if row.get("tipping_censored"):
        return "idx_ge_6_or_censored"
    idx = row["tipping_idx"]
    if idx <= config.M1_TIPPING_IDX_LE:
        return "idx_le_4"
    if idx == config.REFINED_SUBSET_TIPPING_IDX:
        return "idx_5_refined"
    if idx >= config.M1_TIPPING_IDX_GE:
        return "idx_ge_6_or_censored"
    raise SystemExit(f"SC0 FAILED: row_key {row['row_key']!r} has tipping_idx={idx!r}, uncovered by the partition rule.")


def derive_refined_subset(margin_dataset_staged_path: Path) -> dict[str, Any]:
    rows = common.load_jsonl(margin_dataset_staged_path)
    confab_rows = [r for r in rows if r.get("role") == "confab"]
    if len(confab_rows) != config.EXPECTED_CONFAB_TOTAL:
        raise SystemExit(
            f"SC0 FAILED: staged margin_dataset has {len(confab_rows)} confab rows, "
            f"expected {config.EXPECTED_CONFAB_TOTAL}."
        )

    buckets: dict[str, list[str]] = {"idx_le_4": [], "idx_5_refined": [], "idx_ge_6_or_censored": []}
    for r in confab_rows:
        buckets[_partition_bucket(r)].append(r["row_key"])

    counts = {k: len(v) for k, v in buckets.items()}
    if counts != config.EXPECTED_PARTITION:
        raise SystemExit(
            f"SC0 FAILED: refined-subset partition counts {counts} do not match "
            f"the pre-committed distribution {config.EXPECTED_PARTITION} (Decision "
            f"record item 2). Do not proceed -- this is a hard pre-registered assertion."
        )

    refined_ids = sorted(buckets["idx_5_refined"])
    return {
        "counts": counts,
        "refined_row_keys": refined_ids,
        "n_confab_total": len(confab_rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    pin_check = config.verify_pinned_hashes()
    if not all(pin_check.values()):
        raise SystemExit(f"SC0 FAILED: cell.yaml/gates.yaml pin mismatch: {pin_check}")
    print(f"[staging] cell.yaml/gates.yaml pins verified: {pin_check}", flush=True)

    records = [stage_input(name, entry) for name, entry in config.PINNED_INPUTS.items()]

    manifest = {
        "n_files": len(records),
        "n_cell_yaml_pinned": sum(1 for r in records if r["cell_yaml_pin"]),
        "n_convention_carried_not_cell_yaml_pinned": sum(1 for r in records if not r["cell_yaml_pin"]),
        "files": records,
    }
    common.write_json(COMMITTED / "staging_manifest.json", manifest)

    for r in records:
        flag = "CELL.YAML PIN" if r["cell_yaml_pin"] else "CONVENTION (not a cell.yaml pin; see config.py docstring)"
        print(f"  COPIED {r['name']:20s} sha256={r['sha256'][:10]} [{flag}]", flush=True)

    detector_check = verify_detector_stack_byte_identical()
    print(f"[staging] detector stack byte-identical to M1: {detector_check['pass']}", flush=True)

    margin_dataset_staged = STAGED / config.PINNED_INPUTS["margin_dataset"]["dest"]
    partition = derive_refined_subset(margin_dataset_staged)
    print(f"[staging] refined-subset partition: {partition['counts']} (expected {config.EXPECTED_PARTITION}) -- MATCH", flush=True)

    refined_payload = {
        "family": "qwen35_4b",
        "rule": (
            "confab rows with M1 tipping_idx == 5 (tipped exactly at the 0.75x "
            "rung, bracket (0.5x, 0.75x]); partitioned on tipping_censored FIRST"
        ),
        "source_margin_dataset_sha256": config.PINNED_INPUTS["margin_dataset"]["sha256"],
        "n_confab_total": partition["n_confab_total"],
        "partition_counts": partition["counts"],
        "expected_partition_counts": config.EXPECTED_PARTITION,
        "partition_counts_match_expected": partition["counts"] == config.EXPECTED_PARTITION,
        "n_refined": len(partition["refined_row_keys"]),
        "row_keys": partition["refined_row_keys"],
    }
    if refined_payload["n_refined"] != config.REFINED_SUBSET_N:
        raise SystemExit(
            f"SC0 FAILED: derived refined subset has {refined_payload['n_refined']} rows, "
            f"cell.yaml registers {config.REFINED_SUBSET_N}."
        )
    common.write_json(COMMITTED / "refined_subset_ids_qwen35_4b.json", refined_payload)
    print(
        f"[staging] refined_subset_ids_qwen35_4b.json committed: "
        f"n={refined_payload['n_refined']} first3={refined_payload['row_keys'][:3]}",
        flush=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
