

<!-- PROJECT_ORCHESTRATOR_START -->
# Epistemic Humility Research Agent Orchestrator

You are operating in the root `Epistemic-Humility-Research` repository. These
instructions apply to this project root only. Do not install, copy, or rewrite
these project instructions inside `synaptic-tuner/`; that directory is a
separate git submodule with its own ownership boundary.

## Operating Rules (hook-enforced where possible)

The highest-frequency mistakes, several blocked by PreToolUse hooks that name
the correct alternative. A blocked call means RE-ROUTE, not retry. These are
also re-injected into context after every compaction (the moment they are most
often forgotten).

1. SEARCH FIRST. Run `bin/search <query> --limit 10` before any `rg`/`grep`/
   `find`/`rtk grep`; restate this rule in every search subagent's prompt.
   [`bin_search_guard`: exploratory search blocked; conscious bypass `EHR_SEARCH_OK=1`]
2. PROTECTED main. Do experiment/feature work on a BRANCH in its own worktree,
   merged via PR. Governed evidence (amendments, `experiments/<slug>/`,
   `docs/protocols/`), skills, and the submodule are ALWAYS PR-gated.
   A SHORT list goes direct to main: session notes, `TODO.md`, `docs/ideas/`,
   backlog edits, the cross-experiment tracking docs, and KG nodes under
   `library/`. That list is not a paraphrase to reason from; the authoritative
   table is `.skills/pr-workflow/SKILL.md` ("What goes where") plus the
   living-docs split in `.skills/experiment-wrapup/SKILL.md`. Read it before
   concluding something cannot go to main.
   [`main_protect_guard`: blocked; sanctioned bypass `EHR_MAIN_OK=1`]
3. CANONICAL CHECKOUT ONLY. Work in `/home/profsynapse/code/Epistemic-Humility-
   Research`; `/mnt/f/...` is a FROZEN read-only backup. `cd` to canonical
   explicitly (the shell may start on /mnt/f). [`path_write_guard`: frozen-backup writes blocked]
4. NO TUNER POLLUTION. Never install root-project instructions/orchestration
   (`CLAUDE.md`, `AGENTS.md`, `.claude`/`.agents`/`.codex`/`.skills`) inside
   `synaptic-tuner/`. [`path_write_guard`: blocked]
5. NO MIRROR EDITS. Edit canonical `.skills/` (and `AGENTS.md`), then
   `python3 bin/sync_skills.py --write`; never hand-edit `CLAUDE.md` or a skill
   mirror. [`block_claudemd_write`: blocked]
6. READ BEFORE YOU CITE. State no experimental fact from memory/notes/KG/summary
   — open `experiments/<slug>/AMENDMENT.md` first. Never announce a verdict
   (SUCCESS / FAILED / FALSIFIED / INCONCLUSIVE / MIXED) from a remembered or
   paraphrased rule — RUN the registered roll-up instrument (e.g.
   `cross_family_rollup.py`) and quote its output. (Not hook-enforceable — this
   one is on you; re-injected after every compaction.)
7. GOVERNED-DOC DISCIPLINE. Before drafting/editing a protocol, gate, or
   amendment, read the governing reference under
   `.skills/experiment-runner/reference/` (amendment-vs-lab-notebook,
   gate-diagnosticity, operator-discipline, protocol-amendment-template).
   After editing an `experiment.yaml`, validate (`bin/validate-experiments`) and
   regen the registry (`bin/exp regen`). [`post_write_reminders`: non-blocking
   nudge; `.githooks/pre-commit` hard-enforces validate + regen at commit]
8. CHECK THE SKILL BEFORE YOU ASSERT A PROCESS RULE. Any claim about how this
   repo works (what may be committed where, which tool is canonical, what a
   command does, whether something is allowed) comes from the skill or script
   that governs it, not from memory and not from these summaries. `.skills/` is
   the canonical tree; `bin/search` finds it. Two recurring failures this rule
   exists to stop: (a) refusing or re-routing work because a remembered rule
   seemed to forbid it, when the governing skill has an explicit carve-out;
   (b) trusting a tool whose own docstring records that it lies. `rtk`-proxied
   `diff` prints a false "Files are identical" banner, and `rtk`-proxied
   `pytest` on a directory glob reports "No tests collected" with exit 0. Verify
   structurally (sha256, `yaml.safe_load`, `json.load`, explicit file paths)
   rather than by scraping proxied output or trusting an exit code.
   (Not hook-enforceable. Re-injected after every compaction.)

## Purpose

This repository supports research on epistemic humility in language models. The
program has one through-line: small open models represent more about their own
ignorance than they say, and training moves the policy without reliably wiring
that internal signal to stated confidence or action. So read the signal directly
and wire it to behavior instead.

### The architecture under test

A SENSOR feeding a SEPARATE ACTUATOR, in three steps, repeated per model family:

1. READ. Fit a known-unknown (KU) direction from the residual stream and show it
   discriminates on held-out rows.
2. ACTUATOR. Fit a refusal/caution direction in that same model, orthogonalized
   against the KU direction, and find a dose at which pushing it produces a
   coherent abstention rather than a collapse.
3. WIRE. Gate the actuator on a threshold applied to the standardized KU
   readout, so it fires only where the read crosses. Then evaluate held-out.

Two things this frame rules out, both of which have been asserted here by
mistake and cost real time:

- The read axis and the write axis are NOT the same direction. The actuator is
  constructed orthogonal to the sensor on purpose. "Read a direction, then push
  along it" is a wrong description of every gated experiment in this repo.
