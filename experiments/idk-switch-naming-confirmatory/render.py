"""Cross-family JSON-answer render for idk-switch-naming-confirmatory.

Ported (logic, not cross-experiment import, per this repo's convention) from
`experiments/write-direction-naming-battery/render.py` (source sha256
6230655a91b9c94d4b380d710f29304e433d0075aff5ac100d3f3c4e1e5639c7, matching
that file's own pin), itself ported from
`experiments/qwen35-4b-midband-heldout/render.py` and
`experiments/doubt-snap-cross-family-confirmatory/render.py`. This cell's
AMENDMENT.md pins "the naming battery's pinned operating point"
(BASELINE_SYSTEM_PROMPT, the anchor position prompt_len - 1 matched by the
chat template's own `add_generation_prompt=True` placement, and the
thinking-off self-check) unchanged. Only the environment variable names are
renamed to this experiment's own namespace (ISNC_RENDER_MODEL /
ISNC_RENDER_REVISION, "ISNC" = idk-switch-naming-confirmatory) so this cell's
render cache can never collide with the naming battery's or any other
cell's if ever imported in the same process.
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
    key = (model, mode)
    if key in _LOGGED_FALLBACKS:
        return
    _LOGGED_FALLBACKS.add(key)
    print(f"[isnc-render] {model}: {detail}", file=sys.stderr, flush=True)


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_KEY
    model = os.environ.get("ISNC_RENDER_MODEL")
    if not model:
        raise RuntimeError("ISNC_RENDER_MODEL must name the HF tokenizer repo")
    revision = os.environ.get("ISNC_RENDER_REVISION") or None
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
    model = os.environ.get("ISNC_RENDER_MODEL", "<unset>")
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
