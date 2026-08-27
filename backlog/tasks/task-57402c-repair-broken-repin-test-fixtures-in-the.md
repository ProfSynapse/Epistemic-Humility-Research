---
id: task-57402c
title: Repair broken repin test fixtures in the exp test suite
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
13 repin test fixtures were flagged as broken during the August wide-rescore
arc in `.skills/experiments/tests/test_exp.py`. Repair or regenerate the
fixtures. Migrated from the TODO.md audited backlog table (row RT, audited
2026-08-27). Note (2026-08-27, task-backlog harness build): re-confirmed at
13 failed / 51 passed via `python3 -m pytest .skills/experiments/tests/test_exp.py -q`.

## Acceptance Criteria
- [ ] All 13 flagged repin fixtures identified and root-caused
- [ ] Fixtures repaired or regenerated
- [ ] `python3 -m pytest .skills/experiments/tests/test_exp.py -q` fully green

## Work Log
- 2026-08-27 @claude: seeded from TODO.md row RT during the task-backlog harness build; re-confirmed baseline at 13 failed / 51 passed (unrelated to this build's changes).
