---
name: task-backlog
description: Task-backlog lifecycle tooling for the Epistemic-Humility-Research repo - one markdown file per task under backlog/{tasks,drafts,completed}, a bin/task CLI (new/list/show/claim/release/review/done/validate), a generated TODO.md table, and a pre-commit commit gate that requires gated work files to be covered by an active task. Use to mint, claim, and close backlog tasks, to bind a task to an experiments/<slug>/ record, and to understand the commit-gate scope and escape hatch. Tasks point at experiments; experiments keep their own lifecycle under bin/exp and AMENDMENT.md.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Task Backlog

Tasks live in `backlog/` -- one markdown file per task. **All task operations
go through `bin/task`** -- it mints merge-safe random hex ids (never
sequential; those collide when parallel worktrees merge), enforces the schema,
and re-validates after every mutating command. This ports the syntunia
`backlog/` task-lifecycle pattern into this repo, adapted to bind tasks against
this repo's `experiments/<slug>/` records instead of a generic `component:`
path.

Experiments themselves stay governed by `bin/exp` and
`experiments/<slug>/AMENDMENT.md` (see the `experiments` skill). Tasks never
duplicate an experiment's lifecycle -- they only point at one via the optional
`experiment:` field, and validation fails a task that stays open against an
experiment that has already reached a terminal status (the "rot-killer").

## States (enumerated -- the validator rejects anything else)

`draft` (in `backlog/drafts/`) -> `todo` -> `in-progress` -> `in-review` -> `done` (archived to `backlog/completed/`)

## The CLI

```bash
python3 bin/task.py new "Title" --tier P --priority high \
    [--experiment <slug>] [--component path] \
    [--depends-on task-xxxxxx]... [--file existing/path]... \
    [--new-file planned/path]... [--blocker "text"] [--draft]
python3 bin/task.py list                          # blocked tasks are flagged
python3 bin/task.py show task-xxxxxx               # full working context
python3 bin/task.py claim task-xxxxxx --as @you    # -> in-progress
python3 bin/task.py release task-xxxxxx            # -> todo, unassigned
python3 bin/task.py review task-xxxxxx             # -> in-review (PR open)
python3 bin/task.py done task-xxxxxx               # -> done, archived
python3 bin/task.py validate                       # full validation pass
```

(`bin/task` -- no extension -- is the same wrapper shape as `bin/exp`; either
invocation works. `bin/task` runs the generated `.agents/skills/task-backlog/`
mirror, so re-sync after editing canonical scripts -- see Maintenance below.)

## Rules

1. **All work starts from a task.** No task covering your change? `bin/task
   new` first (or claim an existing one).
2. **Claim before you touch a gated file** (`claim --as @you`; default handle
   is `@agent` if omitted). Claim refuses a task another assignee holds.
3. **Dependencies are a DAG.** `--depends-on` (or a hand-edited `depends_on:`
   list) is validated for cycles and unknown ids.
4. **`files:` / `new_files:` give the change's scope.** `files:` = existing
   files in scope (validated to exist); `new_files:` = files the task expects
   to create (no existence check -- a trailing `/` marks a whole subtree
   prefix, honored by the commit gate). Move an entry from `new_files:` to
   `files:` once it exists.
5. **`experiment:` binds a task to `experiments/<slug>/`** (must exist).
   `validate` fails any open task (`draft`/`todo`/`in-progress`/`in-review`)
   whose bound experiment's `experiment.yaml` `status:` is terminal
   (`resolved`, `null-result`, `falsified`, `historical`, `shelved`) --
   close the task (`done` or `release`) instead of leaving it to rot.
   Non-terminal statuses (`draft`, `signed`, `running`) pass.
6. **`component:`** is an optional path-prefix binding (`.` = repo-wide); must
   resolve to a real path if set.
7. **Never hand-edit `TODO.md`'s generated task-backlog block** -- see
   Generated TODO.md block below.

## Task file schema

```yaml
id: task-a1b2c3          # random 6-hex, minted ONLY by the CLI
title: ...
status: todo             # draft | todo | in-progress | in-review | done
assignee: []             # ['@handle']
tier: P                  # A | L | P  (A=amendment-linked, L=lab-notebook, P=paper/infra)
priority: medium         # high | medium | low
experiment: <slug>       # optional; must exist under experiments/
component: papers/paper-5-actuation   # optional path prefix; must exist ('.' = repo-wide)
depends_on: []           # task ids, DAG-validated
files: []                # existing files in scope (existence validated)
new_files: []            # planned files; trailing "/" = subtree prefix
blocker: ""              # optional free text
created_date: YYYY-MM-DD
updated_date: YYYY-MM-DD
```

Body: `## Description` (the why) -- `## Acceptance Criteria` (checkboxes) --
`## Work Log` (append-only; edit this section by hand as you go).

## Generated TODO.md block

`build_todo_index.py` renders every non-done task into the fenced
`<!-- BEGIN GENERATED: task-backlog -->` / `<!-- END GENERATED: task-backlog -->`
block in `TODO.md` -- a table (id, title, tier, status, priority,
blocker/deps, experiment) sorted by priority then `created_date`, plus a
one-line count of tasks archived in `backlog/completed/`. Everything outside
the fence (the "Prioritized backlog" preamble, dated gotcha paragraphs, the
standing-posture note, the "Parked" section, the archive note) is
hand-written prose and is preserved verbatim on regen -- **never hand-edit
inside the fence**; run:

```bash
python3 .agents/skills/task-backlog/scripts/build_todo_index.py --write
python3 .agents/skills/task-backlog/scripts/build_todo_index.py --check   # CI/pre-commit gate
```

This is a second, independent generated block in `TODO.md` alongside the
pre-existing `<!-- BEGIN GENERATED: amendment-index -->` block (from
`bin/build_backlog_index.py`); the two never overlap.

## Commit gate (`check_task_gate.py`)

Wired into `.githooks/pre-commit`, this enforces change -> task traceability
for a fixed **gated scope**: `papers/`, `bin/`, `.skills/`, `.githooks/`,
`.claude/hooks/`, and `docs/` **excluding** `docs/sessions/`. Everything else
is exempt, including `experiments/`, `backlog/`, `TODO.md`, `docs/sessions/`,
the generated skill mirrors (`.agents/`, `.claude/skills/`), the
`synaptic-tuner` submodule pointer, `.claude/settings.json`, and `analysis/`.

A gated file may only be staged when an **active** task (`in-progress` or
`in-review`) covers it via `files:`, `new_files:` (trailing-slash prefix), or
`component:` prefix, AND that task's own file is also staged (or its
`updated_date` is today, in pre-commit mode). On failure the gate prints
exactly which files are uncovered and the one-line fix (`bin/task new` /
`bin/task claim`).

**Escape hatch:** `EHR_TASK_OK=1 git commit ...` skips the gate loudly (it
prints that it was skipped) -- use only for genuine emergencies.

## Validation

`bin/task validate` (also run at commit time via `.githooks/pre-commit`)
checks: schema/enum conformance, unique ids, `depends_on` DAG acyclicity,
`experiment:` slug existence, `files:` existence, `component:` existence, and
the terminal-experiment rot-killer cross-check above.

## Maintenance

Canonical source is `.skills/task-backlog/`; `.agents/skills/task-backlog/`
and `.claude/skills/task-backlog/` are GENERATED MIRRORS -- never hand-edit a
mirror. After editing the canonical scripts or this doc:

```bash
python3 bin/sync_skills.py --write --skill task-backlog
python3 bin/sync_skills.py --check --skill task-backlog
```

