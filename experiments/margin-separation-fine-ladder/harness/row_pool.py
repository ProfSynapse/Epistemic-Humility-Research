"""Question-text lookup for margin-separation-fine-ladder (M1b), qwen35_4b
ONLY.

Reads ONLY the SC0-staged inputs (analysis/staged_inputs/, gitignored). No
GPU, no model. This module never writes question/answer text to a committed
path (containment rule). Trimmed from `margin-mapping/row_pool.py` (read in
full before writing this) to the ONE thing M1b's own build phase needs:
row_key -> question text, for the refined-53 population (preflight rows,
rg0_drift_check rows, and eventually the 212-generation run). M1b has no
dose-0 baseline rung and no fresh known-row generation, so
`baseline_text_pool`/`heldout_row_keys_by_role` (M1's own full-population
census helpers) are not ported -- this experiment's population is already
fixed by `staging.py`'s refined-subset derivation, not derived fresh here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402

STAGED = HERE.parent / "analysis" / "staged_inputs"

_QUESTION_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "heldout_rows_for_steer.jsonl",
}


def question_pool(family: str) -> dict[str, dict[str, Any]]:
    """row_key -> {question, aliases, category_canon, source, role} for every
    HELD-OUT row in the family's private question pool. PRIVATE (contains
    question text); callers must keep this in gitignored analysis/, never
    write it to analysis-committed/."""
    path = _QUESTION_SOURCE[family]
    out: dict[str, dict[str, Any]] = {}
    for r in common.load_jsonl(path):
        if r.get("split") != "held_out":
            continue
        if r.get("role") not in ("confab", "known_correct_answered"):
            continue
        out[r["row_key"]] = {
            "question": r.get("question"), "aliases": r.get("aliases", []),
            "category_canon": r.get("category_canon"), "source": r.get("source"),
            "role": r.get("role"),
        }
    return out
