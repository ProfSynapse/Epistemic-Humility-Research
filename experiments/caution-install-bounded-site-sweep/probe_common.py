"""Shared helpers for the caution-install-bounded-site-sweep pre-sign
feasibility probe (Stage A CPU corpus inventory, Stage B GPU role yield).

Tier 3, lab notebook. See feasibility_probe.yaml and NOTEBOOK.md for the
pre-registration this script executes against. Nothing here computes a
steered quantity, a direction fit, a gate AUC, a tau, a tighten rate, or an
AUROC -- the blinding boundary stated in NOTEBOOK.md.

The normalization and grading primitives below are deliberately verbatim
ports (not re-derivations) of the primitives already governing this exact
research line, so the probe's numbers are produced by the same instruments
the rest of the program trusts:

  - `norm_question` / `normalize` / `is_correct`: verbatim from
    experiments/j-space-cross-family-layer-contrast/scorers.py (itself a
    verbatim port of archive/experiment/phase1/eval/scorers.py for the
    question/alias half).
  - `is_stated_confidence_refusal`: verbatim REFUSAL_MARKERS and
    STATED_CONFIDENCE_REFUSAL_PATTERNS from
    archive/experiment/phase1/eval/scorers.py, the Cheng-validated port this
    exact trained lineage's other cells (e.g. dark_actuator_grader.py) reuse
    for JSON stated-confidence answer text.
  - `is_degenerate`: verbatim n-gram-repeat / no-alnum / empty rule from
    experiments/common/graders/dark_actuator_grader.py.
  - `wilson_interval`: the standard Wilson score interval, matching the
    formula in archive/experiment/phase1/eval/analysis/unknown_question_labels/
    category_regimen_analysis.py (z=1.96 for the 95% interval this probe's
    pass criterion is defined in terms of).

`extract_first_json` / `parse_first_json_stated_confidence` are new: they
implement the "first_json" read policy feasibility_probe.yaml asserts
explicitly (grading.read_policy_note) as distinct from a whole-completion
read. The precedent `parse_stated_confidence` in
archive/experiment/phase1/eval/scorers.py requires the ENTIRE trimmed
completion to be exactly one JSON object; first_json instead scans for the
first balanced `{...}` substring and parses only that, so trailing prose
after a well-formed JSON answer does not fail the parse and does not reach
grading -- the distinction the read_policy_note calls out.
"""

from __future__ import annotations

import json
import math
import re
from typing import Optional, Sequence

# --------------------------------------------------------------------------
# Question-text / alias normalization (verbatim port)
# --------------------------------------------------------------------------

HIR_PREFIX = re.compile(
    r"^your current knowledge expression confidence level is [0-9.]+,\s*"
    r"please answer the user's question:\s*"
)


def normalize(text: str) -> str:
    """Answer/alias normalizer: lowercase, keep only [a-z0-9] tokens."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def norm_question(text: str) -> str:
    """Question-text normalizer for gold-key lookup and leakage matching."""
    q = re.sub(r"\s+", " ", text.strip().lower())
    return HIR_PREFIX.sub("", q)


def is_correct(generation: str, aliases: Sequence[str]) -> bool:
    """Word-bounded alias membership. Verbatim port."""
    gen = f" {normalize(generation)} "
    return any(f" {alias} " in gen for alias in aliases)


# --------------------------------------------------------------------------
# Refusal / degenerate detection (verbatim ports)
# --------------------------------------------------------------------------

REFUSAL_MARKERS: tuple[str, ...] = (
    "beyond the scope of my knowledge",
    "i am not sure what the answer is",
    "i don't know the answer",
    "i do not know the answer",
)

STATED_CONFIDENCE_REFUSAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi\s+do\s+not\s+know\b", re.IGNORECASE),
    re.compile(r"\bi\s+don['’]t\s+know\b", re.IGNORECASE),
    re.compile(r"^\s*abstain\b", re.IGNORECASE),
)


def is_refusal(text: str) -> bool:
    t = text.lower()
    return any(m in t for m in REFUSAL_MARKERS)


def is_stated_confidence_refusal(text: str) -> bool:
    return is_refusal(text) or any(
        p.search(text) for p in STATED_CONFIDENCE_REFUSAL_PATTERNS
    )


_MAX_NGRAM = 5
_MIN_REPEATS = 3


def _is_repeated_ngram(tokens: list[str]) -> bool:
    n_tok = len(tokens)
    for n in range(1, _MAX_NGRAM + 1):
        if n_tok < n * _MIN_REPEATS:
            continue
        unit = tokens[:n]
        reps = n_tok // n
        if reps < _MIN_REPEATS:
            continue
        if (all(tokens[i * n:(i + 1) * n] == unit for i in range(reps))
                and tokens[reps * n:] == unit[: n_tok - reps * n]):
            return True
    return False


def is_degenerate(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    if not re.search(r"[a-zA-Z0-9]", stripped):
        return True
    return _is_repeated_ngram(stripped.split())


# --------------------------------------------------------------------------
# first_json read policy
# --------------------------------------------------------------------------

def _coerce_confidence_value(value: object) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    if parsed < 0.0 or parsed > 1.0:
        return None
    return parsed


def extract_first_json(text: str) -> Optional[dict]:
    """Scan for the first balanced top-level `{...}` object and parse only
    that substring. Trailing text after the object is ignored. Returns None
    if no balanced object parses as a JSON object anywhere in the text."""
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        obj = json.loads(candidate)
                    except json.JSONDecodeError:
                        obj = None
                    if isinstance(obj, dict):
                        return obj
                    break
        start = text.find("{", start + 1)
    return None


def parse_first_json_stated_confidence(text: str) -> Optional[str]:
    """Return the extracted `answer` string if the first balanced JSON
    object in `text` is a well-formed stated-confidence payload (exactly the
    keys {"answer", "response_confidence"} or the legacy {"answer",
    "confidence"}, answer a string, confidence a number in [0, 1]).
    Returns None ("not captured") otherwise."""
    payload = extract_first_json(text)
    if not isinstance(payload, dict):
        return None
    keys = set(payload)
    if keys not in ({"answer", "response_confidence"}, {"answer", "confidence"}):
        return None
    answer = payload.get("answer")
    confidence = _coerce_confidence_value(
        payload.get("response_confidence", payload.get("confidence"))
    )
    if isinstance(answer, str) and confidence is not None:
        return answer.strip()
    return None


# --------------------------------------------------------------------------
# Wilson score interval
# --------------------------------------------------------------------------

def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    p_hat = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p_hat + z2 / (2 * n)) / denom
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z2 / (4 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def wilson_lower_95(successes: int, n: int) -> float:
    lo, _hi = wilson_interval(successes, n, z=1.96)
    return lo
