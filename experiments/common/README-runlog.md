# Resumable per-item run logs (RunLog)

Generic checkpoint/resume infrastructure for long per-item evaluation loops
lives in the `synaptic-tuner` submodule at `shared/utilities/run_log.py`
(class `RunLog`). It is stdlib-only (no torch import) and project-agnostic;
this note is the research-repo-specific consumption guide. Read the module's
own docstring for the full API and failure-mode rationale before using it.

## Why this exists

A multi-hour per-item loop (generate, then grade, one row at a time) that
buffers every result in memory and writes output only at the end loses the
whole run to a crash in the final stretch. This is not hypothetical here:
`experiments/j-space-layer-replication-*` and `run_contrast.py`-style scripts
build a `records = [run_one_row(...) for r in rows]` list per arm and only
write a summary at the end of the loop, so a kill anywhere in a multi-hour
arm loses that arm's rows entirely. The Modal doubt-snap wrapper already
implements the same idea on the volume side (durable per-row writes plus a
`DONE` marker checked before treating a run as complete); `RunLog` is the
local, generic version of that pattern; see
`experiment/protocol/notes/ak-stage1-modal-launch-plan.md` for the volume-side
precedent it mirrors.

## Importing it from an experiment script

Follow the same `sys.path` convention already used to reach `MechInterp.*`
from experiment scripts (see `j-space-midband-write-sweep-qwen3-4b/model_lib.py`
and `j-space-cross-family-layer-contrast/model_lib.py`):

```python
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # experiments/<slug>/
REPO_ROOT = HERE.parents[1]                       # repo root
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
if str(TUNER_DIR) not in sys.path:
    sys.path.insert(0, str(TUNER_DIR))

from shared.utilities.run_log import RunLog, RunLogError
```

**Availability note (as of this writing):** `shared/utilities/run_log.py`
exists on the tuner branch `feature/runlog`, not yet on `main`. Any consumer
must either check out that branch inside its own `synaptic-tuner` checkout,
or wait until it is merged and the root repo's submodule pointer is bumped.
Import failures should fail loudly with a message naming the required branch,
not fall back to an unchecked-in loop -- see the cross-family wiring in
`experiments/j-space-cross-family-layer-contrast/run_contrast.py` for the
pattern.

## Log-path convention

One `RunLog` per arm (or per family x arm, for multi-family experiments),
under the experiment's gitignored `analysis/` directory, so a resumed run
picks up exactly where a killed one left off:

```
experiments/<slug>/analysis/<family>/runlog/<arm>.jsonl
```

which yields the sidecars `<arm>.jsonl.meta.json` and
`<arm>.jsonl.summary.json` alongside it. Do not point a `RunLog` at anything
under `analysis-committed/`; that tree is for finalized, hand-promoted
artifacts, not live per-row state.

## Minimal usage

```python
run_log = RunLog(
    arm_log_path,
    run_config={"experiment": "j-space-cross-family", "family": family, "arm": arm},
)
pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
for row in pending:
    result = run_one_row(row)  # generate + grade
    run_log.record(row["row_key"], result)

all_records = load_jsonl(arm_log_path)  # your own JSONL loader, or the arm's rows.jsonl reader
run_log.finalize({"n_rows": len(all_records), ...})
run_log.close()
```

`run_config` should include everything that would make a resumed run invalid
if it changed silently (model ref, seed, prompt/render version, arm
definition). A mismatched fingerprint on reopen raises `RunLogError` rather
than silently mixing rows from two different configs; pass `fresh=True` only
when the config change is intentional and old rows should be discarded.

## When to use it

Per the `mechinterp-cells` skill: any local run expected to take longer than
about 15 minutes should write per-item results through `RunLog` and write its
summary atomically. Sign-pinned instruments must adopt this before sign,
since a pinned instrument file cannot be patched mid-run to add resumability
after a crash has already happened.
