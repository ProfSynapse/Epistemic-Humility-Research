# Pipeline workflow

Read this when writing `pipeline.yaml`, running local stage checks, validating
example configs, or choosing direct verb commands.

## Pipeline config

A pipeline config has schema `mechinterp-pipeline/v1` and belongs beside the
experiment's cell configs, for example `experiments/<semantic-slug>/pipeline.yaml`.
Keep it generic: it may reference project-owned rows, renders, graders, and
gates, but the Synaptic Tuner runner remains experiment-agnostic.

Use pipeline stages to sequence:

- `kind: command` for CPU/local smokes, preflight checks, or deterministic
  project-side transforms.
- `kind: mechinterp.extract` for activation capture.
- `kind: mechinterp.probe-fit` for direction fitting.
- `kind: mechinterp.steer` for intervention cells. Put
  `execution.render_fn` in the steer config, or `render_fn` on the pipeline
  stage, so launchers do not need wrapper flags for project prompt rendering.
- `kind: mechinterp.dose-calibrate` for coherent-window dose ladders.
- `kind: mechinterp.score-gates` for declarative adjudication.

The pipeline YAML declares stages, stage configs, Modal image/GPU/timeout,
checkpoint paths, environment, and plug-in paths. CLI flags should supply
late-bound facts only: `--provider`, `--repo-commit`, `--only-step`,
`--from-step`, `--skip-step`, `--yes`, and the per-run GPU acknowledgement.

For project-local configs, set `runtime.workdir: ..` when the pipeline is
executed from the tuner checkout but stages must run against the research repo
root.

## CWD and PYTHONPATH

Run tuner commands from the repo root or experiment worktree root, not from
inside `synaptic-tuner/`. A cell's internal paths (`surface.rows_path`,
`execution.output_path`, `readouts[*].path`) are repo-root relative; `cd
synaptic-tuner` makes those paths resolve incorrectly.

Invoke the tuner as:

```bash
python synaptic-tuner/tuner.py ...
```

For parse-only import checks, put the tuner on `PYTHONPATH` instead of changing
directories:

```bash
PYTHONPATH=synaptic-tuner python -c "from MechInterp.config import load_steer_config; load_steer_config('experiments/example-cell/cell.yaml'); print('cell ok')"
PYTHONPATH=synaptic-tuner python -c "from MechInterp.stats.evaluator import load_gates_config; load_gates_config('experiments/example-cell/gates.yaml'); print('gates ok')"
```

For project render and grader modules:

```bash
PYTHONPATH=experiments/common/renders:experiments/common/graders
```

## Minimal pipeline commands

Inspect the exact stage plan without touching GPU or cloud:

```bash
python synaptic-tuner/tuner.py mechinterp run \
  --config experiments/<semantic-slug>/pipeline.yaml \
  --provider local \
  --dry-run
```

Run a CPU-only stage locally:

```bash
python synaptic-tuner/tuner.py mechinterp run \
  --config experiments/<semantic-slug>/pipeline.yaml \
  --provider local \
  --only-step fit \
  --yes
```

Submit a GPU pipeline to Modal from an exact pushed tuner commit:

```bash
python synaptic-tuner/tuner.py mechinterp run \
  --config experiments/<semantic-slug>/pipeline.yaml \
  --provider modal \
  --repo-commit <pushed-synaptic-tuner-sha> \
  --i-know-this-runs-on-gpu \
  --yes
```

Do not use Modal just to test CPU config plumbing. Run a local `command` stage
smoke first; reserve Modal for GPU-backed extract/steer/dose-calibrate after
the plan is clean and the exact commit is pushed.

## Direct verb sequence

Use lower-level verbs when debugging a stage directly:

```bash
# 1. Extract hidden states over a labeled row pool (GPU).
PYTHONPATH=experiments/common/renders python synaptic-tuner/tuner.py mechinterp extract \
  --mi-config experiments/<semantic-slug>/extract.yaml \
  --model <base-model> \
  --render-fn example_render:render \
  --i-know-this-runs-on-gpu

# 2. Fit a linear readout and freeze a direction (CPU).
python synaptic-tuner/tuner.py mechinterp probe-fit \
  --mi-config experiments/<semantic-slug>/probe_fit.yaml

# 3. Run the intervention cell: smoke first, then the full arms (GPU).
PYTHONPATH=experiments/common/renders python synaptic-tuner/tuner.py mechinterp steer \
  --mi-config experiments/<semantic-slug>/cell.yaml \
  --model <base-model> \
  --render-fn example_render:render \
  --i-know-this-runs-on-gpu

# 4. Calibrate a dose ladder before locking a real steer run (GPU).
PYTHONPATH=experiments/common/renders:experiments/common/graders \
python synaptic-tuner/tuner.py mechinterp dose-calibrate \
  --mi-config experiments/<semantic-slug>/dose_calibration.yaml \
  --model <base-model> \
  --i-know-this-runs-on-gpu

# 5. Adjudicate with declarative gates (CPU).
python synaptic-tuner/tuner.py mechinterp score-gates \
  --gates-config experiments/<semantic-slug>/gates.yaml \
  --rows-path experiments/<semantic-slug>/analysis/rows_out.jsonl
```

## Worked example

`experiments/example-cell/` is a complete, parseable teaching artifact against
the real tuner schema. It is not a registered instrument and should not be
launched as confirmatory. It includes:

- `cell.yaml` - six-block steer cell with erase-write setpoint, baseline,
  thresholded primary, seeded permuted control, and two-rung dose ladder.
- `gates.yaml` - reach, specificity, and readout-floor gates.
- `direction_stub.json` - `mechinterp-direction/v1` stub for schema checks.
- Shared example plug-ins under `experiments/common/graders/` and
  `experiments/common/renders/`.

CPU-side validation:

```bash
PYTHONPATH=synaptic-tuner python -c "from MechInterp.config import load_steer_config; load_steer_config('experiments/example-cell/cell.yaml'); print('cell ok')"
PYTHONPATH=synaptic-tuner python -c "from MechInterp.stats.evaluator import load_gates_config; load_gates_config('experiments/example-cell/gates.yaml'); print('gates ok')"
python synaptic-tuner/tuner.py mechinterp list-configs
```
