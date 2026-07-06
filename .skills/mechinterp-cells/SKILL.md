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
| `mechinterp extract` | yes (`--i-know-this-runs-on-gpu`) | generate over rows, capture hidden states to safetensors + a manifest |
| `mechinterp probe-fit` | no (CPU) | fit a linear readout from extracted activations, freeze a `mechinterp-direction/v1` JSON |
| `mechinterp steer` | yes (`--i-know-this-runs-on-gpu`) | run the six-block declarative intervention cell (smoke-gated) |
| `mechinterp score-gates` | no (CPU) | evaluate a `gates.yaml` against a per-row output JSONL |
| `mechinterp list-configs` | no (CPU) | list the bundled example recipes |

`extract` and `steer` refuse to run without `--i-know-this-runs-on-gpu`.
`probe-fit` and `score-gates` are CPU-only, so they are the parts you iterate on
locally without a GPU.

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
   present), and an optional `grader` (`module:callable`).
6. **smoke** - readback tolerances (`n_rows`, `write_rel_tol`, `write_abs_floor`,
   `offtarget_tol`). Before the full arms run, a small smoke pass applies the
   intervention and reads back the realized projection. `steer` refuses the full
   arms until a smoke passes for this exact config sha; `--force-full-run`
   overrides (do not use `--force-full-run` for a signed cell).

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
schema:

```bash
cd synaptic-tuner
python -c "from MechInterp.config import load_steer_config; \
  load_steer_config('../experiments/example-cell/cell.yaml'); print('cell ok')"
python -c "from MechInterp.stats.evaluator import load_gates_config; \
  load_gates_config('../experiments/example-cell/gates.yaml'); print('gates ok')"
python tuner.py mechinterp list-configs   # lists the bundled tuner templates
```

## Typical workflow

```bash
# 1. Extract hidden states over a labeled row pool (GPU).
cd synaptic-tuner && python tuner.py mechinterp extract \
  --mi-config ../experiments/<slug>/extract.yaml \
  --model <base-model> \
  --render-fn example_render:render \
  --i-know-this-runs-on-gpu

# 2. Fit a linear readout and freeze a direction (CPU).
python tuner.py mechinterp probe-fit \
  --mi-config ../experiments/<slug>/probe_fit.yaml

# 3. Run the intervention cell: smoke first, then the full arms (GPU).
python tuner.py mechinterp steer \
  --mi-config ../experiments/<slug>/cell.yaml \
  --model <base-model> \
  --render-fn example_render:render \
  --i-know-this-runs-on-gpu

# 4. Adjudicate with declarative gates (CPU).
python tuner.py mechinterp score-gates \
  --gates-config ../experiments/<slug>/gates.yaml \
  --rows-path ../experiments/<slug>/analysis/rows_out.jsonl
```

Run the `mechinterp` verbs from the `synaptic-tuner/` dir (that is where
`tuner.py` and the `MechInterp` package resolve); set `PYTHONPATH` to the project
graders/renders dirs so the flat plug-in module names resolve.

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
  `--i-know-this-runs-on-gpu`. Iterate the CPU verbs (`probe-fit`,
  `score-gates`) freely; they need no GPU.
- **Modal / cloud**: new cells launch through the tuner `mechinterp` verbs inside
  the Modal harness. Before any paid run, walk the wrapper-authoring checklist
  in the experiment-runner skill:
  [reference/runpod-modal-lanes.md](../experiment-runner/reference/runpod-modal-lanes.md)
  (five paid-run killers: idempotent clone under retries, argparse equals form
  for negative-leading values, spawn+detach reap-proofing, xet-off in image AND
  function, verify staging inputs pre-launch), plus the lane-selection rules in
  the same file (Modal A10G is for NEW surfaces; parity-locked cells stay on
  local 3090 / RunPod-3090). [reference/cloud-lane.md](../experiment-runner/reference/cloud-lane.md)
  covers the HF Jobs training lane. Do not duplicate those checklists here.

## Migration map (legacy -> tuner)

| Legacy file (frozen) | Tuner replacement |
|----------------------|-------------------|
| `confidence_steer.py` `SteeringHook` (`h += alpha*d`) | `mechinterp steer` with `law.kind: additive` (or `erase_write` for a setpoint), `law.position`, `law.generation_mode` |
| `amendment_*_grade_and_gates.py` | `mechinterp score-gates` + a project grader under `graders/` |
| `gpu_equivalence_cell.py` (CPU-vs-GPU hook check) | the built-in `steer` smoke readback / equivalence self-check |
| `*_extract.py`, `amendment_*_primed_extract.py` | `mechinterp extract` (+ `content_end_fn` plug-in) |
| `persist_probe_direction.py` (fit + persist direction) | `mechinterp probe-fit` -> frozen `mechinterp-direction/v1` JSON |
| `run_arm_a.py` / `run_arm_b.py` orchestration | `arms` block in one `cell.yaml` (fixed / score-thresholded / flagged / permuted-control) |

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
