"""Prompt render for qwen3-4b-family-atlas anchor capture.

Ported (copied, not imported) from this cell's source experiment,
`doubt-gated-caution-tighten` (via the shared
`experiments/common/renders/ah_a0_raw_base_render.py` module it itself
imports, `model_lib.py`), so this read-only mapping experiment never imports
across experiment directories and never depends on the shared render module
changing under it. Renders the identical AH-A0 baseline system prompt +
chat-template + thinking-off pin the source experiment used for its own L34
anchor extraction, so this atlas's full-depth captures are directly
comparable to the source experiment's own single-layer capture at the same
anchor position. Only the environment variable names differ: the module
reads FAMILY_ATLAS_RENDER_MODEL/REVISION (the names the shared
capture_family_atlas_cell.py exports from cell.yaml, same contract as
render_gemma_atlas.py), with QWEN3_ATLAS_RENDER_MODEL/REVISION retained as
a fallback for standalone smoke use. Signed revision 1 (2026-07-21) wired
in the FAMILY_ATLAS_* names; the rendered surface is unchanged.

This experiment does no generation and no steering, so the source
experiment's `enable_thinking=False` pin is kept unchanged; a silently
honored thinking tag would shift the captured anchor position (the last
prompt token) relative to the source experiment's own anchor, breaking
cross-comparability. Unlike `jspace-family-atlas`'s render module, the
source experiment (`doubt-gated-caution-tighten`) never needed an explicit
`assert_no_think_scaffolding` guard (unsloth/Qwen3-4B's own chat template
honors enable_thinking=False cleanly on this surface, per the source
experiment's own committed run history) -- the guard is kept here anyway,
byte-identical to the sibling atlas cells' own copies, as defense in depth
for a family this skill has not previously atlased.
"""

from __future__ import annotations

import os
import re
import sys


BASELINE_SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON "
    "object with exactly two keys: \"answer\" and \"response_confidence\". "
    "The \"answer\" value is your answer or abstention text. The "
    "\"response_confidence\" value is your probability from 0 to 1 that your "
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)

THINK_TAG_MARKERS = ("<think>", "</think>")
EMPTY_THINK_OFF_MARKER_RE = re.compile(r"<think>\s*</think>")


def assert_no_think_scaffolding(rendered_prompt: str, *, model: str) -> None:
    """Fail if a rendered prompt contains populated/unbalanced thinking.

    Ported from `jspace-family-atlas/render_jspace_atlas.py`; see that
    module's docstring for the full rationale.
    """
    without_empty_off_markers = EMPTY_THINK_OFF_MARKER_RE.sub("", rendered_prompt)
    for marker in THINK_TAG_MARKERS:
        if marker in without_empty_off_markers:
            raise RuntimeError(
                f"enable_thinking=False was requested but the prompt rendered "
                f"for model {model!r} contains a non-empty or unbalanced "
                f"thinking marker {marker!r}. The chat template is NOT "
                f"honoring the thinking-off pin; aborting before this cell's "
                f"rows are contaminated."
            )


_TOKENIZER = None
_TOKENIZER_KEY = None
_LOGGED_FALLBACKS: set[tuple[str, str]] = set()


def _log_fallback_once(model: str, mode: str, detail: str) -> None:
    key = (model, mode)
    if key in _LOGGED_FALLBACKS:
        return
    _LOGGED_FALLBACKS.add(key)
    print(f"[qwen3-atlas-render] {model}: {detail}", file=sys.stderr, flush=True)


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_KEY
    model = os.environ.get("FAMILY_ATLAS_RENDER_MODEL") or os.environ.get(
        "QWEN3_ATLAS_RENDER_MODEL"
    )
    if not model:
        raise RuntimeError(
            "FAMILY_ATLAS_RENDER_MODEL (set by capture_family_atlas_cell.py from"
            " cell.yaml) or QWEN3_ATLAS_RENDER_MODEL must name the HF tokenizer repo"
        )
    revision = (
        os.environ.get("FAMILY_ATLAS_RENDER_REVISION")
        or os.environ.get("QWEN3_ATLAS_RENDER_REVISION")
        or None
    )
    key = (model, revision)
    if _TOKENIZER is None or _TOKENIZER_KEY != key:
        from transformers import AutoTokenizer

        _TOKENIZER = AutoTokenizer.from_pretrained(
            model,
            revision=revision,
            token=os.environ.get("HF_TOKEN") or None,
        )
        _TOKENIZER_KEY = key
    return _TOKENIZER


def render(row: dict) -> str:
    """Map one row (carrying at least a `question` field) to its AH-A0-style
    prompt string, byte-identical to
    `experiments/common/renders/ah_a0_raw_base_render.py`'s own render()."""
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question text")
    model = os.environ.get("QWEN3_ATLAS_RENDER_MODEL", "<unset>")
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    rendered = _tokenizer().apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    assert_no_think_scaffolding(rendered, model=model)
    return rendered
