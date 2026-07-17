"""Verbalized-confidence elicitation render for susceptibility-as-probe (M2).

cell.yaml `channels.verbalized_confidence`: "one greedy pass per row,
baseline system prompt unchanged"; the user turn is the SAME question as
`render.py`'s capture channel, with the registered
`template_user_suffix` appended after it (Decision record item 2, wording
frozen at sign). Everything else (chat-template thinking-off handling,
manual-template fallback, anchor/self-check discipline) is ported
byte-identical from `render.py` -- only the user-message construction
differs. Uses its own env-var namespace (M2_ELICIT_RENDER_MODEL /
M2_ELICIT_RENDER_REVISION) and its own tokenizer cache so it can never
collide with the capture channel's render module in the same process.
"""

from __future__ import annotations

import os
import re
import sys

from render import BASELINE_SYSTEM_PROMPT, THINK_TAG_MARKERS, EMPTY_THINK_OFF_MARKER_RE  # noqa: E402

CONFIDENCE_TEMPLATE_USER_SUFFIX = (
    'Before answering, output your confidence that you can answer this '
    'question correctly as the first line, in exactly this format '
    '"CONFIDENCE <integer 0-100>". Then answer the question.'
)


def assert_no_think_scaffolding(rendered_prompt: str, *, model: str) -> None:
    without_empty_off_markers = EMPTY_THINK_OFF_MARKER_RE.sub("", rendered_prompt)
    for marker in THINK_TAG_MARKERS:
        if marker in without_empty_off_markers:
            raise RuntimeError(
                f"enable_thinking=False was requested but the elicitation "
                f"prompt rendered for model {model!r} contains a non-empty "
                f"or unbalanced thinking marker {marker!r}. Aborting before "
                f"this cell's rows are contaminated."
            )


_TOKENIZER = None
_TOKENIZER_KEY = None
_LOGGED_FALLBACKS: set[tuple[str, str]] = set()


def _log_fallback_once(model: str, mode: str, detail: str) -> None:
    key = (model, mode)
    if key in _LOGGED_FALLBACKS:
        return
    _LOGGED_FALLBACKS.add(key)
    print(f"[m2-elicit-render] {model}: {detail}", file=sys.stderr, flush=True)


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_KEY
    model = os.environ.get("M2_ELICIT_RENDER_MODEL")
    if not model:
        raise RuntimeError("M2_ELICIT_RENDER_MODEL must name the HF tokenizer repo")
    revision = os.environ.get("M2_ELICIT_RENDER_REVISION") or None
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
    user_content = f"{question}\n\n{CONFIDENCE_TEMPLATE_USER_SUFFIX}"
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    tok = _tokenizer()
    model = os.environ.get("M2_ELICIT_RENDER_MODEL", "<unset>")
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
    manual = f"System: {BASELINE_SYSTEM_PROMPT}\n\nUser: {user_content}\n\nAssistant:"
    assert_no_think_scaffolding(manual, model=model)
    return manual
