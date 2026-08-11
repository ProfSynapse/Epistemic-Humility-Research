"""Render function for the ood-breadth-beyond-selfaware internal-panel
extraction (experiments/ood-breadth-beyond-selfaware/extract_A1.yaml,
extract_A4.yaml).

Contract (`.skills/mechinterp-cells/reference/verbs-and-schemas.md`,
"Project plug-ins"):

    render(row: dict) -> str
    content_end(full_ids, prompt_len, tokenizer) -> int

`MechInterp/cli.py::run_extract` calls `render_fn(row)` with ONLY the row dict
(no tokenizer injected -- see `extraction/capture.py::extract_rows`, `prompt =
render_fn(row)`), so this module loads its own tokenizer, lazily and once,
cached at module scope, exactly as the base model's tokenizer.

PARITY WITH THE BEHAVIOR-PANEL EVAL (why this hand-writes the chat-template
call rather than reusing a broken prior precedent): the internal-panel read is
only meaningful if the "generation position" activation is read from the SAME
prompt the model actually sees during the behavior-panel eval. This module
therefore reproduces `archive/experiment/phase1/eval/run_eval.py`'s
`VLLMGenerator._apply_chat_template` / `_render_prompt` logic verbatim
(system + user message, `enable_thinking=False`, the direct/
chat_template_kwargs fallback, and the no-think-scaffolding assertion) rather
than importing it, since `run_eval.py` is not designed as a library import (it
pulls in `scorers`/`stats` at module scope) and an EARLIER render_fn in this
tree (`experiments/common/renders/ai_true_render.py`) references
`archive/experiment/phase1/probe/backends.py`, which does not exist in this
checkout -- that precedent is stale and is not reused here.

System prompt is the SAME verbatim JSON answer + response_confidence contract
cell.yaml `rendering_and_scoring.carried_over_unchanged.system_prompt` pins for
the behavior panel (`archive/experiment/phase1/eval/config/
eval_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_local_4b.yaml`
`prompt.system`), copied here as a literal string (not read from that YAML at
runtime) so this module has no import-time dependency on the eval config tree.

Tokenizer resolution: the internal panel runs on A1 (clean-SFT merged base)
and A4 (same base + GRPO-v2 LoRA, cell.yaml `arms.A4.base: same_as_A1`); an
adapter does not retrain tokenization, so both arms share one tokenizer. This
module defaults to A1's base checkpoint path. Override with the
`OOD_BREADTH_RENDER_TOKENIZER_PATH` environment variable if a run environment
does not have that exact local path staged.

`content_end`: the internal panel reads ONLY the `anchor` position family (the
last PROMPT token, pre-generation -- cell.yaml `internal_panel.read_position:
generation_position`). `MechInterp/extraction/capture.py::extract_rows`
requires a >=1-token completion before it will run the forward pass and save
ANY family's tensors (its `answered = content_end >= prompt_len` gate), so
`extract.yaml` sets `max_new_tokens: 1` and this function always reports the
row as answered (`content_end = prompt_len`). This is a mechanical
satisfaction of that gate, not real generation: causal attention means the
anchor position's (`prompt_len - 1`) hidden state depends only on tokens
`0..prompt_len-1`, so it is unaffected by whatever the nominal one generated
token turns out to be.
"""

from __future__ import annotations

import os
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "experiments").is_dir() and (candidate / "archive").is_dir():
            return candidate
    raise RuntimeError(f"could not locate repository root from {here}")


CANONICAL = _repo_root()
DEFAULT_TOKENIZER_PATH = str(
    CANONICAL
    / "scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/"
    "20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit"
)

# Verbatim from eval_amendment_e_..._full_local_4b.yaml `prompt.system`
# (cell.yaml rendering_and_scoring.carried_over_unchanged.system_prompt).
SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    '"I don\'t know the answer" rather than guessing. Return only a JSON '
    'object with exactly two keys: "answer" and "response_confidence". The '
    '"answer" value is your answer or abstention text. The '
    '"response_confidence" value is your probability from 0 to 1 that your '
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)

THINK_TAG_MARKERS = ("<think>", "</think>")

_tokenizer = None
_chat_template_mode: str | None = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer

        path = os.environ.get("OOD_BREADTH_RENDER_TOKENIZER_PATH", DEFAULT_TOKENIZER_PATH)
        _tokenizer = AutoTokenizer.from_pretrained(path)
    return _tokenizer


def _assert_no_think_scaffolding(rendered_prompt: str) -> None:
    import re

    empty_off_marker_re = re.compile(r"<think>\s*</think>")
    rendered_without_empty_off_markers = empty_off_marker_re.sub("", rendered_prompt)
    for marker in THINK_TAG_MARKERS:
        if marker in rendered_without_empty_off_markers:
            raise RuntimeError(
                "enable_thinking=False was requested but the rendered prompt "
                f"contains thinking marker {marker!r}; aborting before extraction "
                "activations are contaminated (parity with run_eval.py "
                "assert_no_think_scaffolding)."
            )


def _apply_chat_template(tokenizer, messages: list[dict[str, str]], mode: str) -> str:
    template_kwargs = {"tokenize": False, "add_generation_prompt": True}
    if mode == "direct":
        template_kwargs["enable_thinking"] = False
    elif mode == "chat_template_kwargs":
        template_kwargs["chat_template_kwargs"] = {"enable_thinking": False}
    else:
        raise ValueError(f"unknown chat template mode: {mode!r}")
    return tokenizer.apply_chat_template(messages, **template_kwargs)


def render(row: dict) -> str:
    """Map one internal-panel row (row_key/question/label, see
    screen_ood_surfaces.py:build_internal_panel_pool) to the same prompt
    string the behavior-panel eval renders for this question, thinking off.
    """
    global _chat_template_mode
    tokenizer = _get_tokenizer()
    question = str(row.get("question", "")).strip()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    if _chat_template_mode is not None:
        rendered = _apply_chat_template(tokenizer, messages, _chat_template_mode)
        _assert_no_think_scaffolding(rendered)
        return rendered

    failures: list[str] = []
    for mode in ("direct", "chat_template_kwargs"):
        try:
            rendered = _apply_chat_template(tokenizer, messages, mode)
            _assert_no_think_scaffolding(rendered)
        except TypeError as exc:
            failures.append(f"{mode}: tokenizer rejected kwargs ({exc})")
            continue
        except RuntimeError as exc:
            failures.append(f"{mode}: {exc}")
            continue
        _chat_template_mode = mode
        return rendered

    detail = "; ".join(failures) if failures else "no render attempts made"
    raise RuntimeError(
        "Unable to render a Qwen3 prompt with thinking off. Tried both direct "
        f"enable_thinking and chat_template_kwargs wiring. Details: {detail}."
    )


def content_end(full_ids, prompt_len: int, tokenizer) -> int:
    """Always report the row as answered so the anchor (pre-generation)
    position gets captured; see module docstring's `content_end` section for
    why this is a mechanical gate satisfaction, not a real content read.
    """
    del full_ids, tokenizer  # unused: anchor position needs no completion text
    return int(prompt_len)
