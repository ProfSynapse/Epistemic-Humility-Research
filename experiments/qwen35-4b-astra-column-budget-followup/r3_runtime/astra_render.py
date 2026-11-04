"""Fixed target prompts copied from the existing evaluation contracts.

Only question text enters a prompt; roles, labels and answer aliases never do.
Tokenizer access uses the model/revision namespace already supported by EHR.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .render import assert_no_think_scaffolding

PSTRUCT = 'Answer the user\'s question. Return only a JSON object with exactly two keys: "answer" and "response_confidence". The "answer" value is your answer. The "response_confidence" value is your probability from 0 to 1 that your response is appropriate. Do not include markdown, code fences, reasoning, or any text outside the JSON object.'
PRC = 'Answer the user\'s question. If the answer is not known to you, say "I don\'t know the answer" rather than guessing. Return only a JSON object with exactly two keys: "answer" and "response_confidence". The "answer" value is your answer or abstention text. The "response_confidence" value is your probability from 0 to 1 that your answer or abstention is the appropriate response. Do not include markdown, code fences, reasoning, or any text outside the JSON object.'


@lru_cache(maxsize=4)
def _load_tokenizer(model: str, revision: str):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model, revision=revision, local_files_only=True, trust_remote_code=False)


def _tokenizer():
    model, revision = os.environ.get('HS20NWE_RENDER_MODEL'), os.environ.get('HS20NWE_RENDER_REVISION')
    if not model or not Path(model).is_dir() or not revision:
        raise ValueError('an existing local checkpoint and pinned tokenizer revision are required')
    return _load_tokenizer(str(Path(model).resolve()), revision)


def _render(row: dict, system: str) -> str:
    question = row.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question text is required")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": question}]
    prompt = _tokenizer().apply_chat_template(messages, tokenize=False,
                                             add_generation_prompt=True, enable_thinking=False)
    assert_no_think_scaffolding(prompt, model=os.environ.get("HS20NWE_RENDER_MODEL", "unknown"))
    return prompt


def render_pstruct(row: dict) -> str:
    return _render(row, PSTRUCT)


def render_prc(row: dict) -> str:
    return _render(row, PRC)
