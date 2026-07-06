

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

## Environment

- The canonical working checkout is `/home/profsynapse/code/Epistemic-Humility-Research`
  (ext4). The `/mnt/f/Code/Epistemic-Humility-Research` mount is a FROZEN backup;
  do not run experiments or commit from it. The shell may start with its cwd at
  the `/mnt/f` path and reset there between calls, so always `cd` to the canonical
  checkout explicitly. Amendment worktrees live under
  `/home/profsynapse/code/ehr-worktrees/`.

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
- New experiments (any evidence-producing type: steering cell, training run,
  eval, probe-fit, lab diagnostic): the experiments-first tree `experiments/`,
  one self-contained directory per experiment holding a signed `AMENDMENT.md`, a
  machine-readable `experiment.yaml` manifest, pinned instrument configs, and a
  generated registry. Scaffold and manage them with `bin/exp` (the `experiments`
  skill). This is where new evidence-producing work goes.
- Locked Phase 1 protocol and its records: `experiment/`, especially protocols,
  architecture docs, phase directories, configs, recipes, and run records. This
  tree is retained for the locked Phase 1 matrix and its historical amendments;
  do not add new experiments here, use `experiments/` instead.
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
- `experiments`: use to scaffold, sign, list, show, resolve, and validate a new
  experiment of any type under `experiments/<slug>/`, and to regenerate the
  experiments registry. New amendments go through `bin/exp new/sign/resolve` with
  the `AMENDMENT.md` and `experiment.yaml` manifest co-located in the experiment
  directory. Pick the tier first with the experiment-runner
  `reference/amendment-vs-lab-notebook.md`.
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

- READ BEFORE YOU CITE. Before stating any fact about a prior experiment or
  amendment (its design, mechanism, checkpoint, gates, result, verdict, or what
  it "showed" / "proved" / "worked"), open and read its governed doc first:
  `experiment/protocol/AMENDMENT-*.md` (pre-migration) or
  `experiments/<slug>/AMENDMENT.md` (new layout). The amendment/protocol docs are
  the SOLE source of truth for experimental facts. Memory, session notes, the
  knowledge graph, prior chat summaries, and this file's Retrieved/Working Memory
  are navigation aids ONLY: they point you to the doc, they are never themselves
  citable as an experimental result, and they may be stale or imprecise. This
  applies with special force to cross-experiment claims ("X actuated because Y",
  "these all null for the same reason"): reconstruct the taxonomy from each doc,
  never pattern-match it from memory. Every delegation prompt that references a
  prior result MUST instruct the subagent to read that doc first and MUST NOT
  hand it a remembered interpretation to cement. If you cannot cite the doc line
  you read it from, you do not know it yet.
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

## Delegation And Context Protection (Lead = Orchestrator)

The lead session is an ORCHESTRATOR, not a worker. Its context is the scarcest
resource in the project: it holds protocol authority, cross-amendment memory,
and the user relationship. Protect it.

- Default to delegation. Any task that is (a) well-specified, (b) verifiable
  from its artifacts, and (c) longer than a few tool calls goes to a subagent.
  The lead writes the spec, spawns the agent (background for long GPU/build
  work), and reviews the structured report — it does not read the interim file
  dumps, run the loops, or debug line-by-line unless review fails.
- The lead KEEPS (never delegates): protocol interpretation and verdicts,
  amendment signing, gate/falsifier adjudication, git commit / PR / merge of
  evidence, GPU or cloud launch approval relays, memory writes, and anything
  lifted to the user for decision.
- Project agent roles live in `.claude/agents/` (one file per role, with a
  pinned model tier). Use them instead of ad-hoc general-purpose prompts when
  a task matches a role; extend a role file when a new durable task shape
  appears.
- Assign the model to the task's judgment density, not its length:
  - `opus` — adversarial review, oracle-leak/circularity audits, design work,
    gnarly failure diagnosis. Anything where a wrong-but-plausible answer is
    expensive.
  - `sonnet` — skilled constrained execution: harness building against a
    locked spec, scoring/stats, KG ingest, doc drafting.
  - `haiku` — mechanical sweeps: locate/inventory/format checks, read-only
    search fan-outs.
- Every delegation prompt restates the binding invariants for that task
  (locked constants, no-goalpost rule, KG-search-first, no-commit rule, output
  contract) — subagents do not inherit lead context and must not rediscover or
  reinterpret the protocol.
- Subagents report; the lead adjudicates. A subagent's final message is
  evidence to verify (spot-check artifacts, re-derive one number), never a
  verdict to relay verbatim. Nulls and falsifiers are reported straight.
- Do not poll harness-tracked background agents; completion notifications
  arrive. While one runs, the lead stays free for the user: guiding, reviewing,
  and lifting decisions up rather than doing the work itself.
<!-- PROJECT_ORCHESTRATOR_END -->
