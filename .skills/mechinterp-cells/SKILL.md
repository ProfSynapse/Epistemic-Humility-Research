---
name: mechinterp-cells
description: Author, organize, and launch tuner-backed mechanistic-interpretation cells (activation reading and writing) for the Epistemic-Humility project. Use when designing a new steering / extraction / probe-fit / gate-scoring cell, deciding where its config, direction, grader, and outputs live, or launching one locally or on Modal. This skill is about USING the synaptic-tuner `mechinterp` verbs via declarative recipe YAML plus project plug-ins; it never modifies the tuner submodule and never touches the frozen legacy machinery.
---

# MechInterp Cells

Use this skill to design and operate new activation-reading or
activation-writing cells through the `synaptic-tuner` `mechinterp` CLI family.
The project supplies rows, renders, graders, gates, and experiment organization;
the tuner owns generic execution through declarative YAML and public verbs.

The bespoke machinery under `experiment/phase1/probe/steering/` is frozen for
provenance. Existing legacy sweeps may still be driven by the `mech-interp-runner`
skill, but new cells use the tuner-backed path described here.

## First Decisions

1. Identify the task shape:
   - Activation writing, setpoint regulation, ablation, or steering:
     `mechinterp steer`.
   - Coherent-window / dose pilot for erase-write cells:
     `mechinterp dose-calibrate`.
   - Activation reading, hidden-state capture, and readout fitting:
     `mechinterp extract` then `mechinterp probe-fit`.
   - Per-row adjudication against declarative gates:
     `mechinterp score-gates`.
   - Multi-stage execution or Modal submission:
     `mechinterp run --config <pipeline.yaml>`.
2. Choose the right governance instrument before creating artifacts. Use the
   experiment-runner reference
   `../experiment-runner/reference/amendment-vs-lab-notebook.md` to distinguish
   a signed protocol/amendment from a lab-notebook diagnostic or smoke.
3. Place new evidence-producing work under `experiments/<semantic-slug>/`.
   Use semantic experiment slugs, not legacy letter-code slugs.

## What To Read

Read only the reference files needed for the task:

- [reference/verbs-and-schemas.md](reference/verbs-and-schemas.md) - mechinterp
  verbs, six-block steer cell schema, dose-calibration schema, gates, direction
  JSON, and plug-in callable contracts.
- [reference/pipeline-workflow.md](reference/pipeline-workflow.md) - pipeline
  config shape, repo-root CWD rules, `PYTHONPATH` rules, worked example checks,
  and typical local commands.
- [reference/organization.md](reference/organization.md) - experiments-first
  layout, signing pins, directions, shared renders/graders, outputs, and run
  tags.
- [reference/dose-calibration.md](reference/dose-calibration.md) - how to find
  the coherent erase-write window before locking a behavioral ladder.
- [reference/modal-launch.md](reference/modal-launch.md) - local vs Modal lanes
  and mechinterp-specific cloud gotchas. Also read the experiment-runner
  runpod-modal reference linked there before paid runs.
- [reference/legacy-migration-map.md](reference/legacy-migration-map.md) -
  frozen bespoke files, tuner replacements, and current genericization gaps.

## Default Workflow

For a new cell:

1. Read `organization.md` and decide the experiment slug, instrument type, and
   artifact homes.
2. Read `verbs-and-schemas.md` for the verb and config schema you need.
3. Prefer a `mechinterp-pipeline/v1` `pipeline.yaml` as the outer launch
   artifact. Read `pipeline-workflow.md` for stage patterns and command forms.
4. If using `erase_write`, read `dose-calibration.md` before choosing real
   strengths or setpoints.
5. If launching on Modal or any paid GPU lane, read `modal-launch.md` and the
   linked experiment-runner cloud checklist first.
6. Validate locally with dry-runs, parse checks, CPU stages, and smoke gates
   before any full GPU run.

For legacy-to-tuner cleanup, read `legacy-migration-map.md` and keep the frozen
legacy tree byte-stable unless the user explicitly requests historical
maintenance.

## Invariants

- Never edit frozen legacy files listed by
  `experiment/phase1/probe/steering/LEGACY.md` while authoring new cells.
- Never modify the `synaptic-tuner/` submodule from this skill; route project
  behavior through recipe YAML, rows, renders, graders, and gates.
- Run tuner commands from the repo root or experiment worktree root unless a
  reference explicitly says otherwise. Internal recipe paths are repo-root
  relative.
- Signed cells pin config, gates, grader, and render shas in the governed doc
  and set `surface.expected_config_sha`; do not use `--force-full-run` for a
  signed cell.
- Treat `--i-know-this-runs-on-gpu` as a deliberate per-run acknowledgement.
  `extract`, `steer`, and `dose-calibrate` are GPU paths; `probe-fit` and
  `score-gates` are CPU paths.
- A passing steer smoke proves write accuracy, not behavioral effect. Calibrate
  the coherent dose window before interpreting a ladder.
- Do not commit restricted row text, raw generations, or FalseQA text. Keep
  restricted row pools and per-row outputs untracked unless a governed manifest
  explicitly says otherwise.
- Do not move goalposts after results. Exploratory cells report as exploratory;
  claims require the pre-registered confirmatory surface.
