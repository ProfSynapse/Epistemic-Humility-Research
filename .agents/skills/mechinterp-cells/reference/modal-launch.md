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

### Local GPU runs execute in a pinned container

**Binding invariant (standing directive, 2026-07-10):** every local-3090
`mechinterp` GPU verb (`extract`, `steer`, `dose-calibrate`) runs inside the
pinned mechinterp runner image, never against a bare shared conda
environment. Trigger: the shared `unsloth_env` conda environment aged out of
`model_type qwen3_5` (its pinned `transformers` was too old for the newer
architecture), which was only caught mid-experiment and forced an
undocumented-until-then environment hop. Experiment file instruments are
already sha256-pinned in `experiment.yaml`, but the runtime that executes
them was not, which left a gap in the provenance story that this closes. The
Modal cloud lane above is already containerized; this brings the local lane
to parity.

- The image and its build instructions live in the `synaptic-tuner`
  submodule at `docker/mechinterp-runner/` (generic, project-agnostic; see
  its `README.md` for the build command, exact pinned versions, and the
  WSL2 + NVIDIA Container Toolkit run pattern with `--gpus all`).
- A signing or resigning experiment records the runtime alongside its file
  pins: capture the image digest (or local Image ID when it has not been
  pushed to a registry) as `instrument.runtime_image_digest` in
  `experiment.yaml`, a sibling of `instrument.pins` rather than a key inside
  it (`instrument.pins` is strictly relpath-to-sha256 for real files;
  `bin/exp sign`/`validate` iterate it as file hashes, so a non-file key
  placed inside `pins` fails validation and gets silently overwritten on the
  next `exp sign`).
- The runner's entrypoint prints one line of provenance JSON at container
  start (image digest, git revision the image was built from, torch/
  transformers/python versions, CUDA availability). That line must appear
  in the run log for any local GPU cell launched after this directive.
- Delegation prompts for local GPU `mechinterp` work must restate this
  invariant; a subagent building or launching a local extract/steer/
  dose-calibrate cell does not inherit it automatically.
- **Honored exception:** `experiments/qwen35-4b-midband-doubt-snap/`, in
  flight on its documented conda-env deviation at the time this directive
  landed, finishes on that deviation rather than being interrupted to
  rebuild inside the container. The invariant binds starting at the next
  experiment boundary, not retroactively.
- See also
  [../../experiment-runner/reference/local-runtime.md](../../experiment-runner/reference/local-runtime.md)
  in the experiment-runner skill: that file documents a *different* local
  Docker lane (`tuner.py local-run` training jobs launched from Windows via
  Docker Desktop over an npipe) and is not the home for this invariant; it
  carries a pointer back here instead of duplicating this section.

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
