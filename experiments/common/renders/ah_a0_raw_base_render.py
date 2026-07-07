"""Render function for the two-signal caution-regulation eval pool
(`experiments/two-signal-caution-regulation-instruct/analysis/
eval_pool_both_tail.jsonl` -- LOCAL, gitignored, materialized by
`materialize_eval_pool.py` from the committed derived-columns-only manifest +
HF-fetched question text; see that experiment's PROVENANCE.md), a
reconstruction of the AH A0 raw-base surface (checkpoint_tag "raw-base",
`unsloth/Qwen3-4B` FULL BF16 as of the 2026-07-07 substrate pivot -- was
`unsloth/Qwen3-4B-bnb-4bit`, no adapter, no prime).

Unlike the AK Stage-1 raw-base pool (`ak_stage1_raw_base_render.py`), this
pool's MATERIALIZED rows carry `question` text directly (joined in by
materialize_eval_pool.py), so no cross-pool join is needed HERE. This module
only re-applies the AH A0 arm's own system prompt and chat template,
byte-identically.

Contract (see synaptic-tuner MechInterp docs, "Plug-in points"):
    render(row: dict) -> str

System prompt is the AH A0 baseline_system_prompt (verified byte-identical to
`experiment/phase1/probe/analysis/ah_main/manifest.json`'s
`arms.A0.baseline_system_prompt` -- see
`two-signal-caution-regulation-instruct/extract_l34_anchor.py` for the same
verification against `amendment_ah_stage0_extract.load_baseline_system_prompt`),
hardcoded here so this module has no import-time dependency on the canonical
checkout's gitignored analysis tree (only the materialized eval pool itself
needs to exist for a real run -- run `materialize_eval_pool.py` first).

Tokenizer vocab/chat template is identical between the 4-bit and bf16
`unsloth/Qwen3-4B*` repos; `_MODEL_NAME` below is updated to the bf16 repo id
purely for provenance clarity, not because the rendered prompt string
differs.
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
    """Map one eval_pool_both_tail.jsonl row to its AH-A0-style prompt string."""
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
