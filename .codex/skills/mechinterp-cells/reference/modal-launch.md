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

## Long GPU stage launch discipline (no detached nohup)

A multi-stage cell pipeline must never launch a long GPU stage as a bare
detached `nohup` process that outlives the launching agent's turn. When that
process exits, nothing re-invokes the agent, the next stage never starts, and
the pipeline silently stalls until a human notices it. This happened twice in
one night on the M4 world-known rebase: once at the census handoff, and again
after the native fit.

Use one of two sanctioned launch patterns:

- **Harness-tracked background execution** - the Bash tool's
  `run_in_background`, which re-invokes the launching agent when the process
  exits so it can chain the next stage.
- **One sequential driver script** - a single script that runs the remaining
  stages in order itself and only returns at a governance halt or at full
  completion.

Whichever pattern is used, the chain MUST hard-halt (never auto-continue) at
governance gates: any firing / S1 gate with a void-and-lift arm, any preflight
failure, and the blinded-grading boundary.

Detached processes also do not survive host/WSL restarts cleanly: the M4-WK
census silently restarted from scratch after a host reset. Write stage
scripts to be resumable and idempotent (skip rows already written) so a
restart costs minutes, not hours.

The lead/orchestrator arms a persistent stall monitor for any overnight or
multi-stage run: a watcher that emits an event on new commits or new stage-log
lines, and fires a stall alert when the GPU sits idle with no progress for
about 20 minutes while the run is still incomplete. Progress checks must not
depend on the user asking.

## Steering and dose-calibration gotchas

These issues are specific to activation intervention (steering/dose-calibrate) and
hidden-state manipulation, on top of the generic cloud checklist in
runpod-modal-lanes.md.

### PEFT/Unsloth adapter wrapping hides decoder layers

A PEFT-wrapped causal LM has the structure `PeftModelForCausalLM -> LoraModel ->
base`; the decoder `ModuleList` (the target for intervention hooks) is several
attributes deep and differs across architectures. The tuner's hook registration
detects and unwraps adapters by calling `get_base_model()`, then tries known
paths in order: `model.layers`, `language_model.model.layers`, `model.decoder.layers`,
`transformer.h`. If a new architecture fails to unwrap, error messages will
indicate which path was attempted; add the correct path to the tuner's registry
rather than working around it in the cell config or grader.

### Layer index off-by-one (hidden_states indexing vs block numbers)

In transformer models, `hidden_states[L]` is the OUTPUT of decoder block `L-1`;
`hidden_states[0]` is the input embedding. A direction fit at "layer 35" (meaning
the output of block 34) should specify `layer: 35` in the direction JSON, and the
tuner's hook registration internally maps this to `layers[34]`. Direction JSONs
that record BOTH `layer` and `block` fields are self-checking; the tuner asserts
they agree (e.g., `layer: 35, block: 34`). Mismatches will error before any
intervention. When manually specifying a layer in a cell config override, use the
hidden_states index (e.g., 35 for block 34's output).

### ULP floors for activation comparisons (bf16 accumulation noise)

Batched-vs-loop and steered-vs-baseline hidden-state comparisons accumulate
floating-point noise, especially in bf16. An ABSOLUTE hidden-state comparison
(e.g., ||h_steered - h_baseline||) is noisier than a DELTA comparison that
cancels shared batched noise (e.g., ||(h_steered - h_baseline) - (h_baseline -
h_baseline_repeat)||). The smoke readback validation compares the COMMANDED
coordinate move against the observed move within a tolerance (`smoke.write_rel_tol`),
not exact equality. Set this tolerance above the bf16 ULP floor for your model
and layer (typically 1e-3 to 1e-2 for common transformer sizes), not to zero. A
too-tight tolerance causes false smoke failures; a too-loose tolerance misses
real write bugs. Calibrate against a known-good baseline run on your GPU.

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
