---
id: task-9221b1
title: Task-backlog harness (bin/task, generated TODO block, commit gate)
status: done
assignee:
- '@claude'
tier: P
priority: high
experiment: ''
component: ''
depends_on: []
files:
- .githooks/pre-commit
new_files:
- .skills/task-backlog/
- bin/task
- bin/task.py
blocker: ''
created_date: '2026-08-27'
updated_date: '2026-08-27'
---
## Description
Borrow the syntunia `backlog/` pattern (one task file per item, `bin/task`
CLI, generated TODO block, pre-commit validation) and bind tasks to
experiment slugs so a terminal `experiment.yaml` status forces its task
closed at commit time. Migrated from the TODO.md audited backlog table (row
TASK, audited 2026-08-27); PI approved the locked design before this build
started. This task's own `files:`/`new_files:` cover this build's gated
output, dogfooding the commit gate this task itself introduces.

## Acceptance Criteria
- [ ] `bin/task` CLI (new/list/show/claim/release/review/done/validate) implemented and tested
- [ ] `backlog/` seeded with the 9 rows from TODO.md's audited table
- [ ] Generated TODO.md task-backlog block renders and is wired into `.githooks/pre-commit`
- [ ] Commit gate (`check_task_gate.py`) wired into `.githooks/pre-commit`, gating this build's own commits
- [ ] `.skills/task-backlog/` synced to both generated mirrors
- [ ] PR opened

## Work Log
- 2026-08-27 @claude: claimed; building the task-backlog harness (CLI, generator, commit gate, skill, tests, seed tasks) in worktree /home/profsynapse/code/ehr-worktrees/task-backlog on branch infra/task-backlog.
