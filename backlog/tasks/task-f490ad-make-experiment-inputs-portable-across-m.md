---
id: task-f490ad
title: Make experiment inputs portable across machines
status: in-review
assignee:
- '@codex'
tier: P
priority: high
experiment: ''
component: .skills/experiments
depends_on: []
files:
- .skills/pr-workflow/SKILL.md
new_files: []
blocker: ''
created_date: '2026-08-28'
updated_date: '2026-08-28'
---
## Description

Separate portable manifest validation from machine-local experiment readiness.
Typed local inputs must carry provenance, and a strict doctor command checks
their presence before use.

## Acceptance Criteria
- [x] Portable validation passes without local run artifacts.
- [x] Repository inputs remain strict.
- [x] `bin/exp doctor` fails on missing inputs and digest mismatches.
- [x] Existing failing manifests use explicit local input declarations.
- [x] Canonical skills and generated mirrors remain synchronized.

## Work Log

- Added typed `repository` and `local` input declarations.
- Added strict `bin/exp doctor [slug]` machine-readiness checks.
- Migrated 29 local artifacts across six resolved experiment manifests.
- Added unit coverage and regenerated skill mirrors and the experiment registry.
