#!/usr/bin/env python3
"""SC0 (provenance and staging) stage-in for gate-contribution-factorial.

CPU-only, no model, no GPU. Mirrors
`placebo-seed-distribution-census/staging.py` (read in full before writing
this): every source runlog, frozen direction JSON, and fit build_manifest
this experiment reads is symlinked (never copied) into this experiment's own
gitignored `analysis/staged_inputs/<family>/...`, with sha256 + row/vector
counts recorded in a COMMITTED, ID-only manifest (gates.yaml
`sc0_provenance_and_staging.stage_inputs`).

Two kinds of source (see config.py for the resolved absolute paths and their
citations):

  gitignored  large local run products that exist ONLY in the sibling
              worktree that generated them (baseline/gated runlogs, private
              question/alias pools, RR2's own reconstructed hs16 direction
              JSONs, qwen's fire decisions and steer-row pool).
  committed   already present in THIS worktree's own git history (qwen's
              doubt-snap committed directions/hs20/ + build_manifest.json,
              qwen35-4b-midband-heldout's own frozen_operating_point_hashes.
              json, RR's own committed mistral hs16_fit_build_manifest.json).

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


def _json_object_key_count(path: Path):
    if path.stat().st_size > 5_000_000:
        return None
    return len(json.loads(path.read_text(encoding="utf-8")))


GITIGNORED_ENTRIES: list[dict[str, Any]] = [
    # --- qwen35_4b (QH) ------------------------------------------------
    {"name": "qwen_baseline_runlog", "kind": "jsonl", "source": config.QH_WT / "analysis" / "runlog" / "baseline.jsonl", "dest": "qwen35_4b/baseline.jsonl"},
    {"name": "qwen_gated_runlog", "kind": "jsonl", "source": config.QH_WT / "analysis" / "runlog" / "gated.jsonl", "dest": "qwen35_4b/gated.jsonl", "note": "fired-rows-only pass (1303 rows); combined with baseline for non-fired rows at read time (gate_construction / run_factorial)"},
    {"name": "qwen_fire_decisions", "kind": "jsonl", "source": config.QH_WT / "analysis" / "fire_decisions_heldout.jsonl", "dest": "qwen35_4b/fire_decisions_heldout.jsonl", "note": "row-level neg_z_d/fire decisions at the frozen tau; numbers only, no text"},
    {"name": "qwen_heldout_rows_for_steer", "kind": "jsonl", "source": config.QH_WT / "analysis" / "heldout_rows_for_steer.jsonl", "dest": "qwen35_4b/heldout_rows_for_steer.jsonl", "note": "question text + aliases + role/split/category_canon per row_key; gitignored destination only. ALSO the exact row ORDER used for the qwen permuted-gate index draw (gate_construction.qwen_permuted_gate_row_keys)"},
    # --- mistral7b_v03 (RR2) --------------------------------------------
    {"name": "mistral_baseline_runlog", "kind": "jsonl", "source": config.RR2_WT / "analysis" / "runlog" / "heldout__baseline.jsonl", "dest": "mistral7b_v03/baseline.jsonl"},
    {"name": "mistral_gated_runlog", "kind": "jsonl", "source": config.RR2_WT / "analysis" / "runlog" / "heldout__gated.jsonl", "dest": "mistral7b_v03/gated.jsonl", "note": "fired-rows-only pass (1303 confab rows, 0 known; RR2 lines 142, 151)"},
    {"name": "mistral_joined_rows_private", "kind": "jsonl", "source": config.RR2_WT / "analysis" / "joined_rows_private.jsonl", "dest": "mistral7b_v03/joined_rows_private.jsonl", "note": "question text + aliases + role/split per row_key, gitignored destination only"},
    {"name": "mistral_hs16_u_d", "kind": "json", "source": config.RR2_WT / "directions" / "hs16_u_d.json", "dest": "mistral7b_v03/directions/hs16_u_d.json"},
    {"name": "mistral_hs16_c_hat", "kind": "json", "source": config.RR2_WT / "directions" / "hs16_c_hat.json", "dest": "mistral7b_v03/directions/hs16_c_hat.json"},
    {"name": "mistral_hs16_random_direction", "kind": "json", "source": config.RR2_WT / "directions" / "hs16_random_direction.json", "dest": "mistral7b_v03/directions/hs16_random_direction.json"},
    {"name": "mistral_hs16_build_manifest_rr2", "kind": "json", "source": config.RR2_WT / "directions" / "hs16_build_manifest.json", "dest": "mistral7b_v03/directions/hs16_build_manifest.json", "note": "RR2's own reconstruction (via its fit_reuse.py) of RR's committed hs16 fit; cross-checked field-for-field against RR's committed manifest by mistral_direction_provenance.py"},
    {"name": "mistral_fit_reuse_report_rr2", "kind": "json", "source": config.RR2_WT / "analysis" / "fit_reuse_report.json", "dest": "mistral7b_v03/fit_reuse_report_rr2.json", "note": "RR2's own RG0 field-for-field crosscheck of its hs16 reconstruction against RR's committed manifest; pass=true expected (independently re-verified by mistral_direction_provenance.py)"},
]

COMMITTED_ENTRIES: list[dict[str, Any]] = [
    {"name": "qwen_hs20_u_d", "kind": "json", "path": config.DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "u_d.json"},
    {"name": "qwen_hs20_c_hat", "kind": "json", "path": config.DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "c_hat.json"},
    {"name": "qwen_hs20_random_direction", "kind": "json", "path": config.DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "random_direction.json"},
    {"name": "qwen_doubt_snap_build_manifest", "kind": "json", "path": config.DOUBT_SNAP_DIR / "analysis-committed" / "build_manifest.json"},
    {"name": "qwen_heldout_frozen_operating_point_hashes", "kind": "json", "path": config.QH_LOCAL_DIR / "frozen_operating_point_hashes.json"},
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
