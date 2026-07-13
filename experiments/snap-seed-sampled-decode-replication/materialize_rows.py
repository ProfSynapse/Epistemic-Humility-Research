#!/usr/bin/env python3
"""H3 seed/sampled-decode replication -- materialize the LOCAL, gitignored
held-out row pool (CPU-only, no GPU, no network).

This experiment refits nothing and re-extracts nothing (AMENDMENT.md
"Design"): the L34 anchor activations for every held-out row are already the
ones the resolved doubt-gated-caution-tighten cell extracted -- the anchor is
a function of the prompt only (prompt_len-1, before any generation or
write), so the SAME tensors are valid input to this experiment's gate-
decision math without a fresh forward pass. This script only JOINS the
promoted ID-only split manifest against those existing artifacts and subsets
them to held-out rows; it fetches no text over the network. (Same reuse
strategy as the sibling H4 ungated-vs-gated-dose-matched build; see that
experiment's materialize_rows.py for the original finding.)

Sources (read, never modified):
  - experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json
    (committed, ID-only: row_key/role/split for all 739 gate-role rows, FIT +
    HELD-OUT; this script keeps split=="held_out" only -- 185 confab + 258
    known_correct_answered).
  - The resolved cell's own gitignored run artifacts, rows_with_text.jsonl
    (question + aliases + category_canon) and l34_anchor_extract.safetensors
    (L34 anchor vectors, prompt_len-1, keyed by sanitized row_key). Default
    source is the build worktree where that cell was actually run
    (/home/profsynapse/code/ehr-worktrees/gate-snap-tighten/experiments/doubt-gated-caution-tighten/analysis/),
    overridable via --source-dir for when that worktree is gone -- in that
    case, regenerate the two files by re-running
    experiments/doubt-gated-caution-tighten/{extract_l34_anchor.py,
    materialize_rows.py} from a worktree with the AH A0 / AK Stage-1 source
    pools present, then point --source-dir at that experiment's own
    analysis/ directory.

Outputs (this experiment's own gitignored analysis/, never committed):
  analysis/rows_with_text.jsonl              443 held-out rows (question,
                                              aliases, category_canon).
  analysis/l34_anchor_extract_heldout.safetensors   443 anchor vectors,
                                              subset of the source extraction,
                                              keyed by sanitized row_key.

Usage:
  python materialize_rows.py
    (writes both outputs under this experiment's analysis/, gitignored)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMON_SPLIT_MANIFEST = (
    HERE.parent / "common" / "doubt-gated-caution-tighten-heldout-split" / "split_manifest.json"
)
ANALYSIS = HERE / "analysis"

DEFAULT_SOURCE_DIR = Path(
    "/home/profsynapse/code/ehr-worktrees/gate-snap-tighten/"
    "experiments/doubt-gated-caution-tighten/analysis"
)

OUT_ROWS = ANALYSIS / "rows_with_text.jsonl"
OUT_TENSORS = ANALYSIS / "l34_anchor_extract_heldout.safetensors"
OUT_MANIFEST = ANALYSIS / "l34_anchor_extract_heldout_manifest.json"


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR),
                     help="resolved cell's analysis/ dir holding rows_with_text.jsonl "
                          "and l34_anchor_extract.safetensors")
    args = ap.parse_args(argv)

    source_dir = Path(args.source_dir)
    source_rows_path = source_dir / "rows_with_text.jsonl"
    source_tensors_path = source_dir / "l34_anchor_extract.safetensors"

    if not COMMON_SPLIT_MANIFEST.is_file():
        print(f"[materialize] ERROR: common split manifest not found at "
              f"{COMMON_SPLIT_MANIFEST}.", file=sys.stderr)
        return 1
    if not source_rows_path.is_file() or not source_tensors_path.is_file():
        print(
            f"[materialize] ERROR: resolved-cell source artifacts not found under "
            f"{source_dir}. This experiment reuses the resolved cell's own gitignored "
            "run outputs rather than re-extracting; if that worktree is gone, "
            "re-run experiments/doubt-gated-caution-tighten/{extract_l34_anchor.py,"
            "materialize_rows.py} elsewhere and pass --source-dir at the resulting "
            "analysis/ directory.",
            file=sys.stderr,
        )
        return 1

    split_manifest = json.loads(COMMON_SPLIT_MANIFEST.read_text())
    held_keys_by_role: dict[str, set[str]] = {"confab": set(), "known_correct_answered": set()}
    for rec in split_manifest["rows"]:
        if rec["split"] == "held_out" and rec["role"] in held_keys_by_role:
            held_keys_by_role[rec["role"]].add(rec["row_key"])
    n_expected_confab = len(held_keys_by_role["confab"])
    n_expected_known = len(held_keys_by_role["known_correct_answered"])
    print(f"[materialize] held-out manifest: confab={n_expected_confab} "
          f"known_correct_answered={n_expected_known}")

    source_rows = load_jsonl(source_rows_path)
    held_rows = [
        r for r in source_rows
        if r.get("split") == "held_out" and r.get("row_key") in held_keys_by_role.get(r.get("role"), set())
    ]

    n_missing_q = sum(1 for r in held_rows if not r.get("question"))
    n_missing_alias_known = sum(
        1 for r in held_rows if r["role"] == "known_correct_answered" and not r.get("aliases")
    )
    found_confab = sum(1 for r in held_rows if r["role"] == "confab")
    found_known = sum(1 for r in held_rows if r["role"] == "known_correct_answered")

    if found_confab != n_expected_confab or found_known != n_expected_known:
        print(
            f"[materialize] ERROR: row-count mismatch vs common split manifest -- "
            f"expected confab={n_expected_confab}/known={n_expected_known}, found "
            f"confab={found_confab}/known={found_known}. The source worktree's own "
            "split_manifest.json may have diverged from the promoted common copy.",
            file=sys.stderr,
        )
        return 1
    if n_missing_q:
        print(f"[materialize] ERROR: {n_missing_q} held-out rows have no question text.",
              file=sys.stderr)
        return 1
    if n_missing_alias_known:
        print(
            f"[materialize] ERROR: {n_missing_alias_known} known_correct_answered held-out "
            "rows have empty aliases; correctness grading cannot proceed.",
            file=sys.stderr,
        )
        return 1

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    with OUT_ROWS.open("w", encoding="utf-8") as fh:
        for r in held_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    from safetensors.numpy import load_file, save_file

    source_tensors = load_file(str(source_tensors_path))
    wanted_keys = {_sanitize_key(r["row_key"]) for r in held_rows}
    missing_tensors = sorted(k for k in wanted_keys if k not in source_tensors)
    if missing_tensors:
        print(
            f"[materialize] ERROR: {len(missing_tensors)} held-out rows have no L34 "
            f"anchor tensor in {source_tensors_path} (first few: {missing_tensors[:5]}).",
            file=sys.stderr,
        )
        return 1
    subset = {k: v for k, v in source_tensors.items() if k in wanted_keys}
    save_file(subset, str(OUT_TENSORS))

    manifest = {
        "stage": "h3_seed_sampled_decode_heldout_materialize",
        "source_dir": str(source_dir),
        "source_rows_path": str(source_rows_path),
        "source_tensors_path": str(source_tensors_path),
        "common_split_manifest": str(COMMON_SPLIT_MANIFEST),
        "n_confab_held_out": found_confab,
        "n_known_correct_answered_held_out": found_known,
        "n_tensors_subset": len(subset),
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2))

    print(f"[materialize] WROTE {OUT_ROWS} ({len(held_rows)} rows) and {OUT_TENSORS} "
          f"({len(subset)} vectors); missing_question=0 missing_alias_on_known_correct_answered=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
