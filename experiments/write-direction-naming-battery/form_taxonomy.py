"""Output-form taxonomy for write-direction-naming-battery Arm A (axis G).

AMENDMENT.md "New instrument: the output-form taxonomy" (the one new module
this cell must build; everything else in the grading stack is reuse). Five
mutually exclusive, jointly exhaustive classes, assigned in priority order so
every generation lands in exactly one:

  F5 degenerate            existing `is_degenerate` (grader.py)
  F4 explicit IDK           existing `semantic_refuse` (gen_lib.py narrow) OR
                            `refused_v2` (detector_v2.py wide)
  F3 non-answerability      NEW: asserts the question cannot be answered, has
                            no determinate answer, or depends on unavailable
                            specifics, WITHOUT an IDK idiom
  F2 hedged assertion       NEW: supplies a candidate answer carrying an
                            explicit epistemic qualifier or scope limitation
  F1 committed assertion    remainder

This module does NOT import grader.py / detector_v2.py and does not
recompute `degenerate` / `semantic_refuse` / `refused_v2` itself. Per
cell.yaml `execution.graders` (`grader:grade`, `detector_v2:grade_one_v2`,
`form_taxonomy:classify`, in that order) and
`.skills/mechinterp-cells/reference/verbs-and-schemas.md` line 136 ("grader
... maps a per-row output dict to a grade dict merged into the row"), this
module runs LAST and reads the fields the first two graders already merged
into the row. That keeps `is_degenerate` / `semantic_refuse` / `refused_v2`
defined in exactly one place each (no drift risk) and makes this module
composable with whichever byte-for-byte port of grader.py/detector_v2.py the
harness build lands on, without a direct import dependency.

The class boundaries were frozen (AMENDMENT.md "Feasibility probe") before
this draft, from a seeded 18-row read: a dosed confab that neither refuses
nor degenerates but asserts "cannot be answered with a single fact because it
depends on specific data" is F3 (no IDK idiom); bare unmarked substitutions
("Kazan", "1900", "York") and confident false biographies are F1.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_PATTERNS_PATH = HERE / "form_patterns.yaml"

# F5 > F4 > F3 > F2 > F1, the exact AMENDMENT.md priority order. Exposed so
# tests (and any downstream aggregation) can assert against the canonical
# order rather than re-typing the five strings.
FORM_CLASSES: tuple[str, ...] = (
    "F5_degenerate",
    "F4_explicit_idk",
    "F3_non_answerability",
    "F2_hedged_assertion",
    "F1_committed_assertion",
)

_CURLY_APOSTROPHE_RE = re.compile("[‘’ʼ]")

_loaded_cache: dict[str, dict[str, Any]] = {}


def _normalize(text: Optional[str]) -> str:
    """Lowercase + fold curly/typographic apostrophes to straight `'`, same
    normalization convention as detector_v2.py's `_normalize`, so a form
    pattern like "i'm not entirely sure" matches both apostrophe styles."""
    return _CURLY_APOSTROPHE_RE.sub("'", (text or "")).lower()


def load_patterns(path: Optional[Path] = None) -> dict[str, Any]:
    p = path or DEFAULT_PATTERNS_PATH
    key = str(p)
    if key not in _loaded_cache:
        with p.open(encoding="utf-8") as fh:
            _loaded_cache[key] = yaml.safe_load(fh)
    return _loaded_cache[key]


def _pattern_entries(config: dict[str, Any], group: str) -> list[dict[str, Any]]:
    return config.get(group, [])


def _first_match(norm_text: str, entries: list[dict[str, Any]]) -> list[str]:
    """Returns every pattern id in `entries` whose regex fires on
    `norm_text` (not just the first), so a row's `form_matched_pattern_ids`
    records the full evidence set for later inspection."""
    hits = []
    for entry in entries:
        if re.search(entry["pattern"], norm_text):
            hits.append(entry["id"])
    return hits


def _scan_text(row: dict[str, Any]) -> str:
    """The JSON `answer` field if the row already carries one (`answer_value`,
    merged in by grader:grade / gen_lib.grade_clean_tighten), else the raw
    generation. Preferring `answer_value` means F2/F3 pattern matching reads
    the model's actual content rather than JSON scaffolding; falling back to
    `answer_text` keeps this module usable on a row that never went through
    gen_lib (e.g. a standalone test fixture)."""
    answer_value = row.get("answer_value")
    if answer_value:
        return str(answer_value)
    return str(row.get("answer_text") or "")


def classify(row: dict[str, Any], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Assigns exactly one of FORM_CLASSES to `row`, in strict F5>F4>F3>F2>F1
    priority: each class is checked in order and returns immediately on a
    hit, so a row that would satisfy more than one class's surface
    description (e.g. degenerate text that also happens to contain an F3
    phrase) always lands in the highest-priority class, structurally, not by
    convention.

    Returns {"form_class": one of FORM_CLASSES, "form_matched_pattern_ids": [...]}.
    `form_matched_pattern_ids` is empty for F5/F4 (those are field checks, not
    pattern checks) and for F1 (the remainder; nothing fired).
    """
    cfg = config if config is not None else load_patterns()

    if bool(row.get("degenerate", False)):
        return {"form_class": "F5_degenerate", "form_matched_pattern_ids": []}

    if bool(row.get("semantic_refuse", False)) or bool(row.get("refused_v2", False)):
        return {"form_class": "F4_explicit_idk", "form_matched_pattern_ids": []}

    norm = _normalize(_scan_text(row))

    f3_hits = _first_match(norm, _pattern_entries(cfg, "f3_non_answerability"))
    if f3_hits:
        return {"form_class": "F3_non_answerability", "form_matched_pattern_ids": f3_hits}

    f2_hits = _first_match(norm, _pattern_entries(cfg, "f2_hedged_assertion"))
    if f2_hits:
        return {"form_class": "F2_hedged_assertion", "form_matched_pattern_ids": f2_hits}

    return {"form_class": "F1_committed_assertion", "form_matched_pattern_ids": []}


def _self_check() -> None:
    cfg = load_patterns()

    degenerate_row = {"answer_text": "", "degenerate": True}
    assert classify(degenerate_row, cfg)["form_class"] == "F5_degenerate"

    idk_row = {
        "answer_text": '{"answer": "I don\'t know"}',
        "degenerate": False,
        "semantic_refuse": True,
        "refused_v2": True,
    }
    assert classify(idk_row, cfg)["form_class"] == "F4_explicit_idk"

    f3_row = {
        "answer_text": '{"answer": "This cannot be answered with a single fact because it depends on specific data."}',
        "answer_value": "This cannot be answered with a single fact because it depends on specific data.",
        "degenerate": False,
        "semantic_refuse": False,
        "refused_v2": False,
    }
    assert classify(f3_row, cfg)["form_class"] == "F3_non_answerability"

    f2_row = {
        "answer_value": "It is probably Kazan.",
        "degenerate": False,
        "semantic_refuse": False,
        "refused_v2": False,
    }
    assert classify(f2_row, cfg)["form_class"] == "F2_hedged_assertion"

    f1_row = {
        "answer_value": "Kazan",
        "degenerate": False,
        "semantic_refuse": False,
        "refused_v2": False,
    }
    assert classify(f1_row, cfg)["form_class"] == "F1_committed_assertion"

    print("form_taxonomy self-check: PASS")


if __name__ == "__main__":
    _self_check()
