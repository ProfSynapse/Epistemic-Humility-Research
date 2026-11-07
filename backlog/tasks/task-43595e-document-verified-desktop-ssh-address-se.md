---
id: task-43595e
title: Document verified desktop SSH address selection
status: in-review
assignee:
- '@codex'
tier: P
priority: medium
experiment: ''
component: ''
depends_on: []
files:
- .skills/experiment-runner/reference/local-windows-gotchas.md
new_files:
- .skills/experiment-runner/reference/desktop-ssh.md
blocker: ''
created_date: '2026-11-04'
updated_date: '2026-11-04'
---

## Description

Record the verified desktop SSH route-selection diagnostic so a LAN hostname
timeout is not mistaken for an offline Tailscale peer or a Docker failure.

## Acceptance Criteria
- [x] Document independent peer/address verification and existing host-key checks.
- [x] Route from the Windows operator reference and sync canonical skill mirrors.
- [x] Keep private IPs, current run state and credentials out of the guide.

## Work Log

2026-11-04: observed short hostname resolving to a LAN address while the same
verified Tailscale peer accepted SSH at its tailnet address. No host-key check
was disabled and no global SSH, Windows or Docker setting was changed.

2026-11-04: added the narrow SSH reference/router and verified all canonical mirrors with sync_skills --check. Ready for PR review.
