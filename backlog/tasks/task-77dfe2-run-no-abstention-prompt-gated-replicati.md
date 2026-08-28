---
id: task-77dfe2
title: Run no-abstention-prompt gated replication across families
status: todo
assignee: []
tier: A
priority: high
experiment: no-abstention-prompt-gated-replication
component: ''
depends_on: []
files: []
new_files: []
blocker: ''
created_date: '2026-08-28'
updated_date: '2026-08-28'
---
## Description

Does the gated abstention write survive removing the abstention instruction
from the system prompt? Every behavioral cell to date ran under a prompt that
permits refusal and seeds the graded refusal string; prompt-independence is
untested (2026-08-28 finding, PI hand-audit session). Draft amendment lives at
`experiments/no-abstention-prompt-gated-replication/` on PR #583 (branch
`exp/no-abstention-prompt-gated-replication`); the `experiment:` frontmatter
field stays empty until that PR merges, then set it to the slug.

## Acceptance Criteria
- [x] PR #583 merged (2026-08-28, merge commit 1ea9e938); `experiment:` field set
- [x] Pre-sign feasibility probe done (2026-08-28): operating points sha-pinned in cell.yaml, recorded in NOTEBOOK.md
- [x] PI adjudicated prediction/falsifier/gates; signed 2026-08-28 via `bin/exp sign` (G1 0.4459, G1b 0.3595, G2 ceiling 0.0698 / floor N=52)
- [ ] GPU launch approved by PI and run on the canonical checkout; both prompt renders diffed in NOTEBOOK.md before launch
- [ ] Resolve with wide-instrument grading; report full-pool and KUQ-only strata

## Work Log
- 2026-08-28: task minted; draft amendment scaffolded and pushed (PR #583).
- 2026-08-28: pre-sign probe done; blockers closed (render pin, llama seed 910016, judge pins, frozen gates); signed; PR #583 merged. Next: PI launch approval on the canonical checkout.
