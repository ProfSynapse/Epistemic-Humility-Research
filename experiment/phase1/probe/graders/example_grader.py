"""Example project grader for a tuner mechinterp steer cell.

NOT a registered instrument. This is the teaching companion to
experiment/phase1/cells/example-cell/. It shows the grader contract the tuner
expects: a callable that maps one per-row output dict to a grade dict, which the
CLI merges back into the row so the declarative gates can read the added fields.

Contract (see synaptic-tuner/docs/MECH_INTERP_CELLS.md, "Plug-in points"):

    grade(row: dict) -> dict

The input row carries at least the fields the steer verb writes:
``row_key``, ``arm``, ``strength``, ``active``, ``answer_text``, ``prompt_len``
(plus any fields carried through from the input rows pool). The returned dict is
merged into the row; gates then read those fields by name.

A real project grader for this research line would apply the abstention /
correctness / degenerate rules from the frozen steering harness
(experiment/phase1/probe/steering/steering_common.py). This example keeps the
logic trivial and dependency-free so the contract is legible.

The grader is byte-pinned per amendment: a signed cell records the sha256 of its
grader file in the amendment doc alongside the cell.yaml and gates.yaml shas.
"""

from __future__ import annotations

# Substrings that mark an abstention / "I don't know" style refusal. A real
# grader would use the project's calibrated abstention classifier.
_ABSTAIN_MARKERS = (
    "i don't know",
    "i do not know",
    "i'm not sure",
    "cannot answer",
    "no answer",
)


def _looks_abstained(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in _ABSTAIN_MARKERS)


def grade(row: dict) -> dict:
    """Map one per-row output to a grade dict merged back into the row."""
    text = str(row.get("answer_text", "")).strip()
    abstained = _looks_abstained(text) or not text
    # "confabulated": produced a substantive answer on a row the design expects
    # the model to abstain on. Here we approximate it as "answered while active".
    confabulated = bool(row.get("active")) and not abstained
    return {
        "abstained": abstained,
        "confabulated": confabulated,
        # gates compare against the baseline arm's per-row value; the baseline
        # pass writes abstained under the same key, so a reach gate can read
        # baseline_abstained after a join step. For this example we simply echo.
        "baseline_abstained": abstained,
    }
