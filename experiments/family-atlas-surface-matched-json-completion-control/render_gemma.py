"""Experiment-owned Gemma renderer port used by generation and capture."""

from __future__ import annotations

import re

SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON "
    "object with exactly two keys: \"answer\" and \"response_confidence\". "
    "The \"answer\" value is your answer or abstention text. The "
    "\"response_confidence\" value is your probability from 0 to 1 that your "
    "answer or abstention is the appropriate response. Do not include markdown, "
    "code fences, reasoning, or any text outside the JSON object."
)


def _assert_thinking_off(prompt: str) -> None:
    cleaned = re.sub(r"<think>\s*</think>", "", prompt)
    if "<think>" in cleaned or "</think>" in cleaned:
        raise RuntimeError("Gemma renderer produced populated or unbalanced thinking scaffolding")


def render_with_tokenizer(tokenizer, row: dict) -> str:
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question text")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        attempts = [
            {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False},
            {"tokenize": False, "add_generation_prompt": True, "chat_template_kwargs": {"enable_thinking": False}},
            {"tokenize": False, "add_generation_prompt": True},
        ]
        for kwargs in attempts:
            try:
                prompt = tokenizer.apply_chat_template(messages, **kwargs)
                _assert_thinking_off(prompt)
                return prompt
            except (TypeError, RuntimeError):
                continue
    prompt = f"System: {SYSTEM_PROMPT}\n\nUser: {question}\n\nAssistant:"
    _assert_thinking_off(prompt)
    return prompt
