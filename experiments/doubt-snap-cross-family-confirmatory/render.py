"""Cross-family JSON-answer render for the doubt-snap cell.

The prompt contract is the AH/A0 raw-base JSON surface, but the tokenizer must
come from the active model family. Set DOUBT_SNAP_RENDER_MODEL to the HF repo
before invoking `mechinterp steer`; the Modal/materializer pipeline does this
per cell.

Pre-launch hygiene fix (2026-07-10 anchor-audit finding; see NOTEBOOK.md):
ported the exploratory pipeline's `assert_no_think_scaffolding` self-check
(experiments/common/knowledge_probe/backends.py) so a chat template that
silently ignores the thinking-off pin fails instead of contaminating rows,
and made every chat-template kwarg fallback log explicitly instead of being
swallowed by a bare `except Exception: continue`.
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

# Ported (logic, not import) from
# experiments/common/knowledge_probe/backends.py's THINK_TAG_MARKERS /
# EMPTY_THINK_OFF_MARKER_RE / assert_no_think_scaffolding. The markers are
# Qwen3.5's literal thinking-tag strings; the other panel families (Llama,
# Ministral, Gemma) never emit them, so this check is a no-op there and a
# hard stop only for a Qwen3.5 thinking-off leak.
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
    """Log a chat-template fallback exactly once per (model, mode).

    render() is called once per row, so without de-duplication this would
    print the same fallback thousands of times per cell.
    """
    key = (model, mode)
    if key in _LOGGED_FALLBACKS:
        return
    _LOGGED_FALLBACKS.add(key)
    print(f"[doubt-snap-render] {model}: {detail}", file=sys.stderr, flush=True)


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_KEY
    model = os.environ.get("DOUBT_SNAP_RENDER_MODEL")
    if not model:
        raise RuntimeError("DOUBT_SNAP_RENDER_MODEL must name the HF tokenizer repo")
    revision = os.environ.get("DOUBT_SNAP_RENDER_REVISION") or None
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
    model = os.environ.get("DOUBT_SNAP_RENDER_MODEL", "<unset>")
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
