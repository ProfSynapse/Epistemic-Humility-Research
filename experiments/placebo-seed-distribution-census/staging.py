#!/usr/bin/env python3
"""SC0 (provenance and staging) stage-in for placebo-seed-distribution-census.

CPU-only, no model, no GPU. Mirrors
`placebo-signflip-question-type-analysis/staging.py` (read in full before
writing this) and, one level further back,
`abstention-wide-instrument-calibration/stage_inputs.py`'s manifest shape
(cell/arm/schema/source_path/dest_path/sha256/row_count): every source
runlog, baseline artifact, frozen direction JSON, and fit build_manifest this
census reads is symlinked (never copied -- some of these are large; host RAM
is limited) into this experiment's own gitignored
`analysis/staged_inputs/<family>/...`, with sha256 + row/vector counts
recorded in a COMMITTED, ID-only manifest (gates.yaml `sc0_provenance_and_
staging.stage_inputs`).

Two kinds of source (see config.py for the resolved absolute paths and their
citations):

  gitignored  -- large local run products that exist ONLY in the sibling
                 worktree that generated them (baseline runlogs, joined-rows-
                 private question/alias pools, RR2's/RR3's reconstructed
                 direction JSONs). Symlinked.
  committed   -- already present in THIS worktree's own git history (qwen's
                 doubt-snap committed directions/hs20/, RR's own committed
                 llama hs20 / mistral hs16 fit-build manifests). Recorded for
                 provenance completeness (sha256 + count) but not symlinked.

No question/answer/generation text, row_key, or category_canon value EVER
enters the committed manifest -- only paths, sha256, and counts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
STAGED = ANALYSIS / "staged_inputs"
COMMITTED = HERE / "analysis-committed"

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


def _json_object_key_count(path: Path) -> int:
    if path.stat().st_size > 5_000_000:
        return None
    return len(json.loads(path.read_text(encoding="utf-8")))


GITIGNORED_ENTRIES: list[dict[str, Any]] = [
    # --- qwen35_4b (QH) ------------------------------------------------
    {"name": "qwen_baseline_runlog", "kind": "jsonl", "source": config.BASELINE_RUNLOG["qwen35_4b"], "dest": "qwen35_4b/baseline.jsonl"},
    {"name": "qwen_heldout_rows_for_steer", "kind": "jsonl", "source": config.QH_WT / "analysis" / "heldout_rows_for_steer.jsonl", "dest": "qwen35_4b/heldout_rows_for_steer.jsonl", "note": "question text + aliases + role/split per row_key, gitignored destination only"},
    {"name": "qwen_random_direction_runlog", "kind": "jsonl", "source": config.QH_WT / "analysis" / "runlog" / "random_direction.jsonl", "dest": "qwen35_4b/random_direction.jsonl", "note": "QH's own gated random-direction pass; row_key set used ONLY to compute the paired-pool intersection with baseline.jsonl (1286 rows, calibration AMENDMENT line 173) -- the census itself does not reuse this pass's text or apply any gate"},
    # --- mistral7b_v03 (MC/RR2) -----------------------------------------
    {"name": "mistral_baseline_runlog", "kind": "jsonl", "source": config.BASELINE_RUNLOG["mistral7b_v03"], "dest": "mistral7b_v03/baseline.jsonl"},
    {"name": "mistral_joined_rows_private", "kind": "jsonl", "source": config.RR2_WT / "analysis" / "joined_rows_private.jsonl", "dest": "mistral7b_v03/joined_rows_private.jsonl", "note": "question text + aliases + role/split per row_key, gitignored destination only"},
    {"name": "mistral_hs16_u_d", "kind": "json", "source": config.DIRECTIONS_DIR["mistral7b_v03"] / "hs16_u_d.json", "dest": "mistral7b_v03/directions/hs16_u_d.json"},
    {"name": "mistral_hs16_c_hat", "kind": "json", "source": config.DIRECTIONS_DIR["mistral7b_v03"] / "hs16_c_hat.json", "dest": "mistral7b_v03/directions/hs16_c_hat.json"},
    {"name": "mistral_hs16_random_direction", "kind": "json", "source": config.DIRECTIONS_DIR["mistral7b_v03"] / "hs16_random_direction.json", "dest": "mistral7b_v03/directions/hs16_random_direction.json"},
    {"name": "mistral_hs16_build_manifest_rr2", "kind": "json", "source": config.DIRECTIONS_DIR["mistral7b_v03"] / "hs16_build_manifest.json", "dest": "mistral7b_v03/directions/hs16_build_manifest.json"},
    # --- llama32_3b (RR / RR3 rider reconstruction) ----------------------
    {"name": "llama_baseline_runlog", "kind": "jsonl", "source": config.BASELINE_RUNLOG["llama32_3b"], "dest": "llama32_3b/baseline.jsonl", "note": "SUBSTITUTION: cell.yaml names an RR llama baseline that does not exist on disk; this is RR3's own rider_llama__baseline.jsonl, same generation contract; see config.py BASELINE_RUNLOG comment"},
    {"name": "llama_joined_rows_private", "kind": "jsonl", "source": config.RR_WT / "analysis" / "llama" / "joined_rows_private.jsonl", "dest": "llama32_3b/joined_rows_private.jsonl", "note": "question text + aliases + role/split per row_key, gitignored destination only"},
    {"name": "llama_hs20_u_d_rr3_reconstruction", "kind": "json", "source": config.DIRECTIONS_DIR["llama32_3b"] / "llama_hs20_u_d.json", "dest": "llama32_3b/directions/llama_hs20_u_d.json"},
    {"name": "llama_hs20_c_hat_rr3_reconstruction", "kind": "json", "source": config.DIRECTIONS_DIR["llama32_3b"] / "llama_hs20_c_hat.json", "dest": "llama32_3b/directions/llama_hs20_c_hat.json"},
    {"name": "llama_hs20_random_direction_rr3_reconstruction", "kind": "json", "source": config.DIRECTIONS_DIR["llama32_3b"] / "llama_hs20_random_direction.json", "dest": "llama32_3b/directions/llama_hs20_random_direction.json"},
    {"name": "llama_hs20_build_manifest_rr3_reconstruction", "kind": "json", "source": config.DIRECTIONS_DIR["llama32_3b"] / "llama_hs20_build_manifest.json", "dest": "llama32_3b/directions/llama_hs20_build_manifest.json"},
    {"name": "llama_fit_reuse_report_rr3", "kind": "json", "source": config.RR3_WT / "analysis" / "llama" / "fit_reuse_report.json", "dest": "llama32_3b/fit_reuse_report_rr3.json", "note": "RR3's own RG0 field-for-field crosscheck of the llama hs20 reconstruction against RR's committed manifest; pass=true, mismatches={} (independently re-verified by llama_setpoint_provenance.py)"},
]

COMMITTED_ENTRIES: list[dict[str, Any]] = [
    {"name": "qwen_hs20_u_d", "kind": "json", "path": config.DIRECTIONS_DIR["qwen35_4b"] / "u_d.json"},
    {"name": "qwen_hs20_c_hat", "kind": "json", "path": config.DIRECTIONS_DIR["qwen35_4b"] / "c_hat.json"},
    {"name": "qwen_hs20_random_direction", "kind": "json", "path": config.DIRECTIONS_DIR["qwen35_4b"] / "random_direction.json"},
    {"name": "rr_llama_hs20_build_manifest", "kind": "json", "path": config.RR_LOCAL_DIR / "analysis-committed" / "llama" / "hs20_fit_build_manifest.json"},
    {"name": "rr_mistral_hs16_build_manifest", "kind": "json", "path": config.RR_LOCAL_DIR / "analysis-committed" / "mistral" / "hs16_fit_build_manifest.json"},
]


def stage_gitignored(entry: dict[str, Any]) -> dict[str, Any]:
    src: Path = Path(entry["source"])
    if not src.is_file():
        raise SystemExit(f"SC0 FAILED: missing source file for {entry['name']!r}: {src}")
    dest = STAGED / entry["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        dest.unlink()
    dest.symlink_to(src)
    count = _jsonl_row_count(src) if entry["kind"] == "jsonl" else _json_object_key_count(src)
    record = {
        "name": entry["name"], "kind": entry["kind"], "staged": True,
        "source_path": str(src), "dest_path": str(dest.relative_to(HERE)),
        "sha256": common.sha256_of_file(src), "count": count,
    }
    if "note" in entry:
        record["note"] = entry["note"]
    return record


def record_committed(entry: dict[str, Any]) -> dict[str, Any]:
    path: Path = Path(entry["path"])
    if not path.is_file():
        raise SystemExit(f"SC0 FAILED: missing committed-in-worktree source for {entry['name']!r}: {path}")
    count = _json_object_key_count(path) if entry["kind"] == "json" else None
    record = {
        "name": entry["name"], "kind": entry["kind"], "staged": False,
        "source_path": str(path), "dest_path": None,
        "sha256": common.sha256_of_file(path), "count": count,
    }
    if "note" in entry:
        record["note"] = entry["note"]
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    records = [stage_gitignored(e) for e in GITIGNORED_ENTRIES]
    records += [record_committed(e) for e in COMMITTED_ENTRIES]

    manifest = {
        "n_files": len(records),
        "n_symlinked": sum(1 for r in records if r["staged"]),
        "n_committed_local": sum(1 for r in records if not r["staged"]),
        "files": records,
    }
    common.write_json(COMMITTED / "staging_manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2), flush=True)
    for r in records:
        count = r["count"] if r["count"] is not None else "n/a"
        print(f"  {'SYM' if r['staged'] else 'LOC'} {r['name']:40s} count={count!s:8s} sha256={r['sha256'][:10]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
