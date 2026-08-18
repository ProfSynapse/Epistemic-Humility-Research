#!/usr/bin/env python3
"""Stage 1 (labels_join, CPU) for base-refusal-direction-under-contract.

Reads the governed retained rows of the resolved prompt-vs-training-panel base
P-rc arm (archive/experiment/phase1/eval/results_prompt_vs_training_panel_prc_4b/
base_prc__selfaware/scored_rows.jsonl, 3369 rows) and emits the known-row subset
with a `behavior_cell` field using the SAME taxonomy as the paper-3 Section 5
lineage (experiments/common/scripts/build_current_selfaware_behavior_rows.py's
`behavior_cell()`, and residual_read_trajectory.py's KNOWN_REFUSED /
KNOWN_ANSWERED="known_correct_answered" constants), so the pinned
residual_caution_direction.py fit script can be invoked UNMODIFIED via CLI.

No fresh generation. CPU-only, no GPU, no model load.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHARED_SCRIPT_DIR = ROOT / "experiments" / "common" / "scripts"
if str(SHARED_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_SCRIPT_DIR))

# Pure functions only, no OUT_ROOT/ROOT global touched by importing these
# (same reuse pattern as experiments/refusal-axis-ablation-confirmatory's
# configs/behavior_rows_build_clean_sft_grpo_v2_seed2.py).
from build_current_selfaware_behavior_rows import (  # noqa: E402
    behavior_cell,
    stable_row_key,
)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def join(scored_rows_path: Path, out_path: Path) -> dict:
    scored_rows = load_jsonl(scored_rows_path)
    out_rows = []
    label_counts: Counter[str] = Counter()
    cell_counts: Counter[str] = Counter()
    for row in scored_rows:
        label = row.get("label")
        label_counts[str(label)] += 1
        if label != "known":
            continue
        cell = behavior_cell(row)
        cell_counts[cell] += 1
        # Only the two contrast classes BR-G0 needs are written to the
        # extraction/fit stream; known_answered_wrong rows are counted above
        # for provenance but excluded (matches the Section 5 ka=correct-only
        # convention residual_caution_direction.py's load_known_split reads).
        if cell not in ("known_refused", "known_correct_answered"):
            continue
        key = stable_row_key(row)
        out_rows.append({
            "row_key": key,
            "probe_pool_row_key": key,
            "question": row["question"],
            "label": label,
            "behavior_cell": cell,
            "refused": bool(row.get("refused")),
            "correct": bool(row.get("correct")),
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in out_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "source": str(scored_rows_path.resolve().relative_to(ROOT)),
        "out": str(out_path.resolve().relative_to(ROOT)),
        "n_total_rows": len(scored_rows),
        "label_counts": dict(sorted(label_counts.items())),
        "known_behavior_cell_counts": dict(sorted(cell_counts.items())),
        "n_written_known_refused": cell_counts.get("known_refused", 0),
        "n_written_known_correct_answered": cell_counts.get("known_correct_answered", 0),
        "n_written_total": len(out_rows),
    }
    summary_path = out_path.with_name("summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored-rows", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    summary = join(args.scored_rows, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
