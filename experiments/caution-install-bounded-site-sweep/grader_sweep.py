"""Grader plug-in for the tuner's `grader` contract: `grader(row) -> dict`.

Called by `MechInterp.cli.run_steer` / `run_dose_calibration` after each
generated row, with the row dict the pass produced (carries `answer_text`,
`n_new_tokens`, `terminated_naturally`, plus every pool-row field passed
through, including `label`/`aliases`/`role`/`fire`). Returns the grade dict
merged back into the row, which is what lands in the output JSONL that
`adjudicate_gates.py` reads.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sweep_lib import grade_clean_tighten, is_correct, is_degenerate  # noqa: E402


def grader(row: dict) -> dict:
    text = row.get("answer_text", "") or ""
    terminated_naturally = bool(row.get("terminated_naturally", False))
    ct = grade_clean_tighten(text, terminated_naturally)

    aliases = row.get("aliases", [])
    answer_value = ct.get("answer_value")
    well_formed_correct = bool(
        ct["well_formed"] and answer_value and not ct["degenerate"]
        and is_correct(answer_value, aliases)
    )
    return {
        **ct,
        "well_formed_correct": well_formed_correct,
        "not_well_formed_correct": not well_formed_correct,
    }
