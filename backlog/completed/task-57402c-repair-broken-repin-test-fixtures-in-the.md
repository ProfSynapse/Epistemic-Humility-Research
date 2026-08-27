---
id: task-57402c
title: Repair broken repin test fixtures in the exp test suite
status: done
assignee:
- '@claude'
tier: P
priority: low
experiment: ''
component: ''
depends_on: []
files:
- .skills/experiments/tests/test_exp.py
- .agents/skills/experiments/tests/test_exp.py
- .claude/skills/experiments/tests/test_exp.py
- .codex/skills/experiments/tests/test_exp.py
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
- 2026-08-27 @claude: root-caused all 13 failures to a single cause: the shared `_sign_ready` test fixture never declared `instrument.engine`, so every steer-cell it builds now hits the generation-engine gate (PI ruling 2026-08-13) added to `cmd_sign` since these fixtures were written. Added `instrument.engine: {name: vllm, version: 0.27.1}` to `_sign_ready` in `.skills/experiments/tests/test_exp.py` (matching the real declaration pattern used in `experiments/dial-logprob-baseline-v3/experiment.yaml`), then synced the fix to the `.agents/`, `.claude/`, `.codex/` mirrors via `bin/sync_skills.py --write --skill experiments`. Full suite now green: 64 passed (was 51 passed / 13 failed). No production bug found; the gate is working as intended and the fixtures were simply stale.
