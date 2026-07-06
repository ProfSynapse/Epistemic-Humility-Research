"""Grader for the AO propensity-regulated-caution cell.

STUB -- NOT a real grader. This raises NotImplementedError until it is ported
from the frozen steering harness. Documented here rather than silently
returning plausible-looking fields, per the "do not invent numbers" rule: a
placeholder that fabricated refused/correct flags would be worse than one that
fails loudly, since a fabricated grade could leak into a gates.yaml readout
undetected.

Contract (see synaptic-tuner/docs/MECH_INTERP_CELLS.md, "Plug-in points" and
experiments/common/graders/example_grader.py for the worked teaching example):

    grade(row: dict) -> dict

The input row carries at least ``row_key``, ``arm``, ``strength``, ``active``,
``answer_text``, ``prompt_len`` (the fields MechInterp.cli.run_steer writes),
plus whatever the rows pool carried through (``cell``, ``prop_z``, and
whatever gold-answer/label field correctness needs).

What a real port needs to reproduce, from
``experiment/phase1/probe/steering/steering_common.py`` (frozen; same
convention as the AL A0 cell per the AMENDMENT's Design section: "Same system
prompt, greedy decoding, and grader as the AL A0 cell"):

  - refusal / abstention detection on ``answer_text`` (the harness's
    calibrated classifier, not a substring heuristic -- see
    ``experiments/common/graders/example_grader.py`` for why a substring
    heuristic is only a teaching stub).
  - correctness scoring against the row's gold answer for cells where
    correctness is meaningful (known_correct_answered, and any de-refused row
    in confab/answerable_refused after an arm's intervention).
  - a per-row ``baseline_refused`` / ``baseline_correct`` join so gates can
    compute per-arm deltas without a separate baseline lookup pass (the
    AL/AN convention; see amendment_al_grade_and_gates.py for the pattern).

The AMENDMENT's gates (gates.yaml in this directory) expect, per graded row:
``refused`` (bool), ``correct`` (bool), ``cell`` (one of "confab",
"answerable_refused", "known_correct_answered", carried through from the rows
pool), and ``row_key`` for cross-arm pairing.
"""

from __future__ import annotations


def grade(row: dict) -> dict:
    raise NotImplementedError(
        "ao_grader.grade is a documented placeholder (Stage-0 prep remaining): "
        "port refusal/correctness detection from "
        "experiment/phase1/probe/steering/steering_common.py before running "
        "this cell for real. See the module docstring for exactly what is "
        "missing. row_key=" + str(row.get("row_key"))
    )
