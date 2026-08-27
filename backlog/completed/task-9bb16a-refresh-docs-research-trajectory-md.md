---
id: task-9bb16a
title: Refresh docs/research-trajectory.md
status: done
assignee:
- '@claude'
tier: P
priority: low
experiment: ''
component: ''
depends_on: []
files:
- docs/research-trajectory.md
new_files: []
blocker: ''
created_date: '2026-08-27'
updated_date: '2026-08-27'
---
## Description
The paper status headers and the paper 5 section in
`docs/research-trajectory.md` predate the late-August arcs (llama
wide-instrument rescore, editorial passes); last substantive update
2026-08-17. Migrated from the TODO.md audited backlog table (row TRAJ,
audited 2026-08-27).

## Acceptance Criteria
- [x] Paper status headers reflect the August editorial arcs
- [x] Paper 5 section reflects the llama wide-instrument rescore and current state
- [x] Doc's own last-updated marker bumped

## Work Log
- 2026-08-27 @claude: seeded from TODO.md row TRAJ during the task-backlog harness build.
- 2026-08-27 @claude: refreshed the doc on branch docs/trajectory-refresh. Paper
  3/4/5 status headers restated against manuscript front matter and figure dirs;
  Paper 5 section extended with the cross-family layer-contrast close-out, both
  gemma cells, the qwen wide-instrument control re-score and L34 placebo census,
  the two llama hs17 cells plus the data-loss incident and recovery re-run, and
  the dial-vs-logprob v3/LT successors; gemma family atlas entry moved from
  "outcome pending" to its resolved verdict; the prompt-scaffolded-confidence
  parked thread updated to its resolved state; process infrastructure extended
  with PRs #561/#564/#569/#570. Awaiting PR review.
