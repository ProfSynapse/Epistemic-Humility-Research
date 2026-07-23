"""Per-family held-out population + question-text join for
gate-contribution-factorial.

Reads ONLY the SC0-staged inputs (analysis/staged_inputs/, gitignored). No
GPU, no model. This module never writes question/answer text to a committed
path (containment rule).

Population definitions, verified against on-disk staged artifacts:

  qwen35_4b   the private steer-row pool (`heldout_rows_for_steer.jsonl`) is
              ALREADY exactly the held-out pool (1692 rows, all split ==
              "held_out"; no fit rows mixed in): 1332 confab + 360
              known_correct_answered, matching cell.yaml
              `families.qwen35_4b.heldout_pool`.
  mistral7b_v03  the private pool (`joined_rows_private.jsonl`) mixes FIT
              (874 confab-fit + 255 known-fit + 214 unknown_refused) and
              HELD_OUT rows; this experiment filters role in
              {confab, known_correct_answered} AND split == "held_out",
              yielding 1312 confab + 382 known, matching cell.yaml
              `families.mistral7b_v03.heldout_pool`.
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

_QUESTION_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "heldout_rows_for_steer.jsonl",
    "mistral7b_v03": STAGED / "mistral7b_v03" / "joined_rows_private.jsonl",
}

_BASELINE_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "baseline.jsonl",
    "mistral7b_v03": STAGED / "mistral7b_v03" / "baseline.jsonl",
}

_GATED_SOURCE = {
    "qwen35_4b": STAGED / "qwen35_4b" / "gated.jsonl",
    "mistral7b_v03": STAGED / "mistral7b_v03" / "gated.jsonl",
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
    experiment's own gen_lib.grade_row so every arm shares one lane."""
    path = _BASELINE_SOURCE[family]
    return {r["row_key"]: r for r in common.load_jsonl(path)}


def gated_text_pool(family: str) -> dict[str, dict[str, Any]]:
    """row_key -> the true_gate__c_hat fired-rows-only generation record
    (qwen: 1303 rows fired at tau_frozen; mistral: RR2's own 1303 confab
    rows, 0 known, RR2 lines 142/151)."""
    path = _GATED_SOURCE[family]
    return {r["row_key"]: r for r in common.load_jsonl(path)}


def heldout_row_keys_by_role(family: str) -> dict[str, list[str]]:
    """Sorted (deterministic) row_keys per role, from the question pool
    (which is already filtered to split == held_out)."""
    qpool = question_pool(family)
    confab = sorted(rk for rk, r in qpool.items() if r["role"] == "confab")
    known = sorted(rk for rk, r in qpool.items() if r["role"] == "known_correct_answered")
    expected = config.HELDOUT_POOL[family]
    if len(confab) != expected["confab"] or len(known) != expected["known_correct_answered"]:
        raise SystemExit(
            f"heldout_row_keys_by_role FAIL ({family}): computed confab={len(confab)} "
            f"known={len(known)}, cell.yaml registers confab={expected['confab']} "
            f"known={expected['known_correct_answered']}. Population definition does "
            f"not reproduce the registered counts; do not proceed."
        )
    return {"confab": confab, "known_correct_answered": known}


def heldout_rows_for_steer_file_order(family: str) -> list[str]:
    """The EXACT file order of the family's private steer-row pool (needed
    for `gate_construction.qwen_permuted_gate_row_keys`, which reproduces
    midband-heldout's own permuted-gate index draw over its own row order)."""
    path = _QUESTION_SOURCE[family]
    out = []
    for r in common.load_jsonl(path):
        if r.get("split") == "held_out" and r.get("role") in ("confab", "known_correct_answered"):
            out.append(r["row_key"])
    return out
