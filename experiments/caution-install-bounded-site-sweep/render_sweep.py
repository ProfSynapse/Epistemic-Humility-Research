"""Render plug-in for the tuner's `render_fn` contract: `render(row) -> str`.

The tuner resolves `render_fn` as `module:callable` and calls it with only the
row dict (see synaptic-tuner MechInterp/cli.py `_run_one_pass` /
`extract_rows`), so the tokenizer/chat-template must be resolved from process
state rather than an argument. This module lazily loads and caches ONE
tokenizer per substrate, selected by the `SWEEP_SUBSTRATE` environment
variable ("trained" | "raw_base"), which every launch wrapper in this
experiment sets before invoking a tuner verb. A materialized recipe is always
scoped to exactly one substrate (see materialize_configs.py), so this is safe.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sweep_lib import SYSTEM_PROMPT, base_repo_and_revision  # noqa: E402

_TOKENIZER_CACHE: dict[str, object] = {}


def _tokenizer_for(substrate: str):
    if substrate in _TOKENIZER_CACHE:
        return _TOKENIZER_CACHE[substrate]
    from transformers import AutoTokenizer

    repo, revision = base_repo_and_revision(substrate)
    tok = AutoTokenizer.from_pretrained(repo, revision=revision)
    _TOKENIZER_CACHE[substrate] = tok
    return tok


def _current_substrate() -> str:
    sub = os.environ.get("SWEEP_SUBSTRATE")
    if not sub:
        raise RuntimeError(
            "render_sweep.render: SWEEP_SUBSTRATE env var not set. Every launch "
            "wrapper in this experiment must export SWEEP_SUBSTRATE=trained|raw_base "
            "before invoking a tuner verb that uses this render_fn."
        )
    return sub


def render(row: dict) -> str:
    """Map one input row to a rendered prompt string via the Qwen3 chat
    template, enable_thinking=False, matching cell.yaml surface.generation
    and probe_stage_b.py's render() exactly."""
    tokenizer = _tokenizer_for(_current_substrate())
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": str(row.get("question", ""))},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False,
    )


def content_end_fn(full_ids, prompt_len: int, tokenizer) -> int:
    """For `mechinterp extract`'s anchor-only capture, content_end is never
    read to place the anchor position (anchor = prompt_len - 1, independent
    of the completion), but the tuner's `extract_rows` always calls this to
    decide `answered` for its manifest. Returns the last non-EOS generated
    token index, or prompt_len - 1 (no usable content) if nothing was
    generated -- matching the tuner's own "value < prompt_len => no content"
    convention documented in MechInterp/extraction/capture.py."""
    seq_total = int(full_ids.shape[0])
    if seq_total <= prompt_len:
        return prompt_len - 1
    eos_id = getattr(tokenizer, "eos_token_id", None)
    im_end_id = None
    try:
        im_end_id = tokenizer.convert_tokens_to_ids("<|im_end|>")
    except Exception:
        im_end_id = None
    stop_ids = {i for i in (eos_id, im_end_id) if i is not None and i != getattr(tokenizer, "unk_token_id", None)}
    for idx in range(prompt_len, seq_total):
        if int(full_ids[idx]) in stop_ids:
            return max(prompt_len - 1, idx - 1)
    return seq_total - 1
