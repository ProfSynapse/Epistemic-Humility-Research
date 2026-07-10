---
name: mechinterp-cells
description: Author, organize, and launch tuner-backed mechanistic-interpretation cells (activation reading and writing) for the Epistemic-Humility project. Use when designing a new steering / extraction / probe-fit / gate-scoring cell, deciding where its config, direction, grader, and outputs live, or launching one locally or on Modal. This skill is about USING the synaptic-tuner `mechinterp` verbs via declarative recipe YAML plus project plug-ins; it never modifies the tuner submodule and never touches the frozen legacy machinery.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# MechInterp Cells (tuner-backed)

The going-forward home for reading and writing a model's internal activations is
the `synaptic-tuner` `mechinterp` verb family, driven by declarative recipe YAML
plus a few project-supplied plug-ins. The bespoke machinery under
`experiment/phase1/probe/steering/` is **frozen for provenance** (see
`experiment/phase1/probe/steering/LEGACY.md`): it stays byte-stable as the signed
instrument of past and in-flight amendments, and every NEW cell uses the tuner
verbs instead.

This skill is authoring glue. It talks to the tuner only through recipe YAML and
public CLI verbs; it never adds project-specific code or config to the submodule.

## When to use

- Designing a new activation-**writing** cell (steering, setpoint regulation,
  ablation) -> `mechinterp steer`.
- Designing a dose-calibration cell to find a direction/layer's coherent
  erase-write window -> `mechinterp dose-calibrate`.
- Designing a new activation-**reading** cell (capture hidden states, fit a
  linear readout, freeze a direction) -> `mechinterp extract` + `probe-fit`.
- Adjudicating a per-row output against declarative gates -> `mechinterp
  score-gates`.
- Deciding where a new cell's config, frozen direction, grader, and outputs live
  (the organization principles below).

Do NOT use this to modify the frozen legacy scripts or to extend the tuner. For
existing legacy Phase 3 sweeps that still run on the bespoke code, see the
`mech-interp-runner` skill; that skill drives frozen machinery and mints no new
cells.

## The verbs

| Verb | GPU? | What it does |
|------|------|--------------|
| `mechinterp run` | depends on stages/provider | run a multi-stage `mechinterp-pipeline/v1` YAML locally or submit it to Modal |
| `mechinterp extract` | yes (`--i-know-this-runs-on-gpu`) | generate over rows, capture hidden states to safetensors + a manifest |
| `mechinterp probe-fit` | no (CPU) | fit a linear readout from extracted activations, freeze a `mechinterp-direction/v1` JSON |
| `mechinterp steer` | yes (`--i-know-this-runs-on-gpu`) | run the six-block declarative intervention cell (smoke-gated) |
| `mechinterp dose-calibrate` | yes (`--i-know-this-runs-on-gpu`) | run a resumable dose ladder over one or more frozen readouts, with per-row JSONL checkpoints and aggregate summaries |
| `mechinterp score-gates` | no (CPU) | evaluate a `gates.yaml` against a per-row output JSONL |
| `mechinterp list-configs` | no (CPU) | list the bundled example recipes |

Prefer `mechinterp run --config <pipeline.yaml>` as the outer operator surface
for new cells. It keeps orchestration config-first: the YAML declares stages,
stage configs, Modal image/GPU/timeout, checkpoint paths, environment, and
plug-in paths; CLI flags supply late-bound facts only (`--provider`,
`--repo-commit`, `--only-step`, `--from-step`, `--skip-step`, `--yes`, and the
per-run GPU acknowledgement). Use the individual verbs directly for focused
debugging, diagnostics, or when a single stage is genuinely all you need.

`extract` and `steer` refuse to run without `--i-know-this-runs-on-gpu`.
`probe-fit` and `score-gates` are CPU-only, so they are the parts you iterate on
locally without a GPU.

## Pipeline config

A pipeline config has schema `mechinterp-pipeline/v1` and belongs beside the
experiment's cell configs, for example `experiments/<slug>/pipeline.yaml`. Keep
it generic: it may reference project-owned rows, renders, graders, and gates,
but the Synaptic Tuner runner itself stays experiment-agnostic.

