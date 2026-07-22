"""Per-family paired confab pool + question-text join for
placebo-seed-distribution-census.

Reads ONLY the SC0-staged inputs (analysis/staged_inputs/, gitignored). No
GPU, no model. Defines, per family, the exact "paired confab pool" cell.yaml
names (qwen 1286, mistral 1312, llama 872) and joins row_key -> question/
aliases from the family's own private row-text source, needed to render
prompts at generation time. This module NEVER writes question/answer text to
a committed path (containment rule).

Population definitions, verified against on-disk staged artifacts (see
NOTEBOOK.md-equivalent commentary in staging.py and this module's own
docstring here):

  qwen35_4b   paired = row_key present in BOTH baseline.jsonl AND
              random_direction.jsonl (QH's own gated random-direction pass),
              role=confab, split=held_out. Baseline alone has 1332 confab
              held_out rows; the random_direction pass only covers the
              doubt-gate's FIRED subset (1286), and the calibration's -5.13
              historical delta was measured on exactly that 1286-row
              intersection (calibration AMENDMENT lines 173, 176, 235-236: "46
              unpaired baseline confabs ... reported separately, never inside
              a delta"). The census draws its S=300 subsample from this SAME
              1286-row paired population, matching where the historical value
              was measured, per AMENDMENT.md "Per-seed subsample".
  mistral7b_v03   paired = baseline.jsonl role=confab, split=held_out (1312
              rows, exact match to cell.yaml's paired_confab_pool_n; RR2's
              baseline and random_direction arms cover the identical
              unconditional held-out population, no gate).
  llama32_3b  paired = baseline.jsonl (RR3's rider_llama__baseline.jsonl)
              role=confab, split=held_out (872 rows, exact match to
              cell.yaml's heldout_confab_pool).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

STAGED = HERE / "analysis" / "staged_inputs"


def _confab_held_out_keys(path: Path) -> set[str]:
    return {
        r["row_key"] for r in common.load_jsonl(path)
        if r.get("role") == "confab" and r.get("split") == "held_out"
    }


def paired_confab_row_keys(family: str) -> list[str]:
    """Sorted (deterministic) list of row_keys in the family's paired confab
    pool. Sorted so any downstream permutation draw depends only on (seed,
    row_key content), never process/OS iteration order."""
    if family == "qwen35_4b":
        baseline_keys = _confab_held_out_keys(STAGED / "qwen35_4b" / "baseline.jsonl")
        random_keys = _confab_held_out_keys(STAGED / "qwen35_4b" / "random_direction.jsonl")
        keys = baseline_keys & random_keys
    elif family == "mistral7b_v03":
        keys = _confab_held_out_keys(STAGED / "mistral7b_v03" / "baseline.jsonl")
    elif family == "llama32_3b":
        keys = _confab_held_out_keys(STAGED / "llama32_3b" / "baseline.jsonl")
    else:
        raise ValueError(f"unknown family {family!r}")
    expected = config.PAIRED_CONFAB_POOL_N[family]
    if len(keys) != expected:
        raise SystemExit(
            f"paired_confab_row_keys FAIL ({family}): computed {len(keys)} paired "
            f"confab rows, cell.yaml registers {expected}. Population definition "
            f"does not reproduce the registered count; do not proceed."
        )
    return sorted(keys)


_QUESTION_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "heldout_rows_for_steer.jsonl",
    "mistral7b_v03": STAGED / "mistral7b_v03" / "joined_rows_private.jsonl",
    "llama32_3b": STAGED / "llama32_3b" / "joined_rows_private.jsonl",
}

_BASELINE_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "baseline.jsonl",
    "mistral7b_v03": STAGED / "mistral7b_v03" / "baseline.jsonl",
    "llama32_3b": STAGED / "llama32_3b" / "baseline.jsonl",
}


def question_pool(family: str) -> dict[str, dict[str, Any]]:
    """row_key -> {question, aliases, category_canon, source} for every row
    in the family's private row-text pool. PRIVATE (contains question text);
    callers must keep this in gitignored analysis/, never write it to
    analysis-committed/."""
    path = _QUESTION_SOURCE[family]
    out: dict[str, dict[str, Any]] = {}
    for r in common.load_jsonl(path):
        out[r["row_key"]] = {
            "question": r.get("question"),
            "aliases": r.get("aliases", []),
            "category_canon": r.get("category_canon"),
            "source": r.get("source"),
        }
    return out


def baseline_text_pool(family: str) -> dict[str, dict[str, Any]]:
    """row_key -> full baseline generation record (answer_text +
    detector_v2-shape fields already present on qwen/llama's runlogs; mistral's
    RR2 runlog carries a slightly different grade schema -- rows are
    RE-GRADED under this census's OWN gen_lib.grade_row at baseline-reuse
    time, this pool exists only for the RG0 byte-repro TEXT check and to
    source `answer_text`)."""
    path = _BASELINE_SOURCE[family]
    return {r["row_key"]: r for r in common.load_jsonl(path)}
