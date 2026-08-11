"""Render functions for flavor-atlas-gemma-pt-confirmatory.

Two surfaces, PRIMARY and CONTROL, per the lead's "Amendment Y base-mode
k-shot render rule" adjudication (AMENDMENT.md "Render" section). This is
the reverse of the draft's original default: base-mode k-shot is PRIMARY
(all G1-G5 readings), the chat-template surface is the descriptive G6
control on a 1800-row subsample only.

Neither function needs a `content_end` companion: this cell's extraction
runs through `extract_anchor_gemma.py` (a plain forward-only anchor
capture, `prompt_len - 1`), not the `mechinterp extract` verb's
render_fn/content_end contract (`MechInterp/extraction/capture.py`), which
is PROHIBITED on this substrate (gates.yaml gg1_kv_seam_admissibility).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# PRIMARY: base-mode k-shot completion surface.
#
# Vendored BYTE-IDENTICAL from experiments/common/readouts/
# amendment_x_cross_model_extract.py's `_BASE_MODE_FEWSHOT` /
# `build_base_mode_prompt` (Amendment Y section 6's registered base-mode
# prompting-surface rule for pretrain-only bases). Reusing the same fixed
# exemplar block, rather than inventing a new one for Gemma, is what makes
# this "the" registered base-mode surface rather than a fresh one; the
# leakage rule (exemplars are hand-written and NOT drawn from PopQA,
# TriviaQA, SelfAware, or KUQ) carries over unchanged since none of this
# cell's panels overlap those exemplar questions either.
# ---------------------------------------------------------------------------

_BASE_MODE_FEWSHOT: tuple[tuple[str, str], ...] = (
    ("What is the largest planet in our solar system?", "Jupiter"),
    ("How many sides does a hexagon have?", "Six"),
    ("What is the chemical symbol for gold?", "Au"),
    ("In what year did the Second World War end?", "1945"),
    ("What is the tallest mountain on Earth?", "Mount Everest"),
)


def build_base_mode_prompt(question: str) -> str:
    """Fixed k-shot QA completion block, vendored byte-identical from
    amendment_x_cross_model_extract.py::build_base_mode_prompt. No chat
    template, no system prompt. Each exemplar is "Q: <question>\\nA:
    <answer>\\n\\n"; the target is "Q: <question>\\nA:" with no trailing
    content, so the anchor position (prompt_len - 1) is the ':' of the
    final answer cue.
    """
    block = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in _BASE_MODE_FEWSHOT)
    return f"{block}Q: {question}\nA:"


def base_mode_kshot_sha() -> str:
    """Stable sha of the exact rendered k-shot exemplar block (target-
    independent), so a run record can prove which prompting surface a cell
    used. Byte-identical value to the upstream module's own
    base_mode_kshot_sha() since the exemplar block is unchanged."""
    block = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in _BASE_MODE_FEWSHOT)
    return hashlib.sha256(block.encode("utf-8")).hexdigest()[:16]


def render_primary_kshot(row: dict) -> str:
    """PRIMARY render: base-mode k-shot completion surface for the pt base.
    `row` needs only a "question" key (this cell's panel schema)."""
    question = str(row.get("question", "")).strip()
    return build_base_mode_prompt(question)


# ---------------------------------------------------------------------------
# CONTROL (descriptive, G6 only): chat-template surface.
#
# Applies the google/gemma-4-E4B-it chat template to the pt base (pt and it
# share a tokenizer; post-training does not retrain tokenization), with the
# SAME verbatim system prompt the Qwen atlas's render carries
# (ood_breadth_response_confidence_render.SYSTEM_PROMPT), so a Gemma-vs-Qwen
# render comparison isolates the template mechanics rather than also
# varying the system prompt.
# ---------------------------------------------------------------------------

# Verbatim from experiments/common/renders/ood_breadth_response_confidence_render.py
SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    '"I don\'t know the answer" rather than guessing. Return only a JSON '
    'object with exactly two keys: "answer" and "response_confidence". The '
    '"answer" value is your answer or abstention text. The '
    '"response_confidence" value is your probability from 0 to 1 that your '
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)

DEFAULT_CHAT_TOKENIZER_REPO = "google/gemma-4-E4B-it"

_chat_tokenizer = None


def _get_chat_tokenizer():
    global _chat_tokenizer
    if _chat_tokenizer is None:
        from transformers import AutoTokenizer

        repo = os.environ.get(
            "GEMMA_CONFIRMATORY_CHAT_TOKENIZER_PATH", DEFAULT_CHAT_TOKENIZER_REPO
        )
        _chat_tokenizer = AutoTokenizer.from_pretrained(repo)
    return _chat_tokenizer


def render_control_chat(row: dict) -> str:
    """CONTROL render (descriptive G6 only): chat-template surface on the
    pt base via the it sibling's tokenizer/template."""
    tokenizer = _get_chat_tokenizer()
    question = str(row.get("question", "")).strip()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


# ---------------------------------------------------------------------------
# Deterministic dual-render subsample selection (1800 rows: 200 unknown per
# KUQ flavor + 600 KUQ known, fixed seed, deterministic ordering).
# ---------------------------------------------------------------------------

DUAL_RENDER_SEED = 20260810
DUAL_RENDER_UNKNOWN_PER_FLAVOR = 200
DUAL_RENDER_KNOWN_TOTAL = 600

KUQ_CATEGORIES = [
    "ambiguous",
    "controversial",
    "counterfactual",
    "false assumption",
    "future unknown",
    "unsolved problem",
]


def select_dual_render_subsample(kuq_panel_rows: list[dict]) -> list[dict]:
    """Deterministic 1800-row subsample of the KUQ panel: 200 unknown rows
    per flavor (all six KUQ categories) + 600 known rows, fixed seed,
    stable sort by row_key before sampling so the selection is reproducible
    independent of input row order.
    """
    import random

    rng = random.Random(DUAL_RENDER_SEED)
    by_flavor: dict[str, list[dict]] = {c: [] for c in KUQ_CATEGORIES}
    known_rows: list[dict] = []
    for r in kuq_panel_rows:
        if r["label"] == "known":
            known_rows.append(r)
        elif r["flavor"] in by_flavor:
            by_flavor[r["flavor"]].append(r)

    known_rows = sorted(known_rows, key=lambda r: r["row_key"])
    selected: list[dict] = []
    for cat in KUQ_CATEGORIES:
        rows = sorted(by_flavor[cat], key=lambda r: r["row_key"])
        if len(rows) < DUAL_RENDER_UNKNOWN_PER_FLAVOR:
            raise ValueError(
                f"flavor '{cat}' has {len(rows)} rows, need "
                f"{DUAL_RENDER_UNKNOWN_PER_FLAVOR}"
            )
        selected.extend(rng.sample(rows, DUAL_RENDER_UNKNOWN_PER_FLAVOR))
    if len(known_rows) < DUAL_RENDER_KNOWN_TOTAL:
        raise ValueError(
            f"known pool has {len(known_rows)} rows, need {DUAL_RENDER_KNOWN_TOTAL}"
        )
    selected.extend(rng.sample(known_rows, DUAL_RENDER_KNOWN_TOTAL))
    selected.sort(key=lambda r: r["row_key"])
    expected = DUAL_RENDER_UNKNOWN_PER_FLAVOR * len(KUQ_CATEGORIES) + DUAL_RENDER_KNOWN_TOTAL
    if len(selected) != expected:
        raise AssertionError(f"expected {expected} rows, got {len(selected)}")
    return selected
