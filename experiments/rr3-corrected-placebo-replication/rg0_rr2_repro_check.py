#!/usr/bin/env python3
"""RG0 `deterministic_repro_of_rr2_baseline_and_gated_text` check (gates.yaml
line 20): RR3's regenerated mistral core baseline and gated arms must
reproduce RR2's held-out generation text byte-for-byte, keyed by row_key.

This gate was registered at sign but the pipeline did not implement it as an
in-run hard stop (build gap found at lead review, closed by this module). It
is a pure read-only comparison over the two runlogs; a single text mismatch
is a hard FAIL. Baseline compares all rows; gated compares the fired set and
also asserts the fired row_key sets are identical.

Usage: python3 rg0_rr2_repro_check.py
Writes analysis-committed/rg0_rr2_repro_report.json (counts + pass only).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RR2_RUNLOG = Path(
    "/home/profsynapse/code/ehr-worktrees/rr2-mistral-confirm/experiments/"
    "rr2-mistral-adjudicated-refusal-confirm/analysis/runlog"
)
RR3_RUNLOG = HERE / "analysis" / "runlog"

TEXT_FIELD = "answer_text"
KEY_FIELD = "row_key"


def load_by_key(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get(KEY_FIELD) or row.get("key")
            if key is None:
                raise SystemExit(f"{path}: line {i} has no {KEY_FIELD}/key field")
            if key in out:
                raise SystemExit(f"{path}: duplicate key {key!r} at line {i}")
            out[key] = row[TEXT_FIELD]
    return out


def compare(name: str, rr2_path: Path, rr3_path: Path) -> dict:
    rr2 = load_by_key(rr2_path)
    rr3 = load_by_key(rr3_path)
    only_rr2 = sorted(set(rr2) - set(rr3))
    only_rr3 = sorted(set(rr3) - set(rr2))
    mismatches = [k for k in rr2 if k in rr3 and rr2[k] != rr3[k]]
    result = {
        "arm": name,
        "n_rr2": len(rr2),
        "n_rr3": len(rr3),
        "n_only_rr2": len(only_rr2),
        "n_only_rr3": len(only_rr3),
        "n_text_mismatches": len(mismatches),
        "pass": not only_rr2 and not only_rr3 and not mismatches,
    }
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    results = [
        compare("baseline", RR2_RUNLOG / "heldout__baseline.jsonl", RR3_RUNLOG / "core__baseline.jsonl"),
        compare("gated", RR2_RUNLOG / "heldout__gated.jsonl", RR3_RUNLOG / "core__gated.jsonl"),
    ]
    overall = all(r["pass"] for r in results)
    report = {"gate": "rg0.deterministic_repro_of_rr2_baseline_and_gated_text", "arms": results, "pass": overall}
    out = HERE / "analysis-committed" / "rg0_rr2_repro_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[rg0_rr2_repro_check] overall pass={overall} -> {out}")
    if not overall:
        raise SystemExit("RG0 FAIL: RR3 core text does not reproduce RR2 byte-for-byte (hard stop; do NOT dispatch adjudication)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
