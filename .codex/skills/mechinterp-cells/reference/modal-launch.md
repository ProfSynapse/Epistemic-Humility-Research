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

## GPU sizing rule (PI directive, 2026-07-30)

Never hard-code a GPU type into a cloud harness. The GPU is an ARGUMENT the
operator provides at dispatch (env var or CLI flag with an explicit default),
and the choice is made from the model actually being run, at harness-review
time, with the arithmetic recorded in the launch record:

1. Estimate the footprint: weights (params x dtype bytes) + KV/activation
   headroom for the largest stage (extraction and teacher-forced sweeps are
   the usual peak, not generation) + roughly 20% margin.
2. Pick the SMALLEST tier that fits: A10G (24 GB) for models up to roughly
   7B bf16 with modest batches; L40S (48 GB) for up to roughly 20B bf16 or
   smaller models with heavy activation caching; A100-80GB / H100 only when
   the arithmetic demands it, never as a default.
3. The harness reads the GPU type from its argument and records it in every
   stage's provenance so the executed hardware is auditable per stage.
   "A100 because that is what the last lane used" is not a justification.
4. Within one experiment, keep the GPU FIXED across arms of the same
   registered contrast once any arm has run: provenance uniformity between
   paired arms outranks the saving from switching mid-run.

Cautionary case: the gemma4-e4b kv-seam Phase B lane hard-coded A100-80GB
for a model whose stages fit an L40S; the two 85-minute dose calibrations
cost roughly double what they needed to. Caught by the PI mid-tranche
(2026-07-30); that lane kept A100 for arm-parity per rule 4, its harness
was converted to take the GPU as an argument, and this rule exists so the
next lane sizes correctly from the start.

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

### One socket, two Docker daemons: Docker Desktop must be OPEN

`unix:///var/run/docker.sock` inside the WSL distro is backed by TWO
different daemons depending on whether Docker Desktop is running. With
Desktop open, the socket is served by the Desktop engine (`docker info`
shows `Operating System: Docker Desktop`, an `nvidia` entry under
`Runtimes`, and the image store that holds the program's validated
`mechinterp-runner` builds). With Desktop closed, the same path silently
falls back to the WSL-native `dockerd` (runc only, no nvidia runtime, a
separate and unrelated image store). Nothing errors on the switch; commands
just answer from a different daemon. This has bitten twice (kv-seam Phase A
dispatch, 2026-07-29; idk-switch digest capture, 2026-07-31), so:

1. **If GPU-in-container fails, the first hypothesis is that Docker Desktop
   is not open.** The signature is `docker run --gpus all` failing with
   `could not select device driver "" with capabilities: [[gpu]]`. Do NOT
   work around it (no `nvidia-container-toolkit` install, no engine
   switching, no image rebuilds): ask the user to open Docker Desktop, then
   re-run the preflight below (PI directive, 2026-07-31).
2. **Preflight before every local GPU verb AND before every digest
   capture:** `export DOCKER_HOST=unix:///var/run/docker.sock`, then confirm
   `docker info` shows `Operating System: Docker Desktop` and `nvidia`
   under `Runtimes`. Only then trust `--gpus all` or any image query.
3. **Digest-capture corollary:** `docker image inspect <tag>` answers from
   whichever daemon currently owns the socket, so a
   `runtime_image_digest` recorded without the preflight can silently pin
   an image from the wrong store. Worked failure: the
   idk-switch-naming-confirmatory sign captured its runtime digest from the
   native store while Desktop was closed, pinning an unrecorded image
   instead of the Phase A validated build; repaired by a recorded lead
   repin. When a provenance digest check fails, ask "which daemon am I
   talking to?" before assuming the image is wrong.

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
