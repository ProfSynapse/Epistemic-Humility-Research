"""Experiment-owned Qwen3 renderer port used by generation and capture."""

from __future__ import annotations

import re

from render_gemma import SYSTEM_PROMPT


def render_with_tokenizer(tokenizer, row: dict) -> str:
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question text")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    cleaned = re.sub(r"<think>\s*</think>", "", prompt)
    if "<think>" in cleaned or "</think>" in cleaned:
        raise RuntimeError("Qwen renderer produced populated or unbalanced thinking scaffolding")
    return prompt
