---
id: task-d342cb
title: Paper 5 submission prep (MATS / fellowship)
status: in-progress
assignee:
- claude
tier: P
priority: high
experiment: ''
component: ''
depends_on: []
files:
- papers/paper-5-actuation/manuscript.md
new_files: []
blocker: PI review
created_date: '2026-08-27'
updated_date: '2026-08-30'
---
## Description
Manuscript is through the figure restructure, voice passes, and the
external-reviewer-lens pass (PRs #563-#567 merged; #568 open for the
figure-key CSV). Remaining work is whatever the submission itself requires:
final PI read, formatting, application forms. Migrated from the TODO.md
audited backlog table (row P5S, audited 2026-08-27).

## Acceptance Criteria
- [ ] Final PI read completed
- [ ] Manuscript formatting matches the target venue's submission requirements
- [ ] Application forms (MATS / fellowship) submitted

## Work Log
- 2026-08-27 @claude: seeded from TODO.md row P5S during the task-backlog harness build.
- 2026-08-30 @claude: added the paper-2 callback (prompt-vs-training panel, 90.89% vs 0% untrained-base actuation, Rosenbaum 2026b) to the 3.7 prompt frame and 6.4 bullet, PI-requested; numbers verified against the panel AMENDMENT Outcome.
- 2026-08-30 @claude: drafted the no-abstention-prompt disclosure edits on branch paper5-no-abstention-disclosure (methods prompt-frame paragraph in 3.7, scope note in Section 5, thermostat qualification in 6.1, exploratory-replication limits bullet in 6.4). Numbers pending final resolve of experiments/no-abstention-prompt-gated-replication; PR held for PI review, no merge before resolve.
