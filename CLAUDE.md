

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
  checks, lane preparation, run records, and experiment smoke tests. Before
  changing a protocol, adding a cell/arm, or recording experiment work, consult
  its `reference/amendment-vs-lab-notebook.md` to pick the right instrument
  (signed protocol revision vs Amendment vs lab-notebook entry) — do not mint a
  new amendment for a smoke, diagnostic, re-run, or authorized-knob tuning.
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

The typed knowledge graph is the default entry point for ALL exploration:
locating papers, concepts, claims, mechanisms, experiment artifacts, or code.
Before reaching for `rg`, grep, or an Explore/general-purpose search subagent,
run the local KG search first:

```bash
bin/search <query terms> --limit 10         # macOS/Linux
bin\search.cmd <query terms> --limit 10      # Windows
```

This wraps `.agents/skills/knowledge-graph/scripts/kg_search.py` and returns
ranked, graph-aware hits (file + line + typed edges). Only after the KG search
returns its candidate set should you fall back to scoped `rg` over those files,
or dispatch a search subagent, when raw text matching is still needed. Do not
open with broad text search or a fan-out search agent on the first move. See the
`knowledge-graph` skill for indexing, feedback, and validation commands.

This directive binds subagents too. Any agent dispatched to find, locate, or
explore anything in this repo must run `bin/search` first and pass through its
candidate set before broad text search. When you spawn a search/explore
subagent, restate this KG-search-first rule in its prompt so it is never lost.

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
- Match the instrument to the work (see the experiment-runner
  `reference/amendment-vs-lab-notebook.md`): the locked headline matrix is the
  only confirmatory surface and its numbers are the only claims; amendment cells
  are exploratory and reported separately, never pooled with the headline. Every
  amendment pre-states a prediction, a falsifier, and its gates before the run,
  and never moves the goalposts after the result. Promote an exploratory win to a
  claim only via a confirmatory replication (fresh seeds / larger model /
  held-out) registered before running it.
- When tests appear absent or oddly skipped, verify with an explicit test file or
  non-wrapper command before concluding there is no test coverage.
<!-- PROJECT_ORCHESTRATOR_END -->
