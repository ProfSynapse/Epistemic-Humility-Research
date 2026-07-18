"""JSON-answer render for margin-evidence-responsiveness-worldknown (M4-WK).

Ported (logic) byte-identical to `margin-mapping/harness/render.py` /
`susceptibility-as-probe/harness/render.py` (both read in full before writing
this) for the system prompt, thinking-off self-check, and chat-template
fallback ladder. Only the environment variable names are namespaced to THIS
experiment (M4WK_RENDER_MODEL / M4WK_RENDER_REVISION) so this render cache
can never collide with any sibling experiment's own render module in the
same process.

NEW relative to the M1/M2 lineage: `render()` accepts an optional `context`
string, injected as `"[Context: the answer is {context}.]\n{question}"`
BEFORE the question in the user message (cell.yaml `arms`: context injected
before the question so the len-1 capture anchor -- len(token_ids)-1 on the
fully rendered prompt, i.e. the position immediately before generation
begins -- stays the SAME structural position relative to the question in
ALL THREE arms; injecting earlier in the prompt does not move it). No other
change to the prompt contract.
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
    """Fail if a rendered prompt contains populated/unbalanced thinking
    (enable_thinking=False pin, reused from the M1/M2/M4 generation stack)."""
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
    print(f"[m4wk-render] {model}: {detail}", file=sys.stderr, flush=True)


def _tokenizer():
    global _TOKENIZER, _TOKENIZER_KEY
    model = os.environ.get("M4WK_RENDER_MODEL")
    if not model:
        raise RuntimeError("M4WK_RENDER_MODEL must name the HF tokenizer repo")
    revision = os.environ.get("M4WK_RENDER_REVISION") or None
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


def build_user_content(question: str, context: str | None) -> str:
    if context is None:
        return question
    return f"[Context: the answer is {context}.]\n{question}"


def render(row: dict) -> str:
    question = row.get("question")
    if not question:
        raise KeyError(f"row {row.get('row_key')!r} has no question text")
    user_content = build_user_content(question, row.get("context"))
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    tok = _tokenizer()
    model = os.environ.get("M4WK_RENDER_MODEL", "<unset>")
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
