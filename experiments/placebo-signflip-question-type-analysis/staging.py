#!/usr/bin/env python3
"""BG0 (provenance and re-slice fidelity) stage-in for
placebo-signflip-question-type-analysis.

CPU-only, no model, no GPU. Every input this experiment reads lives in
another experiment's GITIGNORED `analysis/`/`directions/` tree, in a
DIFFERENT git worktree on this machine (the amendment/cell/gates docs are the
locked spec; cross-worktree paths are this build's own provenance wiring, not
a design decision). Two kinds of source:

  committed  -- already present in THIS worktree's own git history (doubt-
                snap's directions/build_manifest, RR2's final_report.json,
                RR's llama build manifests, RR2's own direction_fit.py
                module). No symlink needed; referenced by relative path.
  gitignored -- large local run products (runlogs, anchor tensors/JSONs,
                row_level_scored.jsonl, RR2's reconstructed hs16 directions)
                that exist ONLY in the worktree that generated them. Staged
                into this experiment's own gitignored analysis/staged_inputs/
                via SYMLINK (never copy -- the mistral/llama anchor JSONs are
                251-493MB; the RR3 pipeline is running on the local 3090 and
                host RAM is tight, so this build never loads those files
                itself, see frame_port.py/test_signflip_smoke.py for the
                opt-in real-data checks that do).

Mirrors abstention-wide-instrument-calibration/stage_inputs.py's manifest
shape (cell/arm/schema/source_path/dest_path/sha256/row_count), generalized
to symlink instead of copy and to cover non-JSONL artifacts (safetensors,
single-object JSON), following the rr3-corrected-placebo-replication
convention of symlinking `analysis/staged_inputs/<family>/...` rather than
copying (verified on disk: its staged_inputs/{llama,mistral}/ entries are
symlinks, not regular files).

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
from common import sha256_of_file, write_json  # noqa: E402

# ---------------------------------------------------------------------------
# Cross-worktree roots. These are THIS MACHINE's local worktree layout (see
# `git worktree list` at the repo root), not a repo-relative convention --
# every gitignored artifact this experiment reads was generated in one of
# these sibling worktrees and never committed anywhere.
# ---------------------------------------------------------------------------

_WT = Path("/home/profsynapse/code/ehr-worktrees")
HELDOUT_WT = _WT / "qwen35-midband-heldout" / "experiments" / "qwen35-4b-midband-heldout"
CALIBRATION_WT = _WT / "abstention-calibration" / "experiments" / "abstention-wide-instrument-calibration"
RR2_WT = _WT / "rr2-mistral-confirm" / "experiments" / "rr2-mistral-adjudicated-refusal-confirm"
RR_WT = _WT / "rr-raw-refusal" / "experiments" / "rr-cross-family-raw-refusal"

# Committed-in-this-worktree sources (relative to HERE's parent experiments/
# tree; no symlink, referenced directly by every downstream module).
DOUBT_SNAP_DIR = HERE.parent / "qwen35-4b-midband-doubt-snap"
RR2_LOCAL_DIR = HERE.parent / "rr2-mistral-adjudicated-refusal-confirm"
RR_LOCAL_DIR = HERE.parent / "rr-cross-family-raw-refusal"


def _jsonl_row_count(path: Path) -> int:
    n = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


def _json_object_key_count(path: Path) -> int:
    """Top-level key count of a single-object JSON file (anchor dicts keyed
    by row_key) WITHOUT holding the fully-parsed float payload longer than
    needed for the count -- still a full parse (no ijson available in this
    environment), so callers must not invoke this on the 251MB/493MB anchor
    files from a memory-constrained context; staging only calls it for the
    small direction/build_manifest JSONs."""
    return len(json.loads(path.read_text(encoding="utf-8")))


def _safetensors_key_count(path: Path) -> int:
    from safetensors import safe_open

    with safe_open(str(path), framework="numpy") as f:
        return len(f.keys())


GITIGNORED_ENTRIES: list[dict[str, Any]] = [
    # --- qwen heldout (QH): behavioral leg + BG1 ground truth -------------
    {"name": "qh_baseline_runlog", "kind": "jsonl", "source": HELDOUT_WT / "analysis" / "runlog" / "baseline.jsonl", "dest": "qh/baseline.jsonl"},
    {"name": "qh_random_direction_runlog", "kind": "jsonl", "source": HELDOUT_WT / "analysis" / "runlog" / "random_direction.jsonl", "dest": "qh/random_direction.jsonl"},
    {"name": "qh_gated_runlog", "kind": "jsonl", "source": HELDOUT_WT / "analysis" / "runlog" / "gated.jsonl", "dest": "qh/gated.jsonl", "note": "BG1 ground-truth fired-set for the qwen frame port, not used by the behavioral leg"},
    {"name": "qh_anchor_tensors", "kind": "safetensors", "source": HELDOUT_WT / "analysis" / "anchor_extract_heldout.safetensors", "dest": "qh/anchor_extract_heldout.safetensors"},
    {"name": "qh_anchor_manifest", "kind": "json", "source": HELDOUT_WT / "analysis" / "anchor_extract_heldout_manifest.json", "dest": "qh/anchor_extract_heldout_manifest.json"},
    {"name": "qh_fire_decisions", "kind": "jsonl", "source": HELDOUT_WT / "analysis" / "fire_decisions_heldout.jsonl", "dest": "qh/fire_decisions_heldout.jsonl", "note": "already-computed fire decisions; BG1 recomputes independently and checks against gated.jsonl, this is provenance only"},
    {"name": "qh_rows_for_steer", "kind": "jsonl", "source": HELDOUT_WT / "analysis" / "heldout_rows_for_steer.jsonl", "dest": "qh/heldout_rows_for_steer.jsonl", "note": "category_canon per row_key; contains question text, gitignored destination only"},
    # --- calibration (QH/QL wide grades) -----------------------------------
    {"name": "calibration_row_level_scored", "kind": "jsonl", "source": CALIBRATION_WT / "analysis" / "row_level_scored.jsonl", "dest": "calibration/row_level_scored.jsonl", "note": "contains generation text, gitignored destination only; wide_grade.field=sub_grade.refused_final"},
    # --- mistral RR2 (MC) ---------------------------------------------------
    {"name": "mc_baseline_runlog", "kind": "jsonl", "source": RR2_WT / "analysis" / "runlog" / "heldout__baseline.jsonl", "dest": "mc/heldout__baseline.jsonl"},
    {"name": "mc_random_direction_runlog", "kind": "jsonl", "source": RR2_WT / "analysis" / "runlog" / "heldout__random_direction.jsonl", "dest": "mc/heldout__random_direction.jsonl"},
    {"name": "mc_gated_runlog", "kind": "jsonl", "source": RR2_WT / "analysis" / "runlog" / "heldout__gated.jsonl", "dest": "mc/heldout__gated.jsonl", "note": "BG1 ground-truth fired-set for the mistral frame port"},
    {"name": "mc_id_map", "kind": "jsonl", "source": RR2_WT / "analysis" / "adjudication_id_map.jsonl", "dest": "mc/adjudication_id_map.jsonl", "note": "opaque_id -> (row_key, arm, is_decoy) for refused_final reconstruction"},
    {"name": "mc_graded", "kind": "jsonl", "source": RR2_WT / "analysis" / "graded.jsonl", "dest": "mc/graded.jsonl", "note": "blinded adjudication result, already committed via adjudication_graded_manifest.json sha256"},
    {"name": "mc_adjudication_pool", "kind": "jsonl", "source": RR2_WT / "analysis" / "adjudication_pool.jsonl", "dest": "mc/adjudication_pool.jsonl"},
    {"name": "mc_joined_rows_private", "kind": "jsonl", "source": RR2_WT / "analysis" / "joined_rows_private.jsonl", "dest": "mc/joined_rows_private.jsonl", "note": "role/split/category_canon/source per row_key; contains question text"},
    {"name": "mc_anchors", "kind": "json_large", "source": RR2_WT / "analysis" / "anchors_at_candidate_layers.json", "dest": "mc/anchors_at_candidate_layers.json", "note": "251MB; count NOT verified at staging time, see frame_port.py opt-in real-data check"},
    {"name": "mc_hs16_u_d", "kind": "json", "source": RR2_WT / "directions" / "hs16_u_d.json", "dest": "mc/directions/hs16_u_d.json", "note": "fit_reuse.py reconstruction, provenance-by-regeneration against RR's committed hs16_fit_build_manifest.json"},
    {"name": "mc_hs16_c_hat", "kind": "json", "source": RR2_WT / "directions" / "hs16_c_hat.json", "dest": "mc/directions/hs16_c_hat.json"},
    {"name": "mc_hs16_random_direction", "kind": "json", "source": RR2_WT / "directions" / "hs16_random_direction.json", "dest": "mc/directions/hs16_random_direction.json"},
    {"name": "mc_hs16_build_manifest", "kind": "json", "source": RR2_WT / "directions" / "hs16_build_manifest.json", "dest": "mc/directions/hs16_build_manifest.json"},
    {"name": "mc_fit_reuse_report", "kind": "json", "source": RR2_WT / "analysis" / "fit_reuse_report.json", "dest": "mc/fit_reuse_report.json", "note": "RR2's own field-for-field cross-check against RR's committed stats; BG1 mistral evidence"},
    # --- llama RR (M1/M2 only, no placebo arm) ------------------------------
    {"name": "llama_joined_rows_private", "kind": "jsonl", "source": RR_WT / "analysis" / "llama" / "joined_rows_private.jsonl", "dest": "llama/joined_rows_private.jsonl"},
    {"name": "llama_anchors", "kind": "json_large", "source": RR_WT / "analysis" / "llama" / "anchors_at_candidate_layers.json", "dest": "llama/anchors_at_candidate_layers.json", "note": "493MB; count NOT verified at staging time, see frame_port.py opt-in real-data check"},
    {"name": "llama_hs20_gated_dose2", "kind": "jsonl", "source": RR_WT / "analysis" / "llama" / "runlog" / "hs20__gated__dose2.jsonl", "dest": "llama/runlog/hs20__gated__dose2.jsonl", "note": "FIT-population fired set at hs20, BG1 llama ground truth (any dose; fire set is dose-invariant, verified across doses by frame_port.py's opt-in check)"},
    {"name": "llama_hs22_gated_dose2", "kind": "jsonl", "source": RR_WT / "analysis" / "llama" / "runlog" / "hs22__gated__dose2.jsonl", "dest": "llama/runlog/hs22__gated__dose2.jsonl"},
    {"name": "llama_hs23_gated_dose2", "kind": "jsonl", "source": RR_WT / "analysis" / "llama" / "runlog" / "hs23__gated__dose2.jsonl", "dest": "llama/runlog/hs23__gated__dose2.jsonl"},
]

# Committed-in-this-worktree sources: recorded in the manifest for provenance
# completeness (sha256 + count) but NOT symlinked (already local, already
# under git, already stable).
COMMITTED_ENTRIES: list[dict[str, Any]] = [
    {"name": "qwen_hs20_u_d", "kind": "json", "path": DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "u_d.json"},
    {"name": "qwen_hs20_c_hat", "kind": "json", "path": DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "c_hat.json"},
    {"name": "qwen_hs20_random_direction", "kind": "json", "path": DOUBT_SNAP_DIR / "analysis-committed" / "directions" / "hs20" / "random_direction.json"},
    {"name": "qwen_build_manifest", "kind": "json", "path": DOUBT_SNAP_DIR / "analysis-committed" / "build_manifest.json"},
    {"name": "rr2_final_report", "kind": "json", "path": RR2_LOCAL_DIR / "analysis-committed" / "final_report.json", "note": "MC certified check target (baseline 368/1312, random 465/1312); transcribed, never re-graded"},
    {"name": "rr2_direction_fit_module", "kind": "py", "path": RR2_LOCAL_DIR / "direction_fit.py", "note": "imported read-only by frame_port.py for the llama frame reconstruction; byte-for-byte port of rr-cross-family-raw-refusal/direction_fit.py"},
    {"name": "rr_llama_hs20_build_manifest", "kind": "json", "path": RR_LOCAL_DIR / "analysis-committed" / "llama" / "hs20_fit_build_manifest.json"},
    {"name": "rr_llama_hs22_build_manifest", "kind": "json", "path": RR_LOCAL_DIR / "analysis-committed" / "llama" / "hs22_fit_build_manifest.json"},
    {"name": "rr_llama_hs23_build_manifest", "kind": "json", "path": RR_LOCAL_DIR / "analysis-committed" / "llama" / "hs23_fit_build_manifest.json"},
]


def _count_for(kind: str, path: Path) -> int | None:
    if kind == "jsonl":
        return _jsonl_row_count(path)
    if kind == "safetensors":
        return _safetensors_key_count(path)
    if kind == "json":
        return _json_object_key_count(path) if path.stat().st_size < 5_000_000 else None
    if kind == "json_large":
        return None  # never parsed at staging time; see module docstring
    if kind == "py":
        return None
    raise ValueError(f"unknown kind {kind!r}")


def stage_gitignored(entry: dict[str, Any]) -> dict[str, Any]:
    src: Path = entry["source"]
    if not src.is_file():
        raise SystemExit(f"BG0 FAILED: missing source file for {entry['name']!r}: {src}")
    dest = STAGED / entry["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        dest.unlink()
    dest.symlink_to(src)
    record = {
        "name": entry["name"], "kind": entry["kind"], "staged": True,
        "source_path": str(src), "dest_path": str(dest.relative_to(HERE)),
        "sha256": sha256_of_file(src), "count": _count_for(entry["kind"], src),
    }
    if "note" in entry:
        record["note"] = entry["note"]
    return record


def record_committed(entry: dict[str, Any]) -> dict[str, Any]:
    path: Path = entry["path"]
    if not path.is_file():
        raise SystemExit(f"BG0 FAILED: missing committed-in-worktree source for {entry['name']!r}: {path}")
    record = {
        "name": entry["name"], "kind": entry["kind"], "staged": False,
        "source_path": str(path), "dest_path": None,
        "sha256": sha256_of_file(path), "count": _count_for(entry["kind"], path),
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
    write_json(COMMITTED / "staging_manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}, indent=2), flush=True)
    for r in records:
        count = r["count"] if r["count"] is not None else "n/a"
        print(f"  {'SYM' if r['staged'] else 'LOC'} {r['name']:32s} count={count!s:8s} sha256={r['sha256'][:10]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
