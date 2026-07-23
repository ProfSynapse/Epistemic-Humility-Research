"""Per-family held-out population + question-text join for margin-mapping
(M1).

Reads ONLY the SC0-staged inputs (analysis/staged_inputs/, gitignored). No
GPU, no model. This module never writes question/answer text to a committed
path (containment rule). Adapted (logic ported) from
`gate-contribution-factorial/row_pool.py` (read in full before writing
this): M1 has no gate, so there is no `gated_text_pool`/fired-rows join --
only the question pool (for rendering) and the baseline pool (the dose-0
rung, reused byte-identically per cell.yaml `ladder.dose_zero_rung`).

Population definitions are IDENTICAL to the factorial's (M1 reuses the
factorial's own held-out pools byte-identically, cell.yaml `pools`):

  qwen35_4b       1332 confab + 360 known_correct_answered (all split ==
                  "held_out", no fit rows mixed in).
  mistral7b_v03   1312 confab + 382 known, filtered from the private pool
                  (which also mixes FIT rows) by role in {confab,
                  known_correct_answered} AND split == "held_out".
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

STAGED = HERE.parent / "analysis" / "staged_inputs"

_QUESTION_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "heldout_rows_for_steer.jsonl",
    "mistral7b_v03": STAGED / "mistral7b_v03" / "joined_rows_private.jsonl",
}

_BASELINE_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "baseline.jsonl",
    "mistral7b_v03": STAGED / "mistral7b_v03" / "baseline.jsonl",
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


def baseline_text_pool(family: str) -> dict[str, dict[str, Any]]:
    """row_key -> full baseline generation record (answer_text + detector_v2-
    shape fields). Reused for text (RG0), re-graded fresh under this
    experiment's own gen_lib.grade_row so this pool's dose-0 rung shares one
    lane with every dosed rung."""
    path = _BASELINE_SOURCE[family]
    return {r["row_key"]: r for r in common.load_jsonl(path)}


def heldout_row_keys_by_role(family: str) -> dict[str, list[str]]:
    """Sorted (deterministic) row_keys per role, from the question pool
    (which is already filtered to split == held_out)."""
    qpool = question_pool(family)
    confab = sorted(rk for rk, r in qpool.items() if r["role"] == "confab")
    known = sorted(rk for rk, r in qpool.items() if r["role"] == "known_correct_answered")
    expected = config.POOLS[family]
    if len(confab) != expected["confab_full"] or len(known) != expected["known_full"]:
        raise SystemExit(
            f"heldout_row_keys_by_role FAIL ({family}): computed confab={len(confab)} "
            f"known={len(known)}, cell.yaml registers confab_full={expected['confab_full']} "
            f"known_full={expected['known_full']}. Population definition does "
            f"not reproduce the registered counts; do not proceed."
        )
    return {"confab": confab, "known_correct_answered": known}
