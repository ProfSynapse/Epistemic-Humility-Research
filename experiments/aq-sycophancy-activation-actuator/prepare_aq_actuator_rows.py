"""Prepare AQ actuator rows from the frozen r2 row pool.

The raw row pool is the governed source of row identity and behavior labels.
This script only enriches it with readout-screen metadata from
analysis/readout_diagnostics/per_row_scores.csv so the downstream steering
output carries the frozen selector score used for interpretation.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_ROW_POOL = HERE / "analysis" / "row_pool.jsonl"
DEFAULT_SCORES = HERE / "analysis" / "readout_diagnostics" / "per_row_scores.csv"
DEFAULT_OUT = HERE / "analysis" / "actuator_rows.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_scores(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {str(row["row_key"]): row for row in rows}


def maybe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-pool", type=Path, default=DEFAULT_ROW_POOL)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = load_jsonl(args.row_pool)
    scores_by_key = load_scores(args.scores)
    out_rows: list[dict[str, Any]] = []
    n_probe = 0
    n_scored = 0
    for row in rows:
        enriched = dict(row)
        probe_label = row.get("probe_label")
        if probe_label is not None:
            n_probe += 1
            enriched["sycophancy_label"] = int(probe_label)
        else:
            enriched["sycophancy_label"] = None

        score = scores_by_key.get(str(row["row_key"]))
        if score:
            n_scored += 1
            enriched["selector_score"] = maybe_float(score.get("selected_oof_score"))
            enriched["selector_full_score"] = maybe_float(score.get("selected_logistic_score"))
            enriched["selector_condition_resid_score"] = maybe_float(
                score.get("condition_resid_oof_score")
            )
            enriched["selector_paired_delta_score"] = maybe_float(
                score.get("paired_delta_oof_score")
            )
        else:
            enriched["selector_score"] = None
            enriched["selector_full_score"] = None
            enriched["selector_condition_resid_score"] = None
            enriched["selector_paired_delta_score"] = None
        out_rows.append(enriched)

    # The tuner smoke gate probes the first n rows. Put the actuator-selected
    # population first so smoke readback checks real write rows, not natural
    # baseline projection on inactive rows.
    out_rows.sort(
        key=lambda row: (
            not bool(row.get("baseline_wrong_hint_followed")),
            str(row.get("row_key", "")),
        )
    )
    smoke_n = 8
    n_smoke_active = sum(
        1 for row in out_rows[:smoke_n] if bool(row.get("baseline_wrong_hint_followed"))
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for row in out_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    print(
        json.dumps(
            {
                "row_pool": str(args.row_pool),
                "scores": str(args.scores),
                "out": str(args.out),
                "n_rows": len(out_rows),
                "n_probe_rows": n_probe,
                "n_rows_with_selector_scores": n_scored,
                "n_smoke_active_first_8": n_smoke_active,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
