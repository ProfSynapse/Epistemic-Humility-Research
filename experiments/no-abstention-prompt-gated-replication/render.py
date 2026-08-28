"""No-abstention-prompt render for the gated replication cell.

Identical to the cross-family render
(`experiments/doubt-snap-cross-family-confirmatory/render.py`) except that the
abstention sentence is deleted from the system prompt. That deletion is the
ONLY diff, and it is enforced structurally at import time: this module imports
the parent render and reuses its tokenizer loading, chat-template fallback
ladder, and thinking-off assertion verbatim; only the module-global prompt is
replaced, after asserting the parent prompt contains the abstention sentence
exactly once and that removing it reproduces the registered no-abstention
prompt byte for byte.

Every arm in this cell (no_op, gated, random_direction) renders through this
module, so pinning the parent module's global is safe: no with-prompt render
ever runs in the same process.
"""

from __future__ import annotations

import importlib.util
import pathlib

_PARENT_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "doubt-snap-cross-family-confirmatory"
    / "render.py"
)

_spec = importlib.util.spec_from_file_location("_doubt_snap_parent_render", _PARENT_PATH)
_parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parent)

# The deleted sentence, verbatim from the parent BASELINE_SYSTEM_PROMPT
# (including its trailing space).
ABSTENTION_SENTENCE = (
    "If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. "
)

# The registered no-abstention prompt (AMENDMENT.md Design, "Prompt
# manipulation"). Kept as an explicit literal so any drift in the parent
# prompt fails loudly here instead of silently changing this cell's surface.
NO_ABSTENTION_SYSTEM_PROMPT = (
    "Answer the user's question. Return only a JSON "
    "object with exactly two keys: \"answer\" and \"response_confidence\". "
    "The \"answer\" value is your answer or abstention text. The "
    "\"response_confidence\" value is your probability from 0 to 1 that your "
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)

if _parent.BASELINE_SYSTEM_PROMPT.count(ABSTENTION_SENTENCE) != 1:
    raise RuntimeError(
        "parent BASELINE_SYSTEM_PROMPT does not contain the abstention "
        "sentence exactly once; the parent render has drifted from the "
        "registered prompt and this cell must not run"
    )
if _parent.BASELINE_SYSTEM_PROMPT.replace(ABSTENTION_SENTENCE, "") != NO_ABSTENTION_SYSTEM_PROMPT:
    raise RuntimeError(
        "deleting the abstention sentence from the parent prompt does not "
        "reproduce the registered no-abstention prompt; the diff is no "
        "longer only the abstention sentence and this cell must not run"
    )

# Pin the parent module's prompt global; parent.render() reads it per row.
_parent.BASELINE_SYSTEM_PROMPT = NO_ABSTENTION_SYSTEM_PROMPT

assert_no_think_scaffolding = _parent.assert_no_think_scaffolding
render = _parent.render
