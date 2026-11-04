---
id: task-6cae94
title: Migrate current research workflows to Tuner public API v1
status: in-review
assignee:
- '@codex'
tier: P
priority: high
experiment: ''
component: .
depends_on: []
files: []
new_files: []
blocker: ''
created_date: '2026-11-03'
updated_date: '2026-11-03'
---
## Description

Adopt the installed Tuner API v1 for new research while retaining signed historical instruments. Parent milestone: Nexus T-0513930e.


## Acceptance Criteria
- [x] Installed host identity and manifest validation work from a neutral directory.
- [x] Public training input planning and the isolated MechInterp/batch CLI boundary are tested.
- [x] Host-owned logs retain generation text and resume safely.
- [x] Prospective skills, atlas template, paths and artifact harvesting use the new boundary.
- [x] Historical signed scripts and submodule gitlink remain byte-identical.
- [x] CPU tests, portable experiment validation and skill synchronization pass.

## Work Log
- 2026-11-03: Installed consumer migration implemented and independently reviewed. Fixed wheel/source binding, abbreviation bypass, T7 cache/snapshot selection and atlas resume identity; documented advisory engine policies and explicit local artifact inputs. 24 installed-host CPU tests pass, real manifest validates, 134 experiments validate, skills sync and synthetic atlas smoke pass. Historical signed sources and gitlink unchanged. Desktop runtime qualification remains separate and pending.