- The write site is NOT assumed to be one shared place. It is searched per
  family. Relative depth is the best predictor found so far and it gives a band,
  not a site.

### The open question

Whether steps 2 and 3 reduce to a per-model RECIPE, that is, a procedure someone
can follow to locate and test the actuator in roughly any open-weight model. Not
a universal site, and not a universal dose. Step 1 already transfers. Choosing
the write site is the unsolved step, and it is the bottleneck on the whole
program.

### Where the program is actually stated

Do not restate the mission, the scoreboard, or any per-family status from memory
or from this file. This section is a pointer, not a source. In freshness order:

- `docs/research-trajectory.md` (current through-line; canonical entry point)
- `papers/paper-5-actuation/manuscript.md` (the actuation half; the
  sensor/actuator architecture is section 3.2 "Readouts and directions")
- `papers/paper-4-two-signal-readout/manuscript.md` (the read half)
- `papers/series/plan.md` (series roadmap; still uses the retired "doubt"
  vocabulary that `papers/common/terminology.md` replaced with known-unknown)
- `TODO.md` (live backlog, including the write-criterion line)

Per-family status, doses, sites, and verdicts live ONLY in
`experiments/<slug>/AMENDMENT.md`. See operating rule 6.

Treat this as a research workspace first and a software project second: claims
need provenance, scripts need reproducibility, and changes should preserve the
line from source evidence to paper text to experiment artifacts.

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
  scripts, and source-of-record synthesis apparatus.
- Paper production: `papers/`, organized one directory per paper with
  `manuscript.md`, `analysis/`, `figures/`, `scripts/`, and paper-specific
  `notes/`. Shared writing conventions live in `papers/common/`; series-level
  planning lives in `papers/series/`.
- Notes by type: `docs/sessions/` for chronological session logs,
  `experiments/<slug>/RUNBOOK.md` and `experiments/<slug>/PLAN.md` for reusable
  experiment-local operating specs, and `library/notes/` for KG-backed
  literature/internal synthesis notes.
- New experiments (any evidence-producing type: steering cell, training run,
  eval, probe-fit, lab diagnostic): the experiments-first tree `experiments/`,
  one self-contained directory per experiment holding a signed `AMENDMENT.md`, a
  machine-readable `experiment.yaml` manifest, pinned instrument configs, and a
  generated registry. Scaffold and manage them with `bin/exp` (the `experiments`
  skill). This is where new evidence-producing work goes.
- Locked locked training-regimen protocol and its records: `experiment/`, especially protocols,
  architecture docs, phase directories, configs, recipes, and run records. This
  tree is retained for the locked training-regimen matrix and its historical amendments;
  do not add new experiments here, use `experiments/` instead.
- Literature graph and concepts: `library/`, including paper notes, concept
  notes, schema docs, manifests, and fulltext where available.
- Datasets: `datasets/`, using dataset cards, loaders, schemas, and configs
  before reading raw rows.
- Skills and agent workflows: `.skills/` as canonical source, with generated
  mirrors under agent-specific directories.
- Archive: `archive/` holds superseded files retained for provenance. Do not use
  archived files as current sources of truth unless the citing text explicitly
  says it is referring to a superseded or retired artifact.

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
- `mechinterp-cells`: use when authoring, organizing, or launching a
  tuner-backed mech-interp cell (steering / extraction / probe-fit /
  gate-scoring via declarative recipe YAML); includes the dose-calibration and
  data-containment rules. Never modifies the tuner submodule or the frozen
  legacy machinery.
- `mech-interp-runner`: use for the legacy local mech-interp sweep machinery
  (candidate inventories, causal-pilot planning, offline aggregation) of
  already-signed amendments; new cell work goes through `mechinterp-cells`.
- `family-atlas`: use when a new model/family/size enters the program, before
  designing any per-family actuation cell; runs the standard full-depth
  read-atlas (workspace profile + three-axis read panel) whose resolved rows
  land in `docs/atlas/family-layer-map.md`. Layer choices are never ported
  across families.
- `data-exhaust`: use when packaging a terminal experiment's row-level exhaust
  as a public HF dataset (license gate, build, verify, dry-run card, upload);
  fail-closed on unaudited sources, and upload only after the user approves
  the dry-run card.
- `pr-workflow`: standing discipline for branches, worktrees, commits, and PR
  merges; read before spawning a file-writing subagent, committing
  housekeeping docs, or merging PRs.
- `experiment-wrapup`: the mechanical downstream half of a resolve, run AFTER
  the lead has adjudicated the verdict/falsifier/scores - write the AMENDMENT
  Outcome, `bin/exp resolve`, update the family-layer-map and
  prediction-scoreboard registries, open the resolve PR, commit the living
  tracking docs to main, hand off KG ingest. Delegable to a sonnet/haiku
  subagent given a locked adjudication packet. It never decides the verdict or
  the scores; those are lead-only inputs. Keep for the lead: the adjudication
  itself, the red-team decision, and the PR merge (needs user approval).

Canonical skill source is `.skills/`. Mirrors under `.agents/skills/`,
`.claude/skills/`, and `.codex/skills/` are generated. Do not hand-edit a
mirror when the same file exists under `.skills/`; edit canonical and run the
sync check/write workflow. A PreToolUse hook blocks direct edits to CLAUDE.md
(a generated mirror of AGENTS.md) and to the skill mirrors, and points back to
the canonical source plus the sync step.

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
  `experiments/<slug>/AMENDMENT.md`. The amendment/protocol docs are
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
