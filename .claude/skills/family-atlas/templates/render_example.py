"""Example render module for a family-atlas capture cell.

This is a REFERENCE PATTERN, not a script the capture runner imports
automatically. Copy it into your new experiment directory (e.g. as
`render.py`), then replace `BASELINE_SYSTEM_PROMPT` and the message
construction in `render()` with the EXACT prompt/template logic of whatever
source experiment's row pool and anchor convention you are mapping. Point
`capture_family_atlas_cell.py capture --render-module` at your copy.

Why this can't be a single shared default: the atlas's hidden states are
only comparable to the source experiment's own captures if the rendered
prompt (system prompt, chat-template handling, thinking-off pinning) and the
anchor position are identical to that experiment's own render path. Every
family-atlas cell run so far (llama32_3b_instruct, mistral7b_instruct_v03 in
`experiments/jspace-family-atlas`) ported its source fleet's render.py
verbatim rather than importing across experiment directories, and rather
than using a generic prompt -- do the same for your own source experiment.

Contract this module must honor:
- Read the model repo/revision from `FAMILY_ATLAS_RENDER_MODEL` /
  `FAMILY_ATLAS_RENDER_REVISION`, which `capture_family_atlas_cell.py` sets
  before calling `render()`, if this module needs its own tokenizer identity
  (e.g. for a chat-template thinking-off ladder like the one below).
- Expose a `render(row: dict) -> str` callable. `row` is whatever the
  source row pool's JSONL objects look like; this example assumes a
  `question` field, but adapt to your own pool's schema.
- If your source model can silently honor a `<think>` scaffold even when you
  asked for `enable_thinking=False`, keep an explicit assertion like
  `assert_no_think_scaffolding` below: a silently-honored thinking tag shifts
  the last-prompt-token anchor position relative to the source experiment's
  own anchor, breaking cross-comparability without raising any error.
"""

from __future__ import annotations

import os
import re
import sys


BASELINE_SYSTEM_PROMPT = "REPLACE ME: copy the exact system prompt your source experiment used."

THINK_TAG_MARKERS = ("<think>", "</think>")
EMPTY_THINK_OFF_MARKER_RE = re.compile(r"<think>\s*</think>")


def assert_no_think_scaffolding(rendered_prompt: str, *, model: str) -> None:
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


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_KEY
    model = os.environ.get("FAMILY_ATLAS_RENDER_MODEL")
    if not model:
        raise RuntimeError("FAMILY_ATLAS_RENDER_MODEL must name the HF tokenizer repo")
    revision = os.environ.get("FAMILY_ATLAS_RENDER_REVISION") or None
    key = (model, revision)
    if _TOKENIZER is None or _TOKENIZER_KEY != key:
        from transformers import AutoTokenizer

        _TOKENIZER = AutoTokenizer.from_pretrained(
            model,
            revision=revision,
            token=os.environ.get("HF_TOKEN") or None,
            trust_remote_code=True,
        )
        _TOKENIZER_KEY = key
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
    model = os.environ.get("FAMILY_ATLAS_RENDER_MODEL", "<unset>")
    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        rendered = tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False,
        )
        assert_no_think_scaffolding(rendered, model=model)
        return rendered
    manual = f"System: {BASELINE_SYSTEM_PROMPT}\n\nUser: {question}\n\nAssistant:"
    assert_no_think_scaffolding(manual, model=model)
    return manual
