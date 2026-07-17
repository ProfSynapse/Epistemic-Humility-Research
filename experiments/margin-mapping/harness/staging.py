#!/usr/bin/env python3
"""SC0 (provenance and staging) stage-in for margin-mapping (M1).

CPU-only, no model, no GPU. Adapted (logic ported) from
`gate-contribution-factorial/staging.py` (read in full before writing this):
every source is symlinked (never copied) into this experiment's own
gitignored `analysis/staged_inputs/<family>/...`, with sha256 + row/vector
counts recorded in a COMMITTED, ID-only manifest (gates.yaml
`SC0_provenance_staging`).

M1 stages a NARROWER set than the factorial (no gate here, so no
gated.jsonl/fire_decisions/u_d/random_direction/build_manifest sources are
needed): per cell.yaml/AMENDMENT.md, only

  - the c_hat direction per family (qwen hs20, mistral hs16)
  - the baseline runlog per family (the dose_zero_rung, reused byte-
    identically per `ladder.dose_zero_rung`)
  - the question-pool source per family (needed to render any row at all;
    not itself named in `directions_source`/`baseline_runlog` but is a
    hard prerequisite of reusing the SAME held-out population the
    factorial's own row_pool.py defines -- documented here as a staging-
    scope call, not a spec value)

Every staged/committed entry's sha256 is asserted, IN CODE, against the
FACTORIAL'S OWN committed `staging_manifest.json`
(config.FACTORIAL_STAGING_MANIFEST) -- this is the "byte-identical (sha256
verified vs the factorial staging manifest)" requirement from cell.yaml's
`directions_source`/`baseline_runlog` fields; a mismatch is a hard SystemExit,
never a warning.

The "detector stack" (detector_v2.py, detector_v2_patterns.yaml, grader.py)
is CODE, not staged data -- it was copied byte-identically into this
harness/ directory at build time (verified `cp` + `sha256sum` against the
factorial's own copies). `verify_detector_stack_byte_identical()` re-checks
this live, so a future edit to either copy is caught rather than silently
trusted.

No question/answer/generation text, row_key, or category_canon value ever
enters the committed manifest -- only paths, sha256, and counts.
"""

from __future__ import annotations

import argparse
import json
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


def _jsonl_row_count(path: Path) -> int:
    n = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


# ---------------------------------------------------------------------------
# Sources. `factorial_name` is the entry `name` in the factorial's OWN
# committed staging_manifest.json this entry's sha256 must match.
# ---------------------------------------------------------------------------
GITIGNORED_ENTRIES: list[dict[str, Any]] = [
    {"name": "qwen_baseline_runlog", "factorial_name": "qwen_baseline_runlog", "kind": "jsonl",
     "source": config.QH_WT / "analysis" / "runlog" / "baseline.jsonl", "dest": "qwen35_4b/baseline.jsonl"},
    {"name": "qwen_heldout_rows_for_steer", "factorial_name": "qwen_heldout_rows_for_steer", "kind": "jsonl",
     "source": config.QH_WT / "analysis" / "heldout_rows_for_steer.jsonl", "dest": "qwen35_4b/heldout_rows_for_steer.jsonl",
     "note": "question text + aliases + role/split/category_canon per row_key; gitignored destination only"},
    {"name": "mistral_baseline_runlog", "factorial_name": "mistral_baseline_runlog", "kind": "jsonl",
     "source": config.RR2_WT / "analysis" / "runlog" / "heldout__baseline.jsonl", "dest": "mistral7b_v03/baseline.jsonl"},
    {"name": "mistral_joined_rows_private", "factorial_name": "mistral_joined_rows_private", "kind": "jsonl",
     "source": config.RR2_WT / "analysis" / "joined_rows_private.jsonl", "dest": "mistral7b_v03/joined_rows_private.jsonl",
     "note": "question text + aliases + role/split per row_key, gitignored destination only"},
    {"name": "mistral_hs16_c_hat", "factorial_name": "mistral_hs16_c_hat", "kind": "json",
     "source": config.RR2_WT / "directions" / "hs16_c_hat.json", "dest": "mistral7b_v03/directions/hs16_c_hat.json"},
]

