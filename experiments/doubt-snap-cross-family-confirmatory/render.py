"""Cross-family JSON-answer render for the doubt-snap cell.

The prompt contract is the AH/A0 raw-base JSON surface, but the tokenizer must
come from the active model family. Set DOUBT_SNAP_RENDER_MODEL to the HF repo
before invoking `mechinterp steer`; the Modal/materializer pipeline does this
per cell.
"""

from __future__ import annotations

import os


BASELINE_SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON "
    "object with exactly two keys: \"answer\" and \"response_confidence\". "
    "The \"answer\" value is your answer or abstention text. The "
    "\"response_confidence\" value is your probability from 0 to 1 that your "
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)

_TOKENIZER = None
_TOKENIZER_MODEL = None


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_MODEL
    model = os.environ.get("DOUBT_SNAP_RENDER_MODEL")
    if not model:
        raise RuntimeError("DOUBT_SNAP_RENDER_MODEL must name the HF tokenizer repo")
    if _TOKENIZER is None or _TOKENIZER_MODEL != model:
        from transformers import AutoTokenizer

        _TOKENIZER = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
        _TOKENIZER_MODEL = model
    return _TOKENIZER


def render(row: dict) -> str:
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question text")
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tok = _tokenizer()
    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        attempts = [
            {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False},
            {
                "tokenize": False,
                "add_generation_prompt": True,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            {"tokenize": False, "add_generation_prompt": True},
        ]
        for kwargs in attempts:
            try:
                return tok.apply_chat_template(messages, **kwargs)
            except Exception:
                continue
    return f"System: {BASELINE_SYSTEM_PROMPT}\n\nUser: {question}\n\nAssistant:"
