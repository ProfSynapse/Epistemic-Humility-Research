---
id: task-d037bb
title: 'flavor-atlas-gemma-pt-confirmatory: run or retire'
status: todo
assignee: []
tier: A
priority: medium
experiment: flavor-atlas-gemma-pt-confirmatory
component: ''
depends_on: []
files: []
new_files: []
blocker: PI go-ahead
created_date: '2026-08-27'
updated_date: '2026-08-27'
---
## Description
`flavor-atlas-gemma-pt-confirmatory` is signed and parked; the park was
upheld by the PI on 2026-08-18 (PR #509). Run it or retire it -- do not leave
it signed-and-idle indefinitely. Migrated from the TODO.md audited backlog
table (row FG, audited 2026-08-27). Bound to
`experiments/flavor-atlas-gemma-pt-confirmatory/` via `experiment:` --
validation will fail this task if that experiment reaches a terminal status
while this task stays open with no update.

## Acceptance Criteria
- [ ] PI go-ahead recorded: run the signed cell, or retire it
- [ ] If run: cell launched and result recorded in the experiment's NOTEBOOK.md
- [ ] `experiment.yaml` status flipped to a terminal state once resolved, and this task closed

## Work Log
- 2026-08-27 @claude: seeded from TODO.md row FG during the task-backlog harness build; bound to the flavor-atlas-gemma-pt-confirmatory experiment to dogfood the experiment: cross-check.
