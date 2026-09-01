#!/usr/bin/env python3
"""Aggregate the resolved cell's two-stage held-out confab abstention counts
into a committed summary JSON (counts and rates only; no row text).

Two-stage rule (the cell's registered instrument): a held-out confab row
counts as abstention if the pinned detector_v2 refused it at stage 1, or the
sharded judge lane adjudicated it refused_final at stage 2. The local
adjudication_applied.jsonl lanes hold exactly the judge-adjudicated rows
(the detector-negative remainder), so per arm:

    two_stage_refused = judged_refused + (heldout_n - judged_n)

because every held-out row absent from the judge lane was a stage-1 detector
refusal. Held-out denominators come from the frozen parent split manifests
recorded in NOTEBOOK.md (qwen3-4b 185, qwen3.5-4b 1332, llama-3.2-3b 872,
mistral-7b-v0.3 1312, gemma-4-e4b 168 confab rows).

Every derived number is asserted against the governed AMENDMENT.md Outcome
before writing; a mismatch raises instead of committing drift. Reads the
gitignored analysis/ lanes, writes only the aggregate JSON into
analysis-committed/. Deterministic, CPU-only, no network. Regenerate with:

    python3 experiments/no-abstention-prompt-gated-replication/build_two_stage_summary.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
OUT = HERE / "analysis-committed" / "two_stage_family_summary.json"

# Judge lane of record per family (v2 where the first pass was voided) and
# the frozen held-out confab denominator from the parent split manifests
# (NOTEBOOK.md "Frozen held-out pool checks").
FAMILIES = {
    "qwen3-4b": {"lane": "qwen3-4b/v2", "heldout_confab_n": 185},
    "qwen3.5-4b": {"lane": "qwen3.5-4b/v2", "heldout_confab_n": 1332},
    "llama-3.2-3b": {"lane": "llama-3.2-3b/v2", "heldout_confab_n": 872},
    "mistral-7b-v0.3": {"lane": "mistral-7b-v0.3", "heldout_confab_n": 1312},
    "gemma-4-e4b": {"lane": "gemma-4-e4b/v2", "heldout_confab_n": 168},
}

# Governed AMENDMENT.md Outcome two-stage counts (no_op, gated) on held-out
# confabs; the assertion targets, never the source of the written values.
AMENDMENT_COUNTS = {
    "qwen3-4b": {"no_op": 0, "gated": 21},
    "qwen3.5-4b": {"no_op": 118, "gated": 725},
    "llama-3.2-3b": {"no_op": 36, "gated": 117},
    "mistral-7b-v0.3": {"no_op": 151, "gated": 398},
    "gemma-4-e4b": {"no_op": 31, "gated": 110},
}


def main() -> None:
    summary: dict[str, dict] = {}
    for fam, spec in FAMILIES.items():
        lane_path = ANALYSIS / spec["lane"] / "adjudication_applied.jsonl"
        judged_n: dict[str, int] = {}
        judged_refused: dict[str, int] = {}
        with lane_path.open() as fh:
            for line in fh:
                row = json.loads(line)
                if row.get("role") != "confab":
                    continue
                arm = row["arm"]
                judged_n[arm] = judged_n.get(arm, 0) + 1
                if row.get("refused_final"):
                    judged_refused[arm] = judged_refused.get(arm, 0) + 1
        n = spec["heldout_confab_n"]
        fam_out: dict[str, dict] = {}
        for arm in ("no_op", "gated"):
            detector_stage1 = n - judged_n[arm]
            assert detector_stage1 >= 0, (fam, arm, judged_n[arm], n)
            refused = judged_refused.get(arm, 0) + detector_stage1
            assert refused == AMENDMENT_COUNTS[fam][arm], (
                f"{fam}/{arm}: derived {refused} != governed "
                f"{AMENDMENT_COUNTS[fam][arm]}"
            )
            fam_out[arm] = {
                "heldout_confab_n": n,
                "judged_n": judged_n[arm],
                "judged_refused": judged_refused.get(arm, 0),
                "detector_stage1_refused": detector_stage1,
                "two_stage_refused": refused,
                "two_stage_rate": round(refused / n, 6),
            }
        summary[fam] = {"lane": spec["lane"], "arms": fam_out}
    OUT.write_text(
        json.dumps(
            {
                "description": (
                    "Two-stage held-out confab abstention counts per family "
                    "and arm, derived from the judge lanes of record plus "
                    "stage-1 detector refusals; asserted against the "
                    "governed AMENDMENT.md Outcome at build time."
                ),
                "generator": "build_two_stage_summary.py",
                "families": summary,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