Use pipeline stages to sequence:

- `kind: command` for CPU/local smokes, preflight checks, or project-side
  deterministic transforms.
- `kind: mechinterp.extract` for activation capture.
- `kind: mechinterp.probe-fit` for direction fitting.
- `kind: mechinterp.steer` for intervention cells. Put `execution.render_fn` in
  the steer cell config, or `render_fn` on the pipeline stage, so launchers do
  not need wrapper flags for project prompt rendering.
- `kind: mechinterp.dose-calibrate` for coherent-window dose ladders over frozen
  readouts before committing a real intervention ladder.
- `kind: mechinterp.score-gates` for declarative adjudication.

Minimal operator commands:

```bash
cd synaptic-tuner

# Inspect the exact stage plan without touching GPU or cloud.
python tuner.py mechinterp run \
  --config ../experiments/<slug>/pipeline.yaml \
  --provider local \
  --dry-run

# Run a CPU-only stage locally.
python tuner.py mechinterp run \
  --config ../experiments/<slug>/pipeline.yaml \
  --provider local \
  --only-step fit \
  --yes

# Submit a GPU pipeline to Modal from an exact pushed tuner commit.
python tuner.py mechinterp run \
  --config ../experiments/<slug>/pipeline.yaml \
  --provider modal \
  --repo-commit <pushed-synaptic-tuner-sha> \
  --i-know-this-runs-on-gpu \
  --yes
```

Do not use Modal just to test CPU config plumbing. Run a local `command` stage
smoke first; reserve Modal for a GPU-backed extract/steer path after the plan is
clean and the exact commit is pushed.

## The six-block steer cell

A `steer` cell is described entirely by one recipe. Five blocks live in
`cell.yaml`; gates are scored separately (a run and its adjudication stay
independent). Blocks map 1:1 to the tuner Pydantic schema
(`synaptic-tuner/MechInterp/config.py`, `SteerCellConfig`).

1. **surface** - `rows_path` (a JSONL row pool), the `generation` contract
   (`max_new_tokens`, `do_sample`, `temperature`, `top_p`, `seed`), a `seed`, and
   an optional `expected_config_sha`. If `expected_config_sha` is set, the run
   aborts unless the recipe still hashes to it. This is the goalpost lock.
2. **readouts** - a list of frozen direction files the cell reads or writes
   along. Each entry is `{name, path}`; `path` points at a `mechinterp-direction/v1`
   JSON produced by `probe-fit`.
