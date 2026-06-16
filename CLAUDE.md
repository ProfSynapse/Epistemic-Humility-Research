

<!-- PROJECT_ORCHESTRATOR_START -->
# Epistemic Humility Research Agent Orchestrator

You are operating in the root `Epistemic-Humility-Research` repository. These
instructions apply to this project root only. Do not install, copy, or rewrite
these project instructions inside `synaptic-tuner/`; that directory is a
separate git submodule with its own ownership boundary.

## Purpose

This repository supports research on epistemic humility in language models:
calibration, abstention, hallucination, sycophancy, uncertainty reporting, and
the tradeoffs introduced by training and fine-tuning. Treat it as a research
workspace first and a software project second: claims need provenance, scripts
need reproducibility, and changes should preserve the line from source evidence
to paper text to experiment artifacts.

## Boundaries

- Work from the root project unless a task explicitly requires entering another
  directory.
- `synaptic-tuner/` is a generic research-engine submodule. Use it as
  training/evaluation infrastructure when needed, but keep changes there generic
  enough for any research project to plug in. Do not install root-project
  instructions or Epistemic-specific orchestration inside it.
- Dot-directories are normally tool state or mirrors. Do not treat them as the
  canonical source unless the task is specifically about that tool integration.
- Generated outputs, caches, scratch space, and local run products are not source
  of truth unless a checked-in manifest or run record says otherwise.

## Navigation

Use artifact type to choose where to look:

- Orientation and contribution norms: root docs such as `README.md`,
  `CONTRIBUTING.md`, and nearby architecture notes.
- Research synthesis: `meta-analysis/`, especially evidence tables, analysis
  scripts, paper drafts, and provenance reports.
- Experiment design and execution: `experiment/`, especially protocols,
  architecture docs, phase directories, configs, recipes, and run records.
- Literature graph and concepts: `library/`, including paper notes, concept
  notes, schema docs, manifests, and fulltext where available.
- Datasets: `datasets/`, using dataset cards, loaders, schemas, and configs
  before reading raw rows.
- Skills and agent workflows: `.skills/` as canonical source, with generated
  mirrors under agent-specific directories.

When protocol, preregistration, or paper-claim files are involved, read the
local instructions in that area before editing. Treat registered study design as
governed: changes need explicit rationale, changelog, and user approval.

## Skills And When To Use Them

- `experiment-runner`: use for experiment orchestration, matrix/runnable-cell
  checks, lane preparation, run records, and experiment smoke tests.
- `knowledge-graph`: use for validating, exporting, analyzing, or searching the
  typed research graph.
- `kg-ingest`: use when adding or backfilling papers into the library as typed
  concepts, claims, mechanisms, evidence, and lineage edges.

Canonical skill source is `.skills/`. Mirrors under `.agents/skills/` and
`.claude/skills/` are generated. Do not hand-edit a mirror when the same file
exists under `.skills/`; edit canonical and run the sync check/write workflow.

Use the sync script only for root project skills and root project context. It
must not write into `synaptic-tuner/`.

## Evolving Skills

Treat skills as reusable project infrastructure:

- If you create a script, checklist, validator, or workflow that should be reused,
  place it in the relevant skill rather than leaving it as a one-off command.
- If a workflow does not fit an existing skill, create a new focused skill instead
  of overloading an unrelated one.
- If you discover a durable gotcha, invariant, or verification habit, update the
  relevant skill so future agents inherit it.
- Keep skills procedural and general. Put transient run state, local paths, and
  one-off conclusions in ordinary project docs or run records, not in timeless
  skill instructions.

## Search And Traversal

Prefer bounded, structure-aware search before broad text search. Use the local
KG/search tooling when available, then use scoped `rg` over the files it returns
when raw matching is still needed.

When investigating behavior, trace artifacts into their downstream consumer:
config -> builder/evaluator -> generated file -> trainer/eval loader -> tests.
Severity follows the crash trace, not the layer where a defect is first noticed.

For data artifacts, search metadata, schemas, configs, loaders, fixtures, and
dataset cards first. Read raw rows only when the task specifically requires row
inspection or fixture debugging.

## Research Guardrails

- Do not commit or redistribute restricted or gitignored data.
- Keep exact provenance for quantitative claims, dataset transformations, and
  reported results.
- Prefer deterministic scripts, manifests, and tests over manual result edits.
- Preserve registered protocols and paper claims unless the user explicitly asks
  for a governed revision.
- When tests appear absent or oddly skipped, verify with an explicit test file or
  non-wrapper command before concluding there is no test coverage.
<!-- PROJECT_ORCHESTRATOR_END -->
