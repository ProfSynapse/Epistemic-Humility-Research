"""Vendored environment-restoration shim -- NOT a ported amendment script.

Restores an import target `model_lib.py` (pinned) names literally:
`from amendment_ah_stage0_extract import load_baseline_system_prompt`. This
file supplies ONLY that one function; it is not a copy or port of the real
historical `experiment/phase1/probe/amendments/amendment_ah_stage0_extract.py`
amendment script (which did GPU pre-generation extraction for a different,
unrelated experiment -- see its own docstring). Sibling convention to this
experiment's vendored `scorers.py` (see NOTEBOOK.md "VENDOR SCORERS").

## Why this shim exists

The only surviving copy of `amendment_ah_stage0_extract.py` in this repo is
archived (`archive/experiment/phase1/probe/amendments/`), with no live twin.
It is unusable as-is for two independent reasons, discovered while diagnosing
this experiment's llama-3.2-3b `extract_anchor.py` G0 crash (2026-07-23):

1. It hardcodes `AC_CONFIG = repo_root() / "experiments/doubt-regulated-
   caution/phase3_ac_doubt_coupled_intervention.yaml"`. That exact filename no
   longer exists: traced via `git log --follow`, it was moved out of
   `experiment/phase1/probe/config/` (commit 6b66536a "Associate AC
   doubt-caution configs") and then renamed, dropping the `phase3_` prefix
   (commit d55b7d26 "Rename active probe and mechinterp surfaces"), to its
   current path `experiments/doubt-regulated-caution/
   ac_doubt_coupled_intervention.yaml`. `git show d55b7d26` on that file's
   diff was checked directly: the `prompt:` block is untouched in that patch
   (only unrelated fields, e.g. checkpoint paths, changed), so the
   `prompt.system` content itself is verified unchanged across the rename.
2. Its sibling archived `path_compat.py`'s own `repo_root()` heuristic checks
   for `experiment/phase1/eval/scorers.py` existing -- but that file was
   itself archived by the same repo reorg that broke this experiment's own
   `grader.py` `EVAL_DIR` (see NOTEBOOK.md "VENDOR SCORERS"), so the archived
   `path_compat.py` is internally broken independent of point 1. The LIVE
   successor `experiments/common/readouts/path_compat.py` fixes that check
   but does not define the `phase1_probe_dir()`/`phase1_eval_dir()` names the
   archived amendment script imports (renamed to `knowledge_probe_dir()` /
   `locked_eval_dir()` / `readouts_dir()`) -- an API mismatch, not just a
   stale path.

Net: the archived script cannot be recovered by an environment/PYTHONPATH fix
alone (no edits, no new files) -- the failure is a hardcoded dead filename
plus an incompatible dependency API, not a missing search path. Adjudicated
by the lead 2026-07-23: vendor this minimal shim into the experiment
directory (not a loose PYTHONPATH file), freeze the loaded prompt against an
embedded hash so a future edit to the doubt-regulated-caution yaml crashes
this experiment instead of silently changing its render, and cross-check
against the sibling `doubt-snap-cross-family-confirmatory` experiment's own
recorded prompt before use.

## Frozen-prompt cross-check (done at diagnosis time, 2026-07-23)

`experiments/doubt-snap-cross-family-confirmatory/render.py`'s hardcoded
`BASELINE_SYSTEM_PROMPT` literal -- the prompt that experiment's frozen
late-site directions (`c_hat`/`u_d`/`gate_fit`, reused verbatim by this
experiment's late arm) were actually fit under -- was loaded directly (module
import, not hand-transcribed) and compared byte-for-byte against this
shim's yaml-sourced string: IDENTICAL (`MATCH: True`), same sha256
`81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c` for both.
This confirms the render convention this shim restores matches what the
reused frozen late-site artifacts were fit on -- the AMENDMENT.md "Open
questions at sign" #5 render/anchor reconciliation concern is resolved
affirmatively for the system-prompt component specifically (anchor position
and enable_thinking convention are separately unchanged, ported verbatim in
model_lib.py/gen_lib.py).

## Fail-closed freeze

The loaded `prompt.system` string's sha256 must equal `_EXPECTED_SHA256`
below (computed once, here, from the current live yaml content). A future
edit to `experiments/doubt-regulated-caution/ac_doubt_coupled_intervention.yaml`
that changes `prompt.system` will make this raise instead of silently
changing what every family's generation actually renders.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

_CONFIG_PATH = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/"
    "experiments/doubt-regulated-caution/ac_doubt_coupled_intervention.yaml"
)

# sha256 of the prompt.system string, computed 2026-07-23 from the yaml above
# AND verified byte-identical to doubt-snap-cross-family-confirmatory's
# hardcoded BASELINE_SYSTEM_PROMPT literal (see docstring). Frozen: this
# module refuses to return a prompt whose hash does not match.
_EXPECTED_SHA256 = "81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c"


def load_baseline_system_prompt() -> str:
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    prompt = cfg["prompt"]["system"]
    actual = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if actual != _EXPECTED_SHA256:
        raise RuntimeError(
            f"[amendment_ah_stage0_extract shim] {_CONFIG_PATH} prompt.system "
            f"sha256 mismatch: expected {_EXPECTED_SHA256}, got {actual}. "
            "The source yaml changed since this shim's hash was frozen "
            "2026-07-23 -- refusing to render with an unverified prompt. "
            "Re-verify against doubt-snap-cross-family-confirmatory's "
            "BASELINE_SYSTEM_PROMPT (render.py) before updating this hash."
        )
    return prompt
