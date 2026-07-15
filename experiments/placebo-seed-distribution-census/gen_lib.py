"""Generation-side grading helpers for placebo-seed-distribution-census.

Simplified relative to rr3-corrected-placebo-replication/gen_lib.py: this
census's `final_rate_rule` is `detector_v2_refused OR adjudicated_abstention`
only (cell.yaml `wide_instrument.adjudication.final_rate_rule`; gates.yaml
`detector_v2_only_rates: reported alongside every wide rate for continuity`),
with no locked v1-detector continuity requirement pinned anywhere in this
experiment's governed docs (unlike RR3, which carried v1 forward from RR/RR2
for cross-experiment comparability). `grade_row` therefore merges only the
`detector_v2` sub-grade, not a v1 merge.
"""

from __future__ import annotations

from typing import Optional

import detector_v2

MAX_NEW_CAP = 200


def resolve_eos_ids(tokenizer) -> list[int]:
    ids = set()
    if tokenizer.eos_token_id is not None:
        ids.add(int(tokenizer.eos_token_id))
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if im_end is not None and im_end != getattr(tokenizer, "unk_token_id", None):
        ids.add(int(im_end))
    return sorted(ids)


def grade_row(text: str, terminated_naturally: bool, aliases: Optional[list[str]]) -> dict:
    """detector_v2 sub-grade (refused_v2, well_formed_correct_v2, degenerate,
    matched_pattern_ids) plus generation-shape fields, one dict per row, per
    the data-exhaust build-time rule (full sub-grade persisted, not a
    collapsed boolean, so this row-level run log is directly usable by
    build_pool.py's detector-v2 screen without any re-generation)."""
    v2 = detector_v2.grade_one_v2(text, aliases)
    return {
        "terminated_naturally": terminated_naturally,
        **v2,
    }
