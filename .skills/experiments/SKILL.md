---
name: experiments
description: Lifecycle tooling for the experiments-first repo layout - one self-contained directory per evidence-producing experiment (steer cell, training run, eval, probe-fit, or lab diagnostic) under experiments/, each with a signed AMENDMENT.md, a thin machine-readable experiment.yaml manifest, pinned instrument configs, and generated indices. Use to scaffold, sign, list, show, resolve, and validate experiments, to regenerate the registry, and to understand the draft -> sign -> run -> resolve lifecycle and the shared-input promotion rule. The bin/exp wrapper runs these scripts; validation and registry regeneration run at commit time via .githooks/pre-commit.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Experiments Lifecycle

The repo keeps one self-contained directory per evidence-producing experiment
under a top-level `experiments/` tree. Any experiment type belongs here: a
steering cell, a training run, an eval, a probe-fit, or a lab diagnostic. This
skill is the tooling around that layout: it scaffolds a new experiment, pins its
instrument at signing, tracks its status, and regenerates the human and machine
registries from the manifests. It never launches or scores an experiment; that is
the job of the type-specific runner skills.

## Start Here

| Task | Do |
|------|----|
| Understand the on-disk layout of one experiment | read [Layout](#layout) |
| Understand the manifest fields | read [Manifest schema](#manifest-schema) |
| Move an experiment through its states | read [Lifecycle](#lifecycle) |
| Run a command | read [Command reference](#command-reference) |
| Share an artifact between two experiments | read [Promotion rule](#promotion-rule-for-shared-inputs) |
| Understand how indices stay correct | read [Generated indices](#generated-indices) |

## Layout

```
experiments/
  REGISTRY.md          # GENERATED human table (never hand-edit)
  registry.json        # GENERATED machine dump (never hand-edit)
  <slug>/              # one experiment; dir name == manifest slug
    experiment.yaml    # thin machine-readable manifest (SSOT for state)
    AMENDMENT.md       # signed prose: motivation, design, prediction, falsifier, gates, outcome
    NOTEBOOK.md        # running lab log
    cell.yaml          # instrument config(s), pinned at signing
    gates.yaml         # pre-stated pass/fail thresholds (when applicable)
    .gitignore         # ignores directions/ and analysis/
    analysis/          # untracked local scratch (not committed)
    directions/        # gitignored fitted-direction data
  common/              # artifacts promoted for use by >1 experiment (see promotion rule)
```

Prose lives in `AMENDMENT.md`; machine state lives in `experiment.yaml`. Never
duplicate the prose into the manifest. The registry files are generated from the
manifests and are the only files you must not edit by hand.

A teaching or example artifact sets `registered: false` in its manifest. It still
validates structurally but is excluded from claim requirements (it does not need
a prediction, falsifier, or verdict) and should not be read as evidence. It still
appears in the generated registry, marked `teaching artifact:`, so the inventory
stays complete.

`experiments/common/` is a reserved directory, not an experiment: it is the
shared cross-experiment code home (`graders/`, `renders/`, and promoted
`directions/`). It carries no manifest and is excluded from validation, the
manifest scan, and the registry.

## Manifest schema

`experiment.yaml` is the single source of truth for machine-readable state:

```yaml
slug: <dir name>                 # must equal the directory name
type: steer-cell | training-run | eval | probe-fit | lab-diagnostic
status: draft | signed | running | resolved | null-result | falsified
registered: true                 # false = teaching/example, excluded from claims
question: <one sentence>
prediction: <one sentence>       # required to sign
falsifier: <one sentence>        # required to sign
checkpoint: {repo: ..., revision: ...}   # optional
instrument:
  configs: [cell.yaml, gates.yaml]       # instrument files pinned at signing
  modules: []                    # optional grader/render modules, pinned too
  pins: {}                       # relpath -> sha256, filled by `exp sign`
inputs: []                       # repo-relative paths this experiment consumes
pr: <int>                        # optional, the PR that carries this experiment
verdict: <one sentence>          # filled at resolve
kg: []                           # typed KG node ids, filled at/after resolve
```

`status`, `pins`, and `verdict` are managed by the CLI; do not hand-edit them.

## Lifecycle

```
draft ──sign──> signed ──run──> running ──resolve──> resolved | null-result | falsified
```

1. **draft** (`exp new`): scaffold the directory. Fill `question`, `prediction`,
   `falsifier`, the instrument `configs`, and write the `AMENDMENT.md` design.
   Nothing is pinned yet.
2. **signed** (`exp sign`): the instrument is frozen. `exp sign` computes the
   sha256 of every file in `instrument.configs` (and any listed `modules`),
   records them in `instrument.pins`, and flips the status to `signed`. From here
   on, `exp validate` fails if a pinned file changes, so the goalposts cannot
   drift silently. Signing refuses if `prediction` or `falsifier` is empty.
3. **running**: set by hand when the run is launched (the runner skills own the
   launch). Pins are still enforced.
4. **resolved / null-result / falsified** (`exp resolve`): stamp the one-sentence
   `verdict` and the terminal status. `exp resolve` prints a kg-ingest checklist;
   ingest the result as typed KG nodes and record their ids in `kg:`.

## Generated indices

`experiments/REGISTRY.md` (human table) and `experiments/registry.json` (full
machine dump) are GENERATED from the manifests by `exp regen`, sorted by slug and
free of timestamps so they are byte-stable. Both carry a "GENERATED - do not
edit" header. Never hand-edit them: change a manifest, then run `bin/exp regen`
and stage the result. The reserved `experiments/common/` directory is skipped,
and `registered: false` rows are rendered with a `teaching artifact:` marker, so
the registry stays a complete inventory without presenting teaching artifacts as
claims.

The `.githooks/pre-commit` hook enforces this. When `experiments/` exists it runs
`exp validate` and `exp regen --check`; a stale registry fails the commit with an
instruction to run `bin/exp regen` and stage the output. Install the hooks once
with `git config core.hooksPath .githooks`, or run a single commit through them
with `git -c core.hooksPath=.githooks commit`.

## Promotion rule for shared inputs

An experiment's own artifacts stay inside its directory. The first time a SECOND
experiment needs to consume an artifact produced by another, promote that
artifact to `experiments/common/` and point both consumers at the promoted copy
via their `inputs:` list. The promoted copy keeps provenance: record where it came
from (the origin experiment slug and the path it was generated at) in a short note
beside it. This keeps cross-experiment dependencies explicit and prevents an
experiment from reaching into a sibling's private directory.

## Command reference

All commands run through the `bin/exp` wrapper (Windows: `bin\exp.cmd`), which
executes the mirror under `.agents/skills/experiments/scripts/exp.py`.

| Command | Effect |
|---------|--------|
| `bin/exp new <slug> --type <t>` | scaffold `experiments/<slug>/` (manifest, AMENDMENT.md, NOTEBOOK.md, .gitignore); refuses an existing slug |
| `bin/exp sign <slug>` | pin instrument configs/modules, flip draft->signed; refuses if prediction/falsifier empty |
| `bin/exp list [--status S] [--type T]` | table of slug/type/status/question |
| `bin/exp show <slug>` | pretty-print the manifest and resolved instrument paths |
| `bin/exp resolve <slug> --verdict "..." [--status null-result\|falsified]` | stamp verdict, flip to a terminal status, print the kg-ingest checklist |
| `bin/exp validate` | validate every manifest (schema, status, pins, inputs, kg ids, slug match); passes on an empty experiments/ |
| `bin/exp regen [--check]` | regenerate REGISTRY.md + registry.json; `--check` fails if the committed registry is stale |

`type` is one of `steer-cell`, `training-run`, `eval`, `probe-fit`,
`lab-diagnostic`. `bin/exp sign` reminds you, when a pinned config carries a
tuner `surface:` block, to set `surface.expected_config_sha` to that config's pin
so the tuner aborts on drift.

## Skill Maintenance

Edit the canonical tree under `.skills/experiments/` only. `.agents/` and
`.claude/` are generated mirrors. After canonical edits, run:

```bash
python3 bin/sync_skills.py --write --skill experiments
python3 bin/sync_skills.py --check --skill experiments
```

Tests live under `.skills/experiments/tests/` and run with
`python3 -m pytest .skills/experiments/tests`.
