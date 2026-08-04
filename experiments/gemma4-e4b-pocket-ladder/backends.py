"""Vendored import-restoration shim -- a RE-EXPORT, not a copy.

Restores an import target that this experiment's pinned `model_lib.py` resolves
by bare module name. `model_lib.render()` does:

    module_name, func_name = cfg["render"]["fn"].split(":")   # "backends:render_probe_prompt"
    module = importlib.import_module(module_name)

and every family config in this experiment points at `backends:render_probe_prompt`.
The historical `experiment/phase1/probe/backends.py` that name referred to was
archived by an unrelated main-branch reorg; the archive copy is a dead compat
wrapper pointing at a nonexistent path. The live, actively-maintained successor
is `experiments/common/knowledge_probe/backends.py`, with an identical
`render_probe_prompt` signature.

## Why a shim at all, and why a re-export rather than a copy

The parent experiment (`j-space-cross-family-layer-contrast`) restored this by
adding `experiments/common/knowledge_probe` to `PYTHONPATH` on every pipeline
invocation. That works, but it makes a correct render depend on an environment
variable set correctly at every launch, with a silent-wrong-answer failure mode
if it is ever set to the archived tree instead. This experiment's donor
diagnostic could only be run by ALSO putting the parent experiment's directory
on `PYTHONPATH` -- a cross-experiment runtime dependency that should not survive
to sign. Recorded as an outstanding item in `cell.yaml
integration_status.missing` and in NOTEBOOK.md 2026-07-25.

This file removes both. It resolves the live module BY PATH from the repo root
and re-exports the one function needed.

Deliberately a re-export and NOT a vendored copy: `experiments/common/
knowledge_probe/backends.py` is live and actively maintained, and it is the same
render path the probe harness uses. Copying it here would fork the render at the
moment of copying and let this experiment silently drift from the convention its
inputs were produced under -- exactly the failure the frozen-prompt hash in
`amendment_ah_stage0_extract.py` exists to prevent for the system prompt. The
sibling shim freezes the prompt; this one freezes the render path.

## Fail-closed freeze

Two independent guards, both raising rather than degrading:

1. The rendering-relevant source of the upstream module -- `render_probe_prompt`,
   `_apply_chat_template`, `assert_no_think_scaffolding`, `_RENDER_MODES`, and
   the two thinking-marker constants -- is hashed and must equal
   `_EXPECTED_RENDER_PATH_SHA256`. It deliberately does NOT hash the whole file:
   `backends.py` also carries a vLLM backend this experiment never touches, and
   an edit there should not stop a run. An edit to the render path itself should.
2. `render_probe_prompt`'s signature is asserted, so a compatible-looking but
   reordered/renamed parameter list fails here rather than rendering something
   subtly different.

Updating either constant is a deliberate act that belongs in NOTEBOOK.md with a
re-verification, not a silent refresh.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import sys
from pathlib import Path

_UPSTREAM_REL = Path("experiments/common/knowledge_probe/backends.py")

# sha256 over the concatenated source of the render path (see docstring for the
# exact member list and the ordering). Computed 2026-07-25 against the live
# module. This is NOT a hash of the whole file.
_EXPECTED_RENDER_PATH_SHA256 = (
    "c35130e0f3d5818b2820d615fd1e4c3ec754c11c61c91061d7c3da464833915f"
)

_EXPECTED_SIGNATURE = (
    "(tokenizer, system_prompt: 'str', question: 'str', *, "
    "enable_thinking: 'bool', mode: 'str | None' = None) -> 'tuple[str, str | None]'"
)


def _repo_root() -> Path:
    """Walk up from this file until the upstream module is found.

    Repo-root-relative rather than absolute: this experiment is developed in git
    worktrees, and an absolute path would silently bind a worktree run to the
    canonical checkout's copy of the render path.
    """
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / _UPSTREAM_REL).is_file():
            return candidate
    raise RuntimeError(
        f"[backends shim] could not locate {_UPSTREAM_REL} in any parent of "
        f"{here}. This shim restores the `backends:render_probe_prompt` import "
        "target that model_lib.render() resolves by bare module name; without "
        "the upstream module there is no render path to re-export."
    )


def _load_upstream():
    path = _repo_root() / _UPSTREAM_REL
    # Distinct module name: this file is itself importable as `backends`, and
    # reusing that name here would make the shim import itself.
    spec = importlib.util.spec_from_file_location("_knowledge_probe_backends", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"[backends shim] could not load a module spec from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_knowledge_probe_backends"] = module
    spec.loader.exec_module(module)

    blob = "\n".join([
        inspect.getsource(module.render_probe_prompt),
        inspect.getsource(module._apply_chat_template),
        inspect.getsource(module.assert_no_think_scaffolding),
        repr(module._RENDER_MODES),
        repr(module.THINK_TAG_MARKERS),
        module.EMPTY_THINK_OFF_MARKER_RE.pattern,
    ])
    actual = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    if actual != _EXPECTED_RENDER_PATH_SHA256:
        raise RuntimeError(
            f"[backends shim] render path in {path} changed: expected sha256 "
            f"{_EXPECTED_RENDER_PATH_SHA256}, got {actual}. Refusing to render "
            "with an unverified render path -- every artifact this experiment "
            "produces is conditioned on it, and a silent change would make old "
            "and new rows incomparable with nothing on disk to tell them apart. "
            "Re-verify the render convention, record it in NOTEBOOK.md, then "
            "update this hash deliberately."
        )

    actual_sig = str(inspect.signature(module.render_probe_prompt))
    if actual_sig != _EXPECTED_SIGNATURE:
        raise RuntimeError(
            f"[backends shim] render_probe_prompt signature changed: expected "
            f"{_EXPECTED_SIGNATURE}, got {actual_sig}."
        )
    return module


_upstream = _load_upstream()

render_probe_prompt = _upstream.render_probe_prompt
assert_no_think_scaffolding = _upstream.assert_no_think_scaffolding

__all__ = ["render_probe_prompt", "assert_no_think_scaffolding"]
