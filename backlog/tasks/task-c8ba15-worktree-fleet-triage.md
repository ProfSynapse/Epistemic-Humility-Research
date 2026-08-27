---
id: task-c8ba15
title: Worktree fleet triage
status: in-progress
assignee:
- '@claude'
tier: P
priority: low
experiment: ''
component: ''
depends_on: []
files: []
new_files: []
blocker: ''
created_date: '2026-08-27'
updated_date: '2026-08-27'
---
## Description
23 worktrees on disk; several carry dirty never-pushed work (`ts-thinking`
~2,731 changes, `two-signal` ~4,743, `wicr-harness` ~139). Commit/push or
retire each. HARVEST BEFORE REMOVE: run `bin/harvest_worktree_data.py` and
confirm 0 conflicts before any `git worktree remove`. Migrated from the
TODO.md audited backlog table (row WT, audited 2026-08-27).

## Acceptance Criteria
- [ ] Every worktree with uncommitted or unpushed work is triaged (commit/push or explicitly abandoned)
- [ ] `bin/harvest_worktree_data.py` run with 0 conflicts before any removal
- [ ] Stale worktrees removed; `git worktree list` reflects only live work

## Work Log
- 2026-08-27 @claude: seeded from TODO.md row WT during the task-backlog harness build.
