---
name: mechinterp-cells
description: Author, organize, and launch tuner-backed mechanistic-interpretation cells (activation reading and writing) for the Epistemic-Humility project. Use when designing a new steering / extraction / probe-fit / gate-scoring cell, deciding where its config, direction, grader, and outputs live, or launching one locally or on Modal. This skill is about USING the synaptic-tuner `mechinterp` verbs via declarative recipe YAML plus project plug-ins; it never modifies the tuner submodule and never touches the frozen legacy machinery.
---

# MechInterp Cells

Use this skill to design and operate new activation-reading or
activation-writing cells through the `synaptic-tuner` `mechinterp` CLI family.
The project supplies rows, renders, graders, gates, and experiment organization;
the tuner owns generic execution through declarative YAML and public verbs.

The bespoke machinery under `archive/experiment/phase1/probe/steering/` is frozen for
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
- [../experiment-runner/reference/batched-generation.md](../experiment-runner/reference/batched-generation.md)
  - vLLM-first backend selection, parity exceptions, structured-output policy,
  batch-invariance smoke, and full-depth HF bridge.

## Default Workflow

For a new cell:

1. Read `organization.md` and decide the experiment slug, instrument type, and
   artifact homes.
2. Read `verbs-and-schemas.md` for the verb and config schema you need.
3. Select and register the backend before writing the GPU stage. New unsteered
   generation prefers vLLM; full-depth extraction prefers vLLM only after the
   model-specific bridge passes. Use the experiment-runner batching reference.
4. Prefer a `mechinterp-pipeline/v1` `pipeline.yaml` as the outer launch
   artifact. Read `pipeline-workflow.md` for stage patterns and command forms.
5. If using `erase_write`, read `dose-calibration.md` before choosing real
   strengths or setpoints.
6. If launching on Modal or any paid GPU lane, read `modal-launch.md` and the
   linked experiment-runner cloud checklist first.
7. Validate locally with dry-runs, parse checks, CPU stages, and smoke gates
   before any full GPU run.

For legacy-to-tuner cleanup, read `legacy-migration-map.md` and keep the frozen
legacy tree byte-stable unless the user explicitly requests historical
maintenance.

## Invariants

- Never edit frozen legacy files listed by
  `archive/experiment/phase1/probe/steering/LEGACY.md` while authoring new cells.
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
- Do not default to HF batch 1 for a new unsteered generation surface. Prefer
  pinned vLLM with `VLLM_BATCH_INVARIANT=1`, and use JSON-schema decoding when
  structure is an interface rather than a measured behavior. Keep the exact
  prior engine for parity-locked work. Native vLLM hidden-state extraction is
  allowed only after the model-specific layer, anchor, normalization, and
  estimator bridge in the experiment-runner batching reference passes.
- If Synaptic Tuner does not expose the required vLLM engine, treat that as a
  generic capability gap. Use the registered HF fallback or implement the
  engine generically in the tuner on its own branch; never hide a one-off
  backend inside an evidence experiment.
- **Local GPU runs execute in a pinned container** (binding invariant,
  2026-07-10): every local-3090 `mechinterp` GPU verb runs inside the pinned
  mechinterp runner image, never a bare shared conda environment. See
  [reference/modal-launch.md](reference/modal-launch.md) for the image
  location, the sha256-pinning convention, and the honored in-flight
  exception.
- **Any local run longer than about 15 minutes writes per-item results
  through the tuner's resumable run log** (`shared/utilities/run_log.py`
  `RunLog`: append + fsync per item, atomic tmp+replace summary write) rather
  than buffering results in memory and writing only at the end. This applies
  to any module, GPU or CPU, whose projected wall-clock exceeds about 15
  minutes, INCLUDING pure statistics/analysis passes with no GPU or model in
  the loop: a bootstrap-CI or aggregation script that buffers every row in
  memory for an hour before writing a summary is exactly as exposed to a kill
  as a generation loop is. An end-only output write on a run in that range is
  a build defect at pre-sign review, not a style preference. Sign-pinned
  instruments must adopt this BEFORE sign: a pinned script cannot be patched
  mid-run to add resumability after a crash has already happened, and
  `bin/exp sign` enforces it structurally: every entry in
  `instrument.modules` needs a matching `instrument.persistence` declaration
  (`persistence: incremental` with a `checkpoint_path`, or `persistence:
  short-run` with a measured smoke wall-clock) before it will pin the
  instrument, see the experiments SKILL.md "Persistence declarations"
  section. See `experiments/common/README-runlog.md` for the import path and
  per-arm log-path convention, and the mechinterp-cells
  `reference/organization.md` "Kill-resume smoke drill" section for the
  mandatory pre-sign drill on any `incremental` module.
- **Parallelize by default when it cannot influence results** (PI rule of
  thumb, 2026-07-20). If a harness's work units are independent (per-layer
  fits, per-rung scoring, batched generation) and every random draw is keyed
  by explicit identifiers (seed derived from stage/layer/purpose strings)
  rather than call order or shared RNG state, then parallel and serial
  execution are byte-identical and a serial-only implementation is a build
  gap, not a style choice. Build the executor in from the start (a
  `--workers N` flag, BLAS threads capped per worker, no full-cache copies
  per worker, `--workers 1` path preserved) and prove equivalence in the
  smoke by diffing `--workers 1` vs `--workers N` output. Lesson from
  correctness-subspace-overlap (2026-07-20): the module shipped serial-only,
  turning a roughly two-hour parallel job into a 14-hour run and forcing a
  kill, retrofit, and audited repin cycle after sign. Where order or shared
  state does matter (sequential dosing on a warm model, cross-item dedup),
  do not parallelize without an explicit equivalence argument.
- **Stage dosed RunLogs to a durable location BEFORE any worktree teardown**
  (lesson from rr-cross-family-raw-refusal, 2026-07-18: its llama dosed
  generation text lived only in gitignored `analysis/` inside the amendment
  worktree and was permanently lost when the worktree was removed, forcing a
  full GPU re-run). Copy the RunLogs to
  `/home/profsynapse/code/ehr-exhaust/<experiment-slug>/` (or the cell's
  registered durable dir) and record the staging path in the experiment's
  NOTEBOOK.md before `git worktree remove`.
- **A pre-registered gate that thresholds a geometry estimator (direction
  reliability, subspace overlap, principal angles, CKA, participation ratio,
  or similar) requires a pre-sign planted-signal validation**: show the
  estimator can reach the gate's pass threshold on synthetic data with a
  planted signal at matched n, dimensionality, and class balance, and that
  the null/no-signal case stays below it. Motivating case:
  `experiments/correctness-subspace-overlap/AMENDMENT.md` Outcome, whose
  k=8 reliability gate of 0.70 was unreachable for any signal, including a
  perfectly separable planted case (best planted reliability 0.104). A
  post-hoc red-team simulation showed the cell was destined for its
  middle-ground null before any data were seen.
