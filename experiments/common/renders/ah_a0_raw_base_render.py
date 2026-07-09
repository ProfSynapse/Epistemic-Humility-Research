"""Render function for the AH A0 raw-base surface (checkpoint_tag "raw-base",
`unsloth/Qwen3-4B` full bf16, no adapter, no prime).

Ported byte-identically (system prompt string, chat-template call, contract)
from `two-signal-caution-regulation-instruct`'s own
`experiments/common/renders/ah_a0_raw_base_render.py` (worktree
`/home/profsynapse/code/ehr-worktrees/two-signal`, branch
`exp/two-signal-caution-regulation-instruct`, as of commit 8f277410) into this
shared `experiments/common/renders/` location, since that sibling branch is
not yet merged and this experiment (`doubt-gated-caution-tighten`) needs the
same render on the SAME surface (AH A0 / AK Stage-1 raw-base rows, same
baseline system prompt) without a cross-worktree import dependency. If the
sibling branch merges later, both experiments point at this one file (the
project's promotion-rule convention for shared renders).

Contract (see synaptic-tuner MechInterp docs, "Plug-in points"):
    render(row: dict) -> str

System prompt is the AH A0 baseline_system_prompt, verified byte-identical to
`experiment/phase1/probe/analysis/ah_main/manifest.json`'s
`arms.A0.baseline_system_prompt` (see this repo's
`experiment/phase1/probe/amendment_ah_stage0_extract.py` compatibility wrapper
for the archived AH implementation's `load_baseline_system_prompt` canonical
source), hardcoded here so this module has no import-time dependency on the
canonical checkout's gitignored analysis tree.
"""

from __future__ import annotations

BASELINE_SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON "
    "object with exactly two keys: \"answer\" and \"response_confidence\". "
    "The \"answer\" value is your answer or abstention text. The "
    "\"response_confidence\" value is your probability from 0 to 1 that your "
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)

_MODEL_NAME = "unsloth/Qwen3-4B"
_TOKENIZER = None


def _tokenizer():
    global _TOKENIZER
    if _TOKENIZER is None:
        from transformers import AutoTokenizer

        _TOKENIZER = AutoTokenizer.from_pretrained(_MODEL_NAME)
    return _TOKENIZER


def render(row: dict) -> str:
    """Map one row (carrying at least a `question` field) to its AH-A0-style
    prompt string."""
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question text")
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    return _tokenizer().apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
