"""Prompt render for gemma-4-e4b-family-atlas anchor capture.

Ported (copied, not imported) from
experiments/doubt-snap-cross-family-confirmatory/render.py so this read-only
mapping experiment never imports across experiment directories. Renders the
same baseline system-prompt + question surface the fleet's `gemma4_e4b_it`
cell would have used for its own baseline generation and anchor capture (that
cell was defined in the fleet's model_matrix.yaml but never launched -- see
AMENDMENT.md "Row pool" for the mining plan), so this atlas's per-row hidden
states stay comparable to the same fleet convention the llama/mistral
jspace-family-atlas cells already used. Only the environment variable names
differ (FAMILY_ATLAS_RENDER_MODEL/REVISION, set by the shared
`.skills/family-atlas/scripts/capture_family_atlas_cell.py` runner, instead
of DOUBT_SNAP_RENDER_MODEL/REVISION) to avoid any cross-experiment env
collision if multiple pipelines ever run in the same process.

Note: jspace-family-atlas's own `render_jspace_atlas.py` used
JSPACE_ATLAS_RENDER_MODEL/REVISION, a cell-specific name -- that module
predates the generalization of `capture_atlas_cell.py` into the shared,
substrate-agnostic `capture_family_atlas_cell.py`, which now sets
FAMILY_ATLAS_RENDER_MODEL/REVISION for every cell (see
`templates/render_example.py`). This module follows the current, shared
contract, not the older per-cell pattern.

This experiment does no generation and no steering at capture time (the
mining stage's own baseline generation is a separate, explicitly-gated step;
see AMENDMENT.md), so the fleet's `assert_no_think_scaffolding` self-check
and its enable_thinking=False fallback ladder are kept unchanged: a
silently-honored thinking tag would still shift the captured anchor position
(the last prompt token) relative to the fleet's own anchor, breaking
cross-comparability. Gemma-4-E4B-it's chat template is not known to emit
`<think>` scaffolding, so this check is expected to be a no-op here, but it
is kept rather than dropped for the same reason jspace-family-atlas kept it
for llama/mistral: uniform protection if a future cell reuses this file.
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

    Ported from the fleet's render.py; see that module's docstring for the
    full rationale.
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
    print(f"[gemma-atlas-render] {model}: {detail}", file=sys.stderr, flush=True)


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
