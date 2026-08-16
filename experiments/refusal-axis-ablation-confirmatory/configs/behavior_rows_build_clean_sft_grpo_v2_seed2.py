#!/usr/bin/env python3
"""Materialize the seed-2 SelfAware behavior-rows panel (AMENDMENT.md stage 1).

SEED-2 mirror of experiments/common/scripts/build_current_selfaware_behavior_rows.py's
`clean_sft_grpo_v2` panel (which produced
archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl
for seed 1). NOT a config file for that shared script: it has no YAML/CLI config
surface (PANELS is a hardcoded module-level list) and its OUT_ROOT constant
(archive/experiment/phase1/probe/legacy-wrapper-tree/analysis/current_selfaware_behavior_rows/)
is NOT covered by any .gitignore rule in this checkout -- confirmed via
`git check-ignore` on a would-be seed-2 output path there, exit 1 (not
ignored). Calling that script unmodified for seed 2 would risk writing
row-level question/answer text to a trackable path, so this cell has its own
thin driver instead, containment-safe under this cell's gitignored analysis/.

Reuses (imports, does not reimplement) the exact join logic
(`stable_row_key`, `behavior_cell`) from the shared script -- both are pure
functions with no OUT_ROOT/ROOT dependency, so importing them carries zero
risk of touching the shared script's global output path. Everything else
(loading, joining, writing) mirrors `materialize()` line-for-line, only
parameterized instead of hardcoded and writing under THIS cell's analysis/.

TRUE STAGE ORDER (flagged in the prep report): this script's SOURCE_ROWS
input is the seed-2 EXTRACTION's rows.jsonl (AMENDMENT stage 2's output), so
despite being "stage 1" in the AMENDMENT's prose numbering, it must run
AFTER extraction completes, not before. SCORED_ROWS is the seed-2 SelfAware
full eval's scored_rows.jsonl, which ALREADY EXISTS on disk from the
resolved `experiments/grpo-three-seed-confirmatory` cell (G1 numerator arm,
byte-identical response-confidence prompt contract) -- no new generation run
is needed for that half of the join. See RUNBOOK.md for the full order.

Usage (CPU-only, no GPU, no model load):
  python3 experiments/refusal-axis-ablation-confirmatory/configs/behavior_rows_build_clean_sft_grpo_v2_seed2.py \\
    --source-rows experiments/refusal-axis-ablation-confirmatory/analysis/hidden_states/qwen3-4b-clean-sft-grpo-v2-seed2-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_seed2_full/extraction__<sha>/rows.jsonl \\
    --scored-rows archive/experiment/phase1/eval/results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_full_4b/clean_schema_sft_grpo_v2_seed2__selfaware/scored_rows.jsonl \\
    --out experiments/refusal-axis-ablation-confirmatory/analysis/behavior_rows/clean_sft_grpo_v2_seed2/rows.jsonl

`--extraction-dir` (sha-suffixed) is not knowable before stage 2 actually
runs; pass the resolved --source-rows path once that directory exists (glob
for `extraction__*/rows.jsonl` under the hidden_states output root).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SHARED_SCRIPT_DIR = ROOT / "experiments" / "common" / "scripts"
if str(SHARED_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_SCRIPT_DIR))

# Pure functions only -- no OUT_ROOT/ROOT global touched by importing these.
from build_current_selfaware_behavior_rows import (  # noqa: E402
    behavior_cell,
    stable_row_key,
)

BEHAVIOR_ARM = "clean_sft_grpo_v2_seed2"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def materialize(source_rows_path: Path, scored_rows_path: Path, out_path: Path) -> dict[str, Any]:
    source_rows = load_jsonl(source_rows_path)
    scored_by_key = {stable_row_key(row): row for row in load_jsonl(scored_rows_path)}

    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    cell_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    confidence_values: list[float] = []
    for source in source_rows:
        key = stable_row_key(source)
        scored = scored_by_key.get(key)
        if scored is None:
            missing.append(key)
            continue
        row = dict(source)
        row["row_key"] = key
        if "aliases" in scored:
            row["aliases"] = scored.get("aliases") or []
        if "answer_value" in scored:
            row["answer_value"] = scored.get("answer_value")
        cell = behavior_cell(scored)
        source_arms = dict(row.get("source_arms") or {})
        source_arms[BEHAVIOR_ARM] = {
            "answer_text": scored.get("answer_text"),
            "generated_answer": scored.get("generated_answer"),
            "refused": bool(scored.get("refused")),
            "correct": bool(scored.get("correct")),
            "truthful": bool(scored.get("truthful")),
            "stated_confidence": scored.get("stated_confidence"),
            "behavior_cell": cell,
            "config_sha": scored.get("config_sha"),
            "method": scored.get("method"),
            "model": scored.get("model"),
            "enable_thinking": scored.get("enable_thinking"),
            "generation_attempts": scored.get("generation_attempts"),
            "stated_confidence_retry_count": scored.get("stated_confidence_retry_count"),
            "stated_confidence_retry_exhausted": scored.get("stated_confidence_retry_exhausted"),
        }
        row["source_arms"] = source_arms
        row["behavior_cell"] = cell
        rows.append(row)
        cell_counts[cell] += 1
        label_counts[str(row.get("label"))] += 1
        confidence = scored.get("stated_confidence")
        if confidence is not None:
            confidence_values.append(float(confidence))

    if missing:
        raise ValueError(
            f"{BEHAVIOR_ARM}: missing scored rows for {len(missing)} keys; "
            f"first={missing[:5]} -- RC-G0 join-coverage check FAILS, stop and report"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary = {
        "behavior_arm": BEHAVIOR_ARM,
        "source_rows": str(source_rows_path.resolve().relative_to(ROOT)),
        "scored_rows": str(scored_rows_path.resolve().relative_to(ROOT)),
        "rows": str(out_path.resolve().relative_to(ROOT)),
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "behavior_cell_counts": dict(sorted(cell_counts.items())),
        "mean_stated_confidence": (
            sum(confidence_values) / len(confidence_values) if confidence_values else None
        ),
    }
    summary_path = out_path.with_name("summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-rows", required=True, type=Path,
                    help="seed-2 extraction rows.jsonl (AMENDMENT stage 2 output)")
    p.add_argument("--scored-rows", required=True, type=Path,
                    help="seed-2 SelfAware full eval scored_rows.jsonl (grpo-three-seed-confirmatory)")
    p.add_argument("--out", required=True, type=Path,
                    help="output rows.jsonl path (under this cell's gitignored analysis/)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = materialize(args.source_rows, args.scored_rows, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