3. **law** - the intervention law and its shared parameters:
   - `kind`: `additive` (`h' = h + strength * d`) or `erase_write`
     (`h' = h - (h . d) d + strength * sigma * d`; removes the current projection
     and writes the commanded coordinate exactly, orthogonal complement
     untouched).
   - `readout`: the name of the readout to intervene along (must be in `readouts`).
   - `layer`: optional override; defaults to the readout's frozen layer.
   - `position`: `anchor` (last prompt token), `anchor_onward`, `final` (each
     row's true last non-pad token; correct under left and right padding), or
     `answer_window` (generated tokens only, from `window_start` onward - set
     `window_start` upstream in the row; the engine refuses `answer_window`
     without it rather than steering the whole sequence).
   - `generation_mode`: `anchor` (edit only the prefill anchor; KV cache carries
     it forward) or `gen_stream` (edit every decode step).
4. **arms** - named strength overrides that also select which rows are active.
   Each arm uses exactly one selection mode:
   - fixed `strength` (a baseline uses `0.0`);
   - `score_field` + `threshold` + `strength` (activate rows whose selection
     score passes the threshold);
   - `flag_field` (activate rows whose named boolean is true);
   - `permuted_control_of` + `control_seed` (a seeded, count-matched random draw
     that probes the same dose on a different population).
5. **execution** - `output_path` (the per-row JSONL), `resume` (skip rows already
   present), optional `grader` (`module:callable`), and optional
   `redact_fields` (recursive field names to drop before per-row records are
   persisted, e.g. restricted `answer_text`, `aliases`, `answer_value`, or
   `raw_output` fields that a grader may need transiently but the checkpoint
   must not retain).
6. **smoke** - readback tolerances (`n_rows`, `write_rel_tol`, `write_abs_floor`,
   `offtarget_tol`). Before the full arms run, a small smoke pass applies the
   intervention and reads back the realized projection. `steer` refuses the full
   arms until a smoke passes for this exact config sha; `--force-full-run`
   overrides (do not use `--force-full-run` for a signed cell).

## Dosing an erase_write cell

`erase_write` writes an absolute coordinate, so the behavioral response is
threshold-then-collapse, not proportional to `strength`: a direction has a narrow
**coherent window** between inert and degenerate output, and a coarse absolute
ladder can jump clean over it (falsely reading a real lever as inert / voiding a
screen's positive control). Dose ambient-relative and pilot-sweep the window
first. Full method, measured numbers, and the smoke-is-write-accuracy caveat:
[reference/dose-calibration.md](reference/dose-calibration.md).

## Config-driven dose calibration

Use `mechinterp dose-calibrate` for new erase-write dose ladders instead of a
bespoke script. The config schema is `DoseCalibrationConfig`:

- `surface` - the same row pool and generation contract used by `steer`.
- `readouts` - frozen `mechinterp-direction/v1` files.
- `law` - intervention law, position, generation mode, and target readout.
  `law.readout: "*"` sweeps every declared readout; a named readout limits the
  run to that direction.
- `calibration` - dose rungs plus optional row selection. `dose_kind:
  setpoint` is the default; for `erase_write` the runner converts each dose to
  `strength = dose / sigma`. `dose_kind: strength` passes values directly to the
  hook.
- `execution` - `output_path` per-row checkpoint JSONL, `summary_path`
  aggregate JSON, `resume`, `render_fn`, optional `grader`, `batch_size`, and
  optional `redact_fields` for restricted per-row fields.

Resume is keyed by `(readout, dose, row_key)` against `execution.output_path`.
Every completed row is fsynced as it lands, so interrupted runs continue from
the last missing triple when `resume: true`. If the row pool or grader carries
restricted text, set `execution.redact_fields` so the grader can use those fields
in memory while the persisted checkpoint remains safe to keep under `analysis/`.

Minimal direct launch, from the repo root:

```bash
PYTHONPATH=experiments/common/renders:experiments/common/graders \
python synaptic-tuner/tuner.py mechinterp dose-calibrate \
  --mi-config experiments/<slug>/dose_calibration.yaml \
  --model unsloth/Qwen3-4B \
  --i-know-this-runs-on-gpu
```

Pipeline stage form:

```yaml
stages:
  - name: calibrate
    kind: mechinterp.dose-calibrate
    config: experiments/<slug>/dose_calibration.yaml
```

Treat the summary as a calibration artifact, not a verdict. The next amendment
or cell should pin selected setpoints and cite the committed aggregate summary,
while keeping raw row text and per-row generations untracked when restricted.

## Plug-in points (project code, not the tuner)

The tuner ships no notion of what a prompt looks like, what "correct" means, or
which rows matter. Each is a callable or file named in the recipe:

- **render function** (`--render-fn module:callable`): maps a row dict to a
  prompt string; apply your chat template here. Home:
  `experiments/common/renders/`.
- **content-end resolver** (`content_end_fn` in an extract recipe): maps
  `(full_ids, prompt_len, tokenizer)` to the index of the last content token.
- **grader** (`grader: module:callable` in a steer recipe): maps a per-row output
  dict to a grade dict, merged back so gates can read it. Home:
  `experiments/common/graders/`.
- **row pool** (`rows_path`): any JSONL your project produces, one object per row
  with a `row_key` (or `id`/`key`).

Render and grader callables are resolved with `importlib.import_module` against
`sys.path`. Reference them as flat module names and put their dirs on
`PYTHONPATH` so you do NOT have to add `__init__.py` up a tree that includes the
frozen `steering/` dir:

```bash
PYTHONPATH=experiments/common/graders:experiments/common/renders
```

## Organization principles

New evidence-producing work follows the **experiments-first** layout: one
self-contained directory per experiment at the repo top level,
`experiments/<slug>/`, holding the signed `AMENDMENT.md`, the `experiment.yaml`
manifest, a `NOTEBOOK.md`, and the cell configs. The `experiment/phase1/` tree
(singular) is frozen as the historical Phase 1 record; nothing new lands there.

The layout and lifecycle (directory shape, manifest fields, generated indices,
the `bin/exp` tooling) are governed by the `experiments` skill (PR in flight; see
`.skills/experiments/` once merged). This section keeps only the
**mechinterp-specific** rules for where a cell's pieces live and how signing keeps
goalposts from moving.

- **Cell configs live with the experiment.** Home:
  `experiments/<amendment-or-diagnostic-slug>/{cell.yaml, gates.yaml}`, co-located
  with that experiment's `AMENDMENT.md` and `experiment.yaml` manifest. The slug
  matches the amendment letter (e.g. `amendment-an`) or the lab-notebook slug for
  a diagnostic.
- **Direction JSONs are DATA** in `mechinterp-direction/v1` format. Their first
  home is the consuming experiment's own `experiments/<slug>/directions/`
  (gitignored data, reproducible from an extraction dir). The first time a SECOND
  experiment consumes the same direction, promote it to
  `experiments/common/directions/<checkpoint>/...` and record the originating
  experiment in its provenance. Recipes reference directions by relative repo path.
- **Shared graders and renders** live under
  `experiments/common/{graders,renders}/`, referenced as `module:callable` in the
  recipe (put those dirs on `PYTHONPATH`). A signed cell **byte-pins** the grader:
  record the grader file's sha256 in the amendment doc alongside the config shas.
- **Signing discipline.** At signing, the amendment doc pins `sha256` of
  `cell.yaml` + `gates.yaml` + the grader (and any render module). Set the cell's
  `surface.expected_config_sha` to the cell.yaml pin; the tuner enforces it at
  run time, so the config cannot drift silently and the goalposts cannot move
  after the result.
- **Outputs are untracked** under the experiment's own
  `experiments/<slug>/analysis/` (gitignored). Staging uploads are namespaced by
  `RUN_TAG`.
- **Naming.** Run tags are `<slug>-r<N>` (e.g. `amendment-an-r2`). Smoke-state
  files live with the outputs, never committed.

## Worked example

`experiments/example-cell/` is a complete, parseable AN-style cell expressed
against the real tuner schema. It is clearly marked **NOT a registered
instrument** - a teaching artifact, never launched as confirmatory. It ships:

- `cell.yaml` - six-block steer cell (erase_write setpoint on `answer_window`,
  baseline / thresholded primary / seeded permuted control / two-rung dose
  ladder).
- `gates.yaml` - reach (`count_flips`), specificity (`kill_diff_vs_control`),
  readout floor (`auroc_floor`).
- `direction_stub.json` - a hand-written `mechinterp-direction/v1` stub so the
  cell runs end to end without a fitted direction.
- companion plug-ins under the shared home:
  `experiments/common/graders/example_grader.py` and
  `experiments/common/renders/example_render.py`.

Validate CPU-side (no GPU) that the config and gates parse against the real
schema.

> **Run tuner commands from the REPO ROOT (or the experiment worktree root),
> never from inside `synaptic-tuner/`.** A cell's internal paths
> (`surface.rows_path`, `execution.output_path`, every `readouts[*].path`) are
> written repo-root-relative, and the tuner opens them at the process working
> directory. A `cd synaptic-tuner` first would silently resolve every one of
> them against the wrong directory and miss the files. Invoking
> `python synaptic-tuner/tuner.py ...` keeps the CWD at the repo root while
> still making `MechInterp` importable (Python adds the script's own directory
> to `sys.path`). For the parse-only import checks, put the tuner on
> `PYTHONPATH` instead of `cd`-ing into it.

```bash
# from the repo root (or the experiment worktree root)
PYTHONPATH=synaptic-tuner python -c "from MechInterp.config import load_steer_config; \
  load_steer_config('experiments/example-cell/cell.yaml'); print('cell ok')"
PYTHONPATH=synaptic-tuner python -c "from MechInterp.stats.evaluator import load_gates_config; \
  load_gates_config('experiments/example-cell/gates.yaml'); print('gates ok')"
python synaptic-tuner/tuner.py mechinterp list-configs   # bundled tuner templates
```

## Typical workflow

For new cells, make `pipeline.yaml` the default launch artifact and use stage
selection flags for iteration. Run every command from the REPO ROOT (see the CWD
warning above). For project-local configs, set `runtime.workdir: ..` in the
pipeline YAML so stages execute against the research repo root while the tuner
entrypoint remains `synaptic-tuner/tuner.py`.

```bash
python synaptic-tuner/tuner.py mechinterp run \
  --config experiments/<slug>/pipeline.yaml \
  --provider local \
  --dry-run

python synaptic-tuner/tuner.py mechinterp run \
  --config experiments/<slug>/pipeline.yaml \
  --provider local \
  --only-step fit \
  --yes
```

Modal submission is for GPU-backed runs and currently clones the pushed tuner
repo/commit. Use it only when the selected pipeline config and referenced stage
configs are available in that cloned repo, or after adding an explicit generic
artifact-staging/experiment-repo mechanism.

```bash
python synaptic-tuner/tuner.py mechinterp run \
  --config synaptic-tuner/MechInterp/configs/templates/pipeline.yaml \
  --provider modal \
  --repo-commit <pushed-synaptic-tuner-sha> \
  --i-know-this-runs-on-gpu \
  --yes
```

The lower-level verb sequence is still useful when debugging a stage directly:
set `PYTHONPATH` to wherever your `--render-fn` / grader modules live (for
example `experiments/common/renders`, or the cell's own directory).

```bash
# 1. Extract hidden states over a labeled row pool (GPU).
PYTHONPATH=experiments/common/renders python synaptic-tuner/tuner.py mechinterp extract \
  --mi-config experiments/<slug>/extract.yaml \
  --model <base-model> \
  --render-fn example_render:render \
  --i-know-this-runs-on-gpu

# 2. Fit a linear readout and freeze a direction (CPU).
python synaptic-tuner/tuner.py mechinterp probe-fit \
  --mi-config experiments/<slug>/probe_fit.yaml

# 3. Run the intervention cell: smoke first, then the full arms (GPU).
PYTHONPATH=experiments/common/renders python synaptic-tuner/tuner.py mechinterp steer \
  --mi-config experiments/<slug>/cell.yaml \
  --model <base-model> \
  --render-fn example_render:render \
  --i-know-this-runs-on-gpu

# 4. Optionally calibrate the dose ladder before locking a real steer run (GPU).
PYTHONPATH=experiments/common/renders:experiments/common/graders \
python synaptic-tuner/tuner.py mechinterp dose-calibrate \
  --mi-config experiments/<slug>/dose_calibration.yaml \
  --model <base-model> \
  --i-know-this-runs-on-gpu

# 5. Adjudicate with declarative gates (CPU).
python synaptic-tuner/tuner.py mechinterp score-gates \
  --gates-config experiments/<slug>/gates.yaml \
  --rows-path experiments/<slug>/analysis/rows_out.jsonl
```

## Gates

A `gates.yaml` declares named gates over the per-row output, grouped by an `arm`
field; `overall_pass` is true only if every gate passes. Every primitive is
seeded, so a verdict is reproducible from its recorded seed:

- `count_flips` - rows whose outcome moved from one boolean state to another.
- `kill_diff_vs_control` - positive-count difference between a primary arm and a
  count-matched control, with a seeded row-bootstrap CI.
- `permutation_p` - one-sided permutation p-value for a count-matched positive
  count against a pool (add-one smoothed). The null is a COUNT-MATCHED DRAW: it
  draws `n_primary` rows without replacement from the pool `n_perm` times and asks
  how often the drawn positive count matches or beats the primary arm's positive
  count. It is NOT a label-permutation mean-difference test. This matches the
  permuted-control framing used by the amendment cells (e.g. AN); pick this
  primitive when your null is "the same dose on a random count-matched slice of
  the pool," not "shuffle the labels."
- `auroc_floor` - tie-safe AUROC point estimate with a Hanley-McNeil analytic SE
  and a seeded bootstrap lower bound.

## Direction JSON schema

`probe-fit` writes `mechinterp-direction/v1`: `layer`, `hidden_dim`, `vector`
(unit-norm when `normalized`), `mu` (mean offset), `sigma` (setpoint scale =
readout-score std), a `calibration` block, the fit `recipe`, and free-form
`provenance`. This is the object `steer` loads to intervene and any external
reader can consume.

## Launch lanes

- **Local** (RTX 3090): run the GPU verbs directly with
  `--i-know-this-runs-on-gpu`, **inside the pinned mechinterp runner
  container** (see "Local GPU runs execute in a pinned container" below).
  Iterate the CPU verbs (`probe-fit`, `score-gates`) freely; they need no
  GPU and do not require the container. Use local `mechinterp run` smokes
  for command/config plumbing before involving Modal.
- **Modal / cloud**: new cells launch through the tuner `mechinterp` verbs inside
  the Modal harness, preferably via `mechinterp run --provider modal` against an
  exact pushed Synaptic Tuner commit. Before any paid run, walk the
  wrapper-authoring checklist in the experiment-runner skill:
  [reference/runpod-modal-lanes.md](../experiment-runner/reference/runpod-modal-lanes.md)
  (five paid-run killers: idempotent clone under retries, argparse equals form
  for negative-leading values, spawn+detach reap-proofing, xet-off in image AND
  function, verify staging inputs pre-launch), plus the lane-selection rules in
  the same file (Modal A10G is for NEW surfaces; parity-locked cells stay on
  local 3090 / RunPod-3090). [reference/cloud-lane.md](../experiment-runner/reference/cloud-lane.md)
  covers the HF Jobs training lane. Do not duplicate those checklists here.

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
- See also [reference/local-runtime.md](../experiment-runner/reference/local-runtime.md)
  in the experiment-runner skill: that file documents a *different* local
  Docker lane (`tuner.py local-run` training jobs launched from Windows via
  Docker Desktop over an npipe) and is not the home for this invariant; it
  carries a pointer back here instead of duplicating this section.

### Modal cell gotchas

- Launch long-running Modal cells as detached remote functions, not as a
  local-entrypoint that calls `.spawn()` and exits unless that exact pattern has
  just been verified. A reliable direct shape is:
  `modal run --detach path/to/modal_app.py::run_one_cell --cell-id ...`.
  Local-entrypoint `spawn()` can leave an app record with zero tasks after the
  parent exits; always confirm with `modal app list` and `modal app logs`.
- Keep exactly one active writer per `(run_tag, cell_id)` Volume namespace. If a
  launch looked dead and you relaunch, re-check `modal app list` and stop the
  ambiguous earlier app before the replacement starts writing the same
  checkpoint files.
- Put every resumable per-cell output directory on a Modal Volume before GPU
  work starts (`analysis/<cell_id>` and `analysis-committed/<cell_id>` for
  experiment cells), and commit the volume periodically during long subprocesses.
  A retry can otherwise restart from zero even when the tuner verb itself has
  `--resume`, because completed rows were only on container scratch.
- Batch-parity smokes should enforce the registered gate semantics. If the gate
  says "same parsed answer and stop reason," do not compare exact token IDs:
  greedy batched generation can differ in harmless formatting while preserving
  the adjudicated answer. Conversely, if byte/token parity is the registered
  requirement, state that explicitly before launch.
- Push batch sizes aggressively only after the live-volume resume path is working.
  Use first-batch peak memory as a stage-specific signal: generation, capture,
  and steering can have different memory curves. If 8B/9B capture is at roughly
  half of GPU memory, doubling the next retry is reasonable, but watch the first
  steer smoke before treating that as the new default.
- Any change to a signed helper that is listed in `instrument.modules` must be
  followed by a refreshed sha pin, `bin/exp regen`, validation, commit, push, and
  relaunch from the pushed commit. Modal clones the commit you pass; local fixes
  do nothing until the commit exists remotely.

## Migration map (legacy -> tuner)

| Legacy file (frozen) | Tuner replacement |
|----------------------|-------------------|
| `confidence_steer.py` `SteeringHook` (`h += alpha*d`) | `mechinterp steer` with `law.kind: additive` (or `erase_write` for a setpoint), `law.position`, `law.generation_mode` |
| `amendment_*_grade_and_gates.py` | `mechinterp score-gates` + a project grader under `graders/` |
| `gpu_equivalence_cell.py` (CPU-vs-GPU hook check) | the built-in `steer` smoke readback / equivalence self-check |
| `*_extract.py`, `amendment_*_primed_extract.py` | `mechinterp extract` (+ `content_end_fn` plug-in) |
| `persist_probe_direction.py` (fit + persist direction) | `mechinterp probe-fit` -> frozen `mechinterp-direction/v1` JSON |
| bespoke erase-write dose sweeps | `mechinterp dose-calibrate` with `calibration.doses`, `dose_kind`, checkpoint JSONL, and summary JSON |
| `run_arm_a.py` / `run_arm_b.py` orchestration | `arms` block in one `cell.yaml` (fixed / score-thresholded / flagged / permuted-control) |

Current genericization gap: compound multi-write arms (for example `c_hat` plus
a second token-target direction in one generation pass) and J-lens/token-target
direction builders are not yet first-class tuner verbs. The reusable shape is:

- tuner-owned: schema for one arm carrying multiple readout writes, each with
  its own readout, layer override, setpoint/strength, and optional readback;
- project-owned: prompt rendering, row splits, gates, graders, and token/J-lens
  bundles;
- tuner-owned: deterministic checkpoint/resume, recursive `redact_fields`, and
  smoke/readback validation;
- project-owned: which fields are restricted and which aggregate metrics define
  a given amendment's gates.

Do not promote experiment-local no-op record seeding until the runner can assert
the generation contract is deterministic (`do_sample: false`) and the arm is
provably off for that row. Under sampling, copied no-op rows are not a valid
resume optimization.

Keep one-off versions project-side only long enough to settle the interface,
then promote the interface as a config-driven tuner surface rather than copying
another bespoke runner.

## Invariants

- Never edit the frozen legacy files (`steering/LEGACY.md` lists them). New
  capability goes through the tuner verbs.
- Never modify the `synaptic-tuner/` submodule from this skill; it is a separate,
  experiment-agnostic repo.
- Signed cells pin config + gates + grader shas in the amendment doc and set
  `expected_config_sha`; never `--force-full-run` a signed cell.
- FalseQA text is never committed; keep row pools with restricted text untracked.
- The GPU verbs need `--i-know-this-runs-on-gpu`; treat that flag as a
  deliberate, per-run acknowledgement, not a default.
- A passing smoke readback is write-accuracy, not a behavioral effect; calibrate
  the dose to the direction's coherent window before the real ladder
  ([reference/dose-calibration.md](reference/dose-calibration.md)).
- **Any local run longer than about 15 minutes writes per-item results
  through the tuner's resumable run log** (`shared/utilities/run_log.py`
  `RunLog`: append + fsync per item, atomic tmp+replace summary write, one
  log per arm) instead of buffering results in memory and writing only at
  the end. This is the LOCAL analog of the "Modal cell gotchas" volume rule
  above -- the tuner-side counterpart of durably checkpointing a Modal
  Volume before GPU work starts, ported to a local 3090 process that has no
  volume to fall back on if it is killed. A held-out layer-contrast
  replication cell in this project has exactly the shape this closes a gap
  for (multiple arms, thousands of rows, hours of wall time per arm, one
  generate-then-grade pass per row): a kill anywhere in that loop without a
  run log loses the whole arm, not just the in-flight row. See
  `experiments/common/README-runlog.md` in the root repo for the import
  path and per-arm log-path convention, and
  `experiments/j-space-cross-family-layer-contrast/run_contrast.py` for a
  worked wiring (resume by default, `--fresh` to discard and restart).
  **Sign-pinned instruments must adopt this BEFORE sign**: once a cell's
  scripts are pinned in `instrument.modules` with a frozen sha, they cannot
  be patched mid-run to add resumability after a crash has already
  happened.
