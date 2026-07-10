# Verbs and schemas

Read this when choosing a mechinterp verb, writing a cell config, defining gates,
or reasoning about direction JSONs and project plug-ins.

## Verbs

| Verb | GPU? | What it does |
|------|------|--------------|
| `mechinterp run` | depends on stages/provider | Run a multi-stage `mechinterp-pipeline/v1` YAML locally or submit it to Modal. |
| `mechinterp extract` | yes (`--i-know-this-runs-on-gpu`) | Generate over rows and capture hidden states to safetensors plus a manifest. |
| `mechinterp probe-fit` | no | Fit a linear readout from extracted activations and freeze a `mechinterp-direction/v1` JSON. |
| `mechinterp steer` | yes (`--i-know-this-runs-on-gpu`) | Run the six-block declarative intervention cell, smoke-gated before full arms. |
| `mechinterp dose-calibrate` | yes (`--i-know-this-runs-on-gpu`) | Run a resumable dose ladder over one or more frozen readouts, with per-row checkpoints and aggregate summaries. |
| `mechinterp score-gates` | no | Evaluate a `gates.yaml` against a per-row output JSONL. |
| `mechinterp list-configs` | no | List bundled example recipes. |

Prefer `mechinterp run --config <pipeline.yaml>` as the outer operator surface
for new cells. Use direct verbs for focused debugging, diagnostics, or truly
single-stage work.

## Six-block steer cell

A `steer` cell is described entirely by one recipe. Five blocks live in
`cell.yaml`; gates are scored separately so the run and adjudication stay
independent. Blocks map to `synaptic-tuner/MechInterp/config.py`
`SteerCellConfig`.

1. **surface** - `rows_path`, `generation` contract (`max_new_tokens`,
   `do_sample`, `temperature`, `top_p`, `seed`), a `seed`, and optional
   `expected_config_sha`. If set, the run aborts unless the recipe still hashes
   to that value. This is the goalpost lock.
2. **readouts** - frozen direction files the cell reads or writes along. Each
   entry is `{name, path}` pointing at a `mechinterp-direction/v1` JSON produced
   by `probe-fit`.
3. **law** - intervention law and shared parameters:
   - `kind`: `additive` (`h' = h + strength * d`) or `erase_write`
     (`h' = h - (h . d) d + strength * sigma * d`).
   - `readout`: name of the readout to intervene along.
   - `layer`: optional override; defaults to the readout's frozen layer.
   - `position`: `anchor`, `anchor_onward`, `final`, or `answer_window`.
     `answer_window` requires upstream `window_start`; the engine refuses to
     guess.
   - `generation_mode`: `anchor` edits only the prefill anchor; `gen_stream`
     edits every decode step.
4. **arms** - named strength overrides and row-selection rules. Each arm uses
   exactly one selection mode: fixed `strength`; `score_field` + `threshold` +
   `strength`; `flag_field`; or `permuted_control_of` + `control_seed`.
5. **execution** - `output_path`, `resume`, optional `grader`
   (`module:callable`), and optional recursive `redact_fields` for restricted
   fields that a grader may need transiently but checkpoints must not retain.
6. **smoke** - readback tolerances (`n_rows`, `write_rel_tol`,
   `write_abs_floor`, `offtarget_tol`). `steer` refuses full arms until a smoke
   passes for the exact config sha. Do not use `--force-full-run` for signed
   cells.

## Dose calibration schema

Use `mechinterp dose-calibrate` for new erase-write ladders instead of bespoke
scripts. It writes resumable row checkpoints and aggregate summaries.

- `surface` - row pool and generation contract, matching `steer`.
- `readouts` - frozen `mechinterp-direction/v1` files.
- `law` - intervention law, position, generation mode, and target readout.
  `law.readout: "*"` sweeps every declared readout.
- `calibration` - dose rungs plus optional row selection. `dose_kind:
  setpoint` is the default; for `erase_write`, the runner converts each dose to
  `strength = dose / sigma`. `dose_kind: strength` passes values directly.
- `execution` - per-row `output_path`, aggregate `summary_path`, `resume`,
  `render_fn`, optional `grader`, `batch_size`, and optional `redact_fields`.

Resume is keyed by `(readout, dose, row_key)` against `execution.output_path`.
Every completed row is fsynced as it lands. Treat the committed summary as a
calibration artifact, not a verdict. Read
[dose-calibration.md](dose-calibration.md) before choosing real setpoints.

## Gates

A `gates.yaml` declares named gates over per-row output, grouped by an `arm`
field. `overall_pass` is true only if every gate passes. Every stochastic
primitive is seeded.

- `count_flips` - rows whose outcome moved from one boolean state to another.
- `kill_diff_vs_control` - positive-count difference between a primary arm and a
  count-matched control, with a seeded row-bootstrap CI.
- `permutation_p` - one-sided permutation p-value for a count-matched positive
  count against a pool. The null is a count-matched draw, not a label-permutation
  mean-difference test.
- `auroc_floor` - tie-safe AUROC point estimate with a Hanley-McNeil analytic SE
  and a seeded bootstrap lower bound.

## Direction JSON

`probe-fit` writes `mechinterp-direction/v1`: `layer`, `hidden_dim`, `vector`
(unit-norm when `normalized`), `mu`, `sigma` (setpoint scale = readout-score
std), a `calibration` block, the fit `recipe`, and free-form `provenance`.
`steer` loads this object for interventions and external readers can consume it.

## Project plug-ins

The tuner has no project-specific concept of prompts, correctness, row splits,
or restricted fields. Name project code in recipes:

- `render_fn` (`module:callable`) maps a row dict to a prompt string and applies
  any chat template. Shared home: `experiments/common/renders/`.
- `content_end_fn` in extract recipes maps `(full_ids, prompt_len, tokenizer)`
  to the last content-token index.
- `grader` (`module:callable`) maps a per-row output dict to a grade dict merged
  into the row so gates can read it. Shared home: `experiments/common/graders/`.
- `rows_path` is any JSONL row pool with one object per row and a stable
  `row_key`, `id`, or `key`.

Resolve render and grader callables with `importlib.import_module` against
`sys.path`. Use flat module names and put their directories on `PYTHONPATH`
rather than adding `__init__.py` through frozen trees:

```bash
PYTHONPATH=experiments/common/graders:experiments/common/renders
```
