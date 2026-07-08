# Modal launch

Read this before launching mechinterp cells on Modal or another paid/cloud GPU
lane.

## Launch lanes

- **Local GPU** - Run GPU verbs directly with `--i-know-this-runs-on-gpu`.
  Iterate CPU verbs (`probe-fit`, `score-gates`) freely. Use local
  `mechinterp run --provider local --dry-run` and CPU command stages before
  involving Modal.
- **Modal / cloud GPU** - Prefer `mechinterp run --provider modal` against an
  exact pushed Synaptic Tuner commit. New surfaces can use Modal A10G-style
  lanes when approved; parity-locked cells remain on the registered substrate.

Before any paid run, walk the wrapper-authoring checklist in the
experiment-runner skill:

- [../experiment-runner/reference/runpod-modal-lanes.md](../experiment-runner/reference/runpod-modal-lanes.md)

That reference owns the generic paid-run killers: retry-idempotent clone,
argparse equals form for negative-leading values, spawn/detach reaping,
`HF_HUB_DISABLE_XET` in image and function, staging-input verification, and
lane-selection policy. Do not duplicate that checklist here.

For HF Jobs training lane details, use:

- [../experiment-runner/reference/cloud-lane.md](../experiment-runner/reference/cloud-lane.md)

## Modal-specific mechinterp gotchas

- Modal currently clones the pushed tuner repo/commit. Local fixes do nothing
  until committed, pushed, and passed as `--repo-commit`.
- Use Modal only when selected pipeline configs and referenced stage configs are
  available to the cloned environment, or after adding an explicit generic
  artifact-staging mechanism.
- Launch long-running cells as detached remote functions, not as a local
  entrypoint that calls `.spawn()` and exits unless that exact pattern has just
  been verified. A reliable direct shape is:

```bash
modal run --detach path/to/modal_app.py::run_one_cell --cell-id ...
```

- Local-entrypoint `spawn()` can leave an app record with zero tasks after the
  parent exits. Confirm with `modal app list` and `modal app logs`.
- Keep exactly one active writer per `(run_tag, cell_id)` Volume namespace. If a
  launch looked dead and you relaunch, re-check active apps and stop the
  ambiguous earlier app before replacement writes the same checkpoints.
- Put every resumable per-cell output directory on a Modal Volume before GPU
  work starts, and commit the volume periodically during long subprocesses. A
  retry can otherwise restart from zero even when the tuner verb has `--resume`.
- Batch-parity smokes should enforce the registered gate semantics. If the gate
  says "same parsed answer and stop reason," do not compare exact token IDs.
  If byte/token parity is the registered requirement, state that before launch.
- Push batch sizes aggressively only after live-volume resume works. Use
  first-batch peak memory as stage-specific evidence; generation, capture, and
  steering can have different curves.
- Any change to a signed helper listed in `instrument.modules` requires a
  refreshed sha pin, registry regeneration, validation, commit, push, and
  relaunch from the pushed commit.