COMMITTED_ENTRIES: list[dict[str, Any]] = [
    {"name": "qwen_hs20_c_hat", "factorial_name": "qwen_hs20_c_hat",
     "path": config.DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "c_hat.json"},
]

DETECTOR_STACK_FILES = ("detector_v2.py", "detector_v2_patterns.yaml", "grader.py")


def _load_factorial_manifest() -> dict[str, dict[str, Any]]:
    if not config.FACTORIAL_STAGING_MANIFEST.is_file():
        raise SystemExit(
            f"SC0 FAILED: factorial staging manifest not found at "
            f"{config.FACTORIAL_STAGING_MANIFEST}; cannot verify byte-identity "
            f"of reused artifacts."
        )
    manifest = common.load_json(config.FACTORIAL_STAGING_MANIFEST)
    return {rec["name"]: rec for rec in manifest["files"]}


def stage_gitignored(entry: dict[str, Any], factorial_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    src: Path = Path(entry["source"])
    if not src.is_file():
        raise SystemExit(f"SC0 FAILED: missing source file for {entry['name']!r}: {src}")
    dest = STAGED / entry["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        dest.unlink()
    dest.symlink_to(src)
    sha = common.sha256_of_file(src)
    count = _jsonl_row_count(src) if entry["kind"] == "jsonl" else None

    fact = factorial_by_name.get(entry["factorial_name"])
    if fact is None:
        raise SystemExit(f"SC0 FAILED: no factorial staging_manifest.json entry named {entry['factorial_name']!r} to verify {entry['name']!r} against.")
    if sha != fact["sha256"]:
        raise SystemExit(
            f"SC0 FAILED: {entry['name']!r} sha256 {sha} does NOT match the "
            f"factorial staging manifest's {entry['factorial_name']!r} entry "
            f"sha256 {fact['sha256']}. This artifact is not byte-identical to "
            f"the factorial's own staged input; do not proceed."
        )

    record = {
        "name": entry["name"], "kind": entry["kind"], "staged": True,
        "source_path": str(src), "dest_path": str(dest.relative_to(EXPERIMENT_DIR)),
        "sha256": sha, "count": count,
        "matches_factorial_manifest_entry": entry["factorial_name"],
    }
    if "note" in entry:
        record["note"] = entry["note"]
    return record


def record_committed(entry: dict[str, Any], factorial_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    path: Path = Path(entry["path"])
    if not path.is_file():
        raise SystemExit(f"SC0 FAILED: missing committed-in-worktree source for {entry['name']!r}: {path}")
    sha = common.sha256_of_file(path)

    fact = factorial_by_name.get(entry["factorial_name"])
    if fact is None:
        raise SystemExit(f"SC0 FAILED: no factorial staging_manifest.json entry named {entry['factorial_name']!r} to verify {entry['name']!r} against.")
    if sha != fact["sha256"]:
        raise SystemExit(
            f"SC0 FAILED: {entry['name']!r} sha256 {sha} does NOT match the "
            f"factorial staging manifest's {entry['factorial_name']!r} entry "
            f"sha256 {fact['sha256']}."
        )

    return {
        "name": entry["name"], "kind": "json", "staged": False,
        "source_path": str(path), "dest_path": None,
        "sha256": sha, "count": None,
        "matches_factorial_manifest_entry": entry["factorial_name"],
    }


def verify_detector_stack_byte_identical() -> dict[str, Any]:
    """Live re-check that the detector-stack CODE files copied into this
    harness/ at build time are still byte-identical to the factorial's own
    copies (which are the byte-identical pins cell.yaml's `readout.primary`
    field cites)."""
    results = {}
    all_pass = True
    for fname in DETECTOR_STACK_FILES:
        mine = HERE / fname
        theirs = config.FACTORIAL_EXPERIMENT_DIR / fname
        if not mine.is_file():
            raise SystemExit(f"SC0 FAILED: detector-stack file missing in this harness: {mine}")
        if not theirs.is_file():
            raise SystemExit(f"SC0 FAILED: factorial detector-stack source missing: {theirs}")
        sha_mine = common.sha256_of_file(mine)
        sha_theirs = common.sha256_of_file(theirs)
        passed = sha_mine == sha_theirs
        all_pass = all_pass and passed
        results[fname] = {"sha256_mine": sha_mine, "sha256_factorial": sha_theirs, "byte_identical": passed}
    if not all_pass:
        raise SystemExit(f"SC0 FAILED: detector stack is NOT byte-identical to the factorial's copies: {results}")
    return {"pass": all_pass, "files": results}


def rg0_baseline_check(family: str) -> dict[str, Any]:
    """RG0 byte-repro: re-verifies, on the row set this pool's population
    covers, that the staged baseline file's live sha256 matches BOTH the
    SC0-committed manifest just written AND the factorial's own committed
    manifest entry (transitively -- the SC0-committed check already implies
    this since stage_gitignored asserted it at staging time, but this
    function is the dedicated, independently-callable RG0 gate gates.yaml
    `SC0_provenance_staging` names explicitly)."""
    staged_path = STAGED / family / "baseline.jsonl"
    if not staged_path.is_file():
        raise SystemExit(f"RG0 baseline check FAIL ({family}): staged baseline missing at {staged_path}; run staging first.")
    live_sha256 = common.sha256_of_file(staged_path)

    manifest_path = COMMITTED / "staging_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"RG0 baseline check FAIL ({family}): no staging_manifest.json at {manifest_path}; run staging first.")
    manifest = common.load_json(manifest_path)
    name_key = "qwen_baseline_runlog" if family == "qwen35_4b" else "mistral_baseline_runlog"
    committed_entry = next((r for r in manifest["files"] if r["name"] == name_key), None)
    if committed_entry is None:
        raise SystemExit(f"RG0 baseline check FAIL ({family}): no staging_manifest.json entry {name_key!r}.")
    if live_sha256 != committed_entry["sha256"]:
        raise SystemExit(
            f"RG0 baseline check FAIL ({family}): staged baseline sha256 {live_sha256} != "
            f"SC0-committed {committed_entry['sha256']} (source drift since staging)."
        )
    return {"family": family, "staged_baseline_sha256": live_sha256, "passed": True}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    factorial_by_name = _load_factorial_manifest()

    records = [stage_gitignored(e, factorial_by_name) for e in GITIGNORED_ENTRIES]
    records += [record_committed(e, factorial_by_name) for e in COMMITTED_ENTRIES]

    manifest = {
        "n_files": len(records),
        "n_symlinked": sum(1 for r in records if r["staged"]),
        "n_committed_local": sum(1 for r in records if not r["staged"]),
        "verified_against_factorial_staging_manifest": str(config.FACTORIAL_STAGING_MANIFEST),
        "files": records,
    }
    common.write_json(COMMITTED / "staging_manifest.json", manifest)

    detector_check = verify_detector_stack_byte_identical()

    rg0 = {family: rg0_baseline_check(family) for family in config.FAMILIES}

    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2), flush=True)
    for r in records:
        count = r["count"] if r["count"] is not None else "n/a"
        print(f"  {'SYM' if r['staged'] else 'LOC'} {r['name']:35s} count={count!s:8s} sha256={r['sha256'][:10]} matches_factorial=OK", flush=True)
    print(f"[staging] detector stack byte-identical: {detector_check['pass']}", flush=True)
    for family, rg0_result in rg0.items():
        print(f"[staging] RG0 baseline check {family}: PASSED", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
