"""Prompt render for qwen35-4b-family-atlas anchor capture.

Ported (copied, not imported) from this cell's SOURCE POOL experiment,
`doubt-snap-cross-family-confirmatory` (its own `render.py`), so this
read-only mapping experiment never imports across experiment directories and
never depends on that module changing under it. This atlas captures over the
doubt-snap `qwen35_4b` cell's committed split manifest, so its anchor position
must reproduce that experiment's own render surface EXACTLY -- hence this port
is from `doubt-snap-cross-family-confirmatory/render.py`, NOT from
`render_qwen3_atlas.py` (a different substrate's render). The rendered surface
is the identical AH/A0 raw-base JSON system prompt + chat-template +
thinking-off contract the doubt-snap fleet used for its own qwen35_4b anchor
capture, so this atlas's full-depth captures are directly comparable to that
experiment's own capture at the same anchor position.

Only the environment variable names differ from the source module: this
module reads FAMILY_ATLAS_RENDER_MODEL / FAMILY_ATLAS_RENDER_REVISION (the
names the shared `capture_family_atlas_cell.py` exports from `cell.yaml`, same
contract as `render_qwen3_atlas.py` and `render_gemma_atlas.py`), with
DOUBT_SNAP_RENDER_MODEL / DOUBT_SNAP_RENDER_REVISION retained as a fallback for
standalone smoke use that mirrors the source module's own variable names.

This experiment does no generation and no steering, so the source experiment's
thinking-off contract is kept unchanged: a silently honored thinking tag would
shift the captured anchor position (the last prompt token) relative to the
source experiment's own anchor, breaking cross-comparability. The source
module's three-attempt thinking-off surface (direct enable_thinking=False ->
chat_template_kwargs -> no_thinking_kwarg -> manual template) is preserved
verbatim; on Qwen/Qwen3.5-4B's chat template the `direct` path is expected to
succeed (the template carries a `{%- if enable_thinking is defined and
enable_thinking is false %}` guard that injects an empty `<think>\n\n</think>`
block; verified 2026-07-09 against the checkpoint's chat_template.jinja, see
experiments/j-space-cross-family-layer-contrast/families/qwen35-4b.yaml), and
`assert_no_think_scaffolding` hard-stops any thinking-off leak before rows are
contaminated.
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

# Ported (logic, not import) from doubt-snap-cross-family-confirmatory/render.py
# (itself ported from experiments/common/knowledge_probe/backends.py). The
# markers are Qwen3.5's literal thinking-tag strings; a hard stop only fires on
# a thinking-off leak.
THINK_TAG_MARKERS = ("<think>", "</think>")
EMPTY_THINK_OFF_MARKER_RE = re.compile(r"<think>\s*</think>")


def assert_no_think_scaffolding(rendered_prompt: str, *, model: str) -> None:
    """Fail if a rendered prompt contains populated/unbalanced thinking.

    A live ``<think>...</think>`` marker with content, or an unclosed
    ``<think>`` tag, means the chat template did not honor the
    enable_thinking=False pin. An empty ``<think>\\n\\n</think>`` marker is
    Qwen3.5's normal thinking-off signature and is allowed.
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
    """Log a chat-template fallback exactly once per (model, mode)."""
    key = (model, mode)
    if key in _LOGGED_FALLBACKS:
        return
    _LOGGED_FALLBACKS.add(key)
    print(f"[qwen35-atlas-render] {model}: {detail}", file=sys.stderr, flush=True)


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_KEY
    model = os.environ.get("FAMILY_ATLAS_RENDER_MODEL") or os.environ.get(
        "DOUBT_SNAP_RENDER_MODEL"
    )
    if not model:
        raise RuntimeError(
            "FAMILY_ATLAS_RENDER_MODEL (set by capture_family_atlas_cell.py from"
            " cell.yaml) or DOUBT_SNAP_RENDER_MODEL must name the HF tokenizer repo"
        )
    revision = (
        os.environ.get("FAMILY_ATLAS_RENDER_REVISION")
        or os.environ.get("DOUBT_SNAP_RENDER_REVISION")
        or None
    )
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
    """Map one row (carrying at least a `question` field) to its AH/A0-style
    prompt string, byte-identical to
    `doubt-snap-cross-family-confirmatory/render.py`'s own render()."""
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question text")
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tok = _tokenizer()
    model = os.environ.get("FAMILY_ATLAS_RENDER_MODEL") or os.environ.get(
        "DOUBT_SNAP_RENDER_MODEL", "<unset>"
    )
    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        attempts = [
            ("direct", {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False}),
            ("chat_template_kwargs", {
                "tokenize": False,
                "add_generation_prompt": True,
                "chat_template_kwargs": {"enable_thinking": False},
            }),
            ("no_thinking_kwarg", {"tokenize": False, "add_generation_prompt": True}),
        ]
        failures: list[str] = []
        for mode_name, kwargs in attempts:
            try:
                rendered = tok.apply_chat_template(messages, **kwargs)
                assert_no_think_scaffolding(rendered, model=model)
            except (TypeError, RuntimeError) as exc:
                failures.append(f"{mode_name}: {exc}")
                continue
            if mode_name != "direct":
                _log_fallback_once(
                    model, mode_name,
                    f"preferred 'direct enable_thinking=False' surface was "
                    f"rejected or unclean, using {mode_name!r} instead "
                    f"(prior attempts: {'; '.join(failures) if failures else 'none'})",
                )
            return rendered
        _log_fallback_once(
            model, "manual_template",
            f"every chat-template thinking-off surface failed "
            f"({'; '.join(failures)}); falling back to the manual "
            "System/User/Assistant template",
        )
    manual = f"System: {BASELINE_SYSTEM_PROMPT}\n\nUser: {question}\n\nAssistant:"
    assert_no_think_scaffolding(manual, model=model)
    return manual
