---
id: task-62d2d6
title: Build and run the bounded hs20 native weight-edit experiment
status: in-progress
assignee:
- '@claude'
tier: A
priority: high
experiment: ''
component: experiments
depends_on: []
files: []
new_files:
- experiments/qwen35-4b-hs20-native-weight-edit/
blocker: ''
created_date: '2026-11-03'
updated_date: '2026-11-03'
---
## Description

Implement and run the lead-owned bounded six-candidate Qwen3.5-4B hs20 native-weight-edit cell on the desktop RTX3090. New model/checkpoint artifacts must use T7 E:. Keep historical instruments unchanged. Parent Nexus task T-0513930e; generic engine PR281 and installed-host migration PR603 are dependencies.


## Acceptance Criteria
- [ ] Complete and independently review the protocol, instrument and provenance before signing.
- [ ] Build the installed-CLI harness with meaningful synthetic CPU checks and honest persistence declarations.
- [ ] Validate the pinned desktop image, model mapping, zero-patch/readback parity and real kill-resume behavior.
- [ ] Run the signed bounded FIT search and, only if eligible, the frozen held-out/control/diagnostic matrix.
- [ ] Apply the registered blinded grading and roll-up without changing thresholds after evidence.
- [ ] Preserve private artifacts on T7 and commit only code, hashes, IDs and aggregates through the experiment PR.
- [ ] Record the actual outcome and restoration state in Nexus, including any null or instrument failure.

## Work Log
