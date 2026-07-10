"""Correctness scoring primitives for the Phase 1 knowledge probe (WS-1).

Location: experiment/phase1/probe/scoring.py
Used by:  experiment/phase1/probe/probe.py to compute P_correct per question.

These primitives are RE-IMPLEMENTED (not imported) from the read-only
meta-analysis/analysis/reanalyze_idk_outputs.py so that the probe carries no
dependency on the meta-analysis package and the paper-1 source stays
untouched. The normalization and word-bounded alias-membership logic match
that source exactly so the probe's correctness labels are comparable to the
Cheng-validated scorer used downstream by the WS-4 eval harness.

There are intentionally TWO normalizers, mirroring the source:
  - normalize_answer: alphanumeric-token join, used for alias membership.
  - normalize_question: whitespace-collapse + lowercase, used to key a
    question's normalized form (the same key the leakage guard and gold
    files use: re.sub(r"\\s+", " ", s.strip().lower())).
"""

from __future__ import annotations

import re


def normalize_answer(text: str) -> str:
    """Lowercase and join alphanumeric tokens with single spaces.

    Mirrors reanalyze_idk_outputs.normalize. Punctuation and extra
    whitespace are dropped so alias membership is robust to formatting.
    """
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def normalize_question(text: str) -> str:
    """Collapse whitespace and lowercase a question string.

    Mirrors the key used by cheng_test_gold.jsonl and
    reanalyze_idk_outputs.norm_question (sans the HIR-prefix strip, which is
    specific to that source's outputs and irrelevant to the bare probe
    questions here). This is the form the WS-2 leakage guard compares.
    """
    return re.sub(r"\s+", " ", text.strip().lower())


def is_correct(generation: str, aliases: list[str]) -> bool:
    """Word-bounded membership of any normalized gold alias in the generation.

    Mirrors reanalyze_idk_outputs.is_correct: pad both sides with spaces so a
    match is on whole normalized tokens, not substrings (so "milton" does not
    match inside "miltonic"). Empty aliases never match.
    """
    gen = f" {normalize_answer(generation)} "
    return any(f" {alias} " in gen for alias in aliases if alias)


def p_correct(sampled_correct: list[bool]) -> float:
    """Fraction of stochastic samples that were correct.

    Returns 0.0 for an empty sample list (defensive; the probe always passes a
    non-empty list in normal operation).
    """
    if not sampled_correct:
        return 0.0
    return sum(1 for c in sampled_correct if c) / len(sampled_correct)
