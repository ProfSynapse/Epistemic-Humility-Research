---
name: steering-cell
description: Build and run a declarative steering/readout cell for the Epistemic-Humility probe from a YAML config instead of a bespoke harness. Use when a new steering or readout amendment (activation steering, setpoint/couple write, additive push, readout-only extraction, permuted control, dose ladder, bidirectional) would otherwise mean writing a fresh multi-hour build_maps/steer_generate/grade harness. Covers the six-block cell model (surface/readouts/law/arms/lane/gates), the YAML schema, the smoke-first readback discipline, the sign-then-pin-config-sha practice, the generic Modal launch, and the known cloud/GPU gotchas. This skill is about USING the checked-in steer_cell runner + gate primitives via CLI and YAML - it never modifies the synaptic-tuner submodule.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Steering-Cell Runner

A steering or readout experiment on the Phase 1 probe is a **cell**: a declarative
YAML config that the generic runner executes. This turns a new steering amendment
into a config plus a signing, instead of a fresh `amendment_XX_build_maps.py` +
`amendment_XX_steer_generate.py` + `amendment_XX_grade_and_gates.py` harness. The
AN couple write, the AL additive push, a readout-only extraction, and a permuted
control are all arms over one set of blocks.

The runner reuses the item-11-certified steering engine
(`confidence_steer.SteeringHook` / `steering_common.GenerationHookController`) by
import - it never re-implements the hook math.

## Start Here

Read only what the current task needs.

| Task | Load |
|------|------|
| Understand the six blocks and write a cell.yaml | [reference/cell-schema.md](reference/cell-schema.md) |
| Write a gates.yaml and score it | [reference/gates-schema.md](reference/gates-schema.md) |
| Run smoke-first, then full arms; sign + pin the config sha | [reference/run-and-sign.md](reference/run-and-sign.md) |
| Launch the cell on Modal (cloud lane) | [reference/modal-launch.md](reference/modal-launch.md) |
| Hit a cloud/GPU failure (xet hang, PEFT unwrap, clone idempotency, reaped run) | [reference/gotchas.md](reference/gotchas.md) |

## Files (checked in, canonical under `.skills/steering-cell/`, runner under the probe)

| File | Role |
|------|------|
| `experiment/phase1/probe/steering/steer_cell.py` | the runner: `plan` (CPU) and `run --config cell.yaml [--arm TAG] [--smoke]` |
| `experiment/phase1/probe/steering/gate_primitives.py` | pure gate library: count_flips, kill_diff_vs_control, permutation_p, auroc_floor, threshold helpers |
| `experiment/phase1/probe/steering/score_gates.py` | `--config cell.yaml --gates gates.yaml` composes the primitives declaratively |
| `experiment/phase1/probe/cloud/modal_steer_cell.py` | ONE parameterized Modal wrapper (`--config --repo-commit --staging-prefix`) |
| `experiment/phase1/probe/steering/configs/example_*.yaml` | worked examples (AN-style + readout-only); DOCUMENTATION, not registered instruments |

## The Six-Block Cell Model

1. **surface** - what to generate over: the rows file (questions + baseline
   grades), the generation contract (model, optional `adapter@revision`,
   system-prompt ref, `enable_thinking`, decode params, `max_new_tokens`, seed),
   and resume semantics (rows already in the output `rows.jsonl` are skipped).
2. **readouts** - frozen direction JSONs scored at the pre-generation anchor.
   Each yields a per-row `<name>_raw` projection and, given `mu`/`sigma`, a
   `<name>_z`. The law's selection references these.
3. **law** - how a row is selected (`expression` over readout scores, a
   `flag_file`, a seeded `permuted` control, or `all`) and actuated (`additive`
   `alpha*d`, `setpoint` erase-and-write `g*sigma`, or `none` for readout-only)
   at a `gain`, a `position` policy, and the readout's layer.
4. **arms** - named runs = law overrides + a row subset + a tag (baseline,
   primary, permuted control, dose ladder, bidirectional).
5. **lane** - local GPU (`steer_cell.py run`) or cloud (`modal_steer_cell.py`).
   The runner is lane-agnostic; the Modal wrapper is a thin harness around it.
6. **gates** - scored separately by `score_gates.py` over the runner's
   provenance, via a `gates.yaml` composing `gate_primitives`.

## Quick Commands

| Task | Command (run from `experiment/phase1/probe`) |
|------|------|
| Parse + report a cell, no model load (CPU) | `python3 steering/steer_cell.py plan --config steering/configs/my_cell.yaml` |
| Smoke one arm (N rows + readback; records a pass state) | `python3 steering/steer_cell.py run --config steering/configs/my_cell.yaml --arm primary --smoke` |
| Run one arm full (refuses without a recorded smoke pass) | `python3 steering/steer_cell.py run --config steering/configs/my_cell.yaml --arm primary` |
| Run every arm | `python3 steering/steer_cell.py run --config steering/configs/my_cell.yaml` |
| Score gates over the provenance | `python3 steering/score_gates.py --config steering/configs/my_cell.yaml --gates steering/configs/my_gates.yaml` |
| Run the CPU unit tests | `python3 steering/tests/test_gate_primitives.py && python3 steering/tests/test_steer_cell_cpu.py && python3 steering/tests/test_score_gates_cpu.py` |

## Core Invariants

- **Smoke first is enforced.** The runner refuses a full arm unless a `--smoke`
  pass for that arm is on record in `smoke_state.json` (bypass only with
  `--force-no-smoke`, and only knowingly). The smoke re-reads the post-write
  anchor coordinate and asserts it landed at the commanded value within tolerance,
  and that off-target rows did not move. A write bug never burns the full sweep.
- **Sign, then pin the config sha.** The amendment doc records the sha256 of the
  exact `cell.yaml` it signed (put it in the config as `expected_config_sha`). The
  runner's `run` path is FATAL on a mismatch, before any model load, so a signed
  run can never diverge from the reviewed config. `plan` only warns, so an author
  can inspect an edited cell.
- **Analysis outputs are UNTRACKED.** Everything the runner writes lands under an
  untracked analysis dir (`analysis/steer_cells/<name>/` by default). Never commit
  generations, readbacks, or gate reports; never commit FalseQA question text.
- **The runner is generic.** No checkpoint names or amendment constants live in
  `steer_cell.py`, `modal_steer_cell.py`, or `gate_primitives.py` - only in the
  cell configs. A cell for another research project is a new YAML, not a code fork.
- **Headline vs exploratory is unchanged.** A cell is an amendment surface: it
  pre-states its prediction, falsifier, and gate thresholds before the run, and
  never moves the goalposts. Promote an exploratory win to a claim only via a
  registered confirmatory replication. See the experiment-runner skill's
  `reference/amendment-vs-lab-notebook.md`.
- **Never write into `synaptic-tuner/`.** This skill and its runner live entirely
  in the root project.

## Editing This Skill

Canonical source is `.skills/steering-cell/`. After any edit:

```bash
python3 bin/sync_skills.py --write --skill steering-cell
python3 bin/sync_skills.py --check --skill steering-cell
```

Never hand-edit the `.claude/` or `.agents/` mirrors.
