#!/usr/bin/env python3
"""SC0 (provenance and staging) stage-in for margin-evidence-responsiveness-
worldknown (M4-WK).

CPU-only, no model, no GPU. Per the task directive: every reused artifact is
staged as a LOCAL COPY under this experiment's own gitignored
`analysis/staged_inputs/` (never a symlink, never a cross-worktree link),
verified byte-identical (sha256) against its pin, before staging into
`analysis/staged_inputs/`.

Staged inputs:
  - the TRANSFER c_hat direction (cell.yaml `directions.transfer`, sha256
    pinned 937d1bff...)
  - the detector stack (detector_v2.py, detector_v2_patterns.yaml,
    grader.py) -- these were copied byte-identically into this harness/
    directory at build time FROM `margin-mapping/harness/` (verified `cp` +
    sha256sum at copy time, recorded in NOTEBOOK/build history).
    `verify_detector_stack_byte_identical()` re-checks this live against
    that SAME direct source (the M1 harness this experiment's own detector
    stack was copied from), mirroring M1's own `verify_detector_stack_byte_
    identical()` (which checked against the factorial's copies) -- cell.yaml
    does not restate a separate numeric sha256 pin for these three files
    beyond "byte-identical" (build-time interpretation, documented here per
    this repo's convention for such gaps).
  - PopQA test.jsonl (no prior sha256 pin exists for this source -- it is
    the experiment's OWN fresh population source, not a reused prior
    artifact -- so this step RECORDS its sha256 for provenance and asserts
    every consumed field (question, possible_answers, obj, prop) is present
    and non-empty on every row (gates.yaml SC0 feasibility assertion,
    already spot-checked in NOTEBOOK's pre-sign feasibility probe; this is
    the full-pool, code-enforced re-check).

No question/answer/generation text, row_key, or category value ever enters
the COMMITTED manifest -- only paths, sha256, and counts.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

STAGED = config.EXPERIMENT_DIR / "analysis" / "staged_inputs"
MARGIN_MAPPING_HARNESS = config.REPO_ROOT / "experiments" / "margin-mapping" / "harness"
DETECTOR_STACK_FILES = ("detector_v2.py", "detector_v2_patterns.yaml", "grader.py")


def _copy_local(src: Path, dest: Path) -> None:
    if not src.is_file():
        raise SystemExit(f"SC0 FAILED: missing source file: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise SystemExit(f"SC0 FAILED: destination {dest} is an existing symlink; refusing to overwrite a stale link with a copy.")
    shutil.copy2(src, dest)


def stage_transfer_c_hat() -> dict[str, Any]:
    src = config.TRANSFER_C_HAT_PATH
    dest = STAGED / "directions" / "hs20" / "c_hat_transfer.json"
    _copy_local(src, dest)
    sha = common.sha256_of_file(dest)
    src_sha = common.sha256_of_file(src)
    if src_sha != config.TRANSFER_C_HAT_SHA256_PINNED:
        raise SystemExit(
            f"SC0 FAILED: transfer c_hat source sha256 {src_sha} != cell.yaml "
            f"pin {config.TRANSFER_C_HAT_SHA256_PINNED}. Source has drifted "
            f"since sign; do not proceed."
        )
    if sha != config.TRANSFER_C_HAT_SHA256_PINNED:
        raise SystemExit(f"SC0 FAILED: transfer c_hat staged-copy sha256 {sha} != pinned {config.TRANSFER_C_HAT_SHA256_PINNED} (copy corruption?).")
    return {"name": "transfer_c_hat", "source_path": str(src), "dest_path": str(dest.relative_to(config.EXPERIMENT_DIR)), "sha256": sha, "matches_cell_yaml_pin": True}


def verify_detector_stack_byte_identical() -> dict[str, Any]:
    """Live re-check that the detector-stack CODE files copied into this
    harness/ at build time are still byte-identical to margin-mapping's own
    copies (the direct source they were copied FROM at build time)."""
    results = {}
    all_pass = True
    for fname in DETECTOR_STACK_FILES:
        mine = HERE / fname
        theirs = MARGIN_MAPPING_HARNESS / fname
        if not mine.is_file():
            raise SystemExit(f"SC0 FAILED: detector-stack file missing in this harness: {mine}")
        if not theirs.is_file():
            raise SystemExit(f"SC0 FAILED: margin-mapping detector-stack source missing: {theirs}")
        sha_mine = common.sha256_of_file(mine)
        sha_theirs = common.sha256_of_file(theirs)
        passed = sha_mine == sha_theirs
        all_pass = all_pass and passed
        results[fname] = {"sha256_mine": sha_mine, "sha256_margin_mapping": sha_theirs, "byte_identical": passed}
    if not all_pass:
        raise SystemExit(f"SC0 FAILED: detector stack is NOT byte-identical to margin-mapping's copies: {results}")
    return {"pass": all_pass, "files": results}


def _parse_json_list(raw: Any) -> list:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return v if isinstance(v, list) else [v]
        except json.JSONDecodeError:
            return []
    return []


def stage_popqa() -> dict[str, Any]:
    src = config.POPQA_PATH
    if not src.is_file():
        raise SystemExit(f"SC0 FAILED: missing PopQA source: {src}")
    dest = STAGED / "popqa_test.jsonl"
    _copy_local(src, dest)
    sha = common.sha256_of_file(dest)

    n_rows = 0
    n_missing_question = 0
    n_missing_gold = 0
    n_missing_aliases = 0
    n_missing_prop = 0
    prop_counts: dict[str, int] = {}
    with dest.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n_rows += 1
            row = json.loads(line)
            if not row.get("question"):
                n_missing_question += 1
            if not row.get(config.POPQA_GOLD_FIELD):
                n_missing_gold += 1
            aliases = _parse_json_list(row.get(config.POPQA_ALIASES_FIELD))
            if not aliases:
                n_missing_aliases += 1
            prop = row.get(config.POPQA_CATEGORY_FIELD)
            if not prop:
                n_missing_prop += 1
            else:
                prop_counts[prop] = prop_counts.get(prop, 0) + 1

    if n_rows != config.POPQA_N_ROWS:
        raise SystemExit(f"SC0 FAILED: PopQA has {n_rows} rows, expected {config.POPQA_N_ROWS}.")
    if n_missing_question or n_missing_gold or n_missing_aliases or n_missing_prop:
        raise SystemExit(
            f"SC0 FAILED: PopQA feasibility check failed: missing_question={n_missing_question} "
            f"missing_gold={n_missing_gold} missing_aliases={n_missing_aliases} missing_prop={n_missing_prop}"
        )
    min_bucket = min(prop_counts.values()) if prop_counts else 0
    return {
        "name": "popqa_test", "source_path": str(src), "dest_path": str(dest.relative_to(config.EXPERIMENT_DIR)),
        "sha256": sha, "n_rows": n_rows, "n_prop_categories": len(prop_counts),
        "min_prop_bucket": min_bucket, "prop_counts": prop_counts,
        "feasibility": {
            "n_missing_question": n_missing_question, "n_missing_gold": n_missing_gold,
            "n_missing_aliases": n_missing_aliases, "n_missing_prop": n_missing_prop,
            "all_fields_present": True,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    config.assert_pinned_hashes()

    transfer_record = stage_transfer_c_hat()
    detector_check = verify_detector_stack_byte_identical()
    popqa_record = stage_popqa()

    manifest = {
        "config_hashes_verified": config.verify_pinned_hashes(),
        "transfer_c_hat": transfer_record,
        "detector_stack_byte_identical": detector_check,
        "popqa": {k: v for k, v in popqa_record.items() if k != "prop_counts"},
        "popqa_prop_counts": popqa_record["prop_counts"],
    }
    common.write_json(config.EXPERIMENT_DIR / "analysis-committed" / "staging_manifest.json", manifest)

    print(json.dumps({k: v for k, v in manifest.items() if k != "popqa_prop_counts"}, indent=2), flush=True)
    print(f"[staging] transfer_c_hat sha256={transfer_record['sha256'][:16]} matches_pin=OK", flush=True)
    print(f"[staging] detector stack byte-identical: {detector_check['pass']}", flush=True)
    print(f"[staging] PopQA: n_rows={popqa_record['n_rows']} n_prop_categories={popqa_record['n_prop_categories']} min_bucket={popqa_record['min_prop_bucket']} sha256={popqa_record['sha256'][:16]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
