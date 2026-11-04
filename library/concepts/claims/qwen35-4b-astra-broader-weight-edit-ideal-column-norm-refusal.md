---
title: Astra R2 failed its frozen ideal column-norm guard
aliases:
- Why broader Astra editing stopped
- R2 45 percent column limit refusal
- No abstention evaluation for wider Qwen edit
tags:
- kg/claim
kg:
  id: claim:qwen35-4b-astra-broader-weight-edit-ideal-column-norm-refusal
  type: claim
  status: canonical
related:
- '[[qwen35-4b-astra-broader-weight-edit]]'
- '[[qwen35-4b-astra-broader-weight-edit-construction-evidence]]'
relationships:
- type: supported_by
  target: '[[qwen35-4b-astra-broader-weight-edit]]'
  target_id: experiment:qwen35-4b-astra-broader-weight-edit
- type: supported_by
  target: '[[qwen35-4b-astra-broader-weight-edit-construction-evidence]]'
  target_id: artifact:qwen35-4b-astra-broader-weight-edit-construction-evidence
---

The fixed `hs20-wide1024-fixed2sigma-r2` construction produced a maximum
ideal column delta/original-column norm ratio of 0.45768700324076517. Its
registered inclusive ideal limit was 0.45, so the instrument refused it before
bf16 serialization or checkpoint export. This was the sole failed ideal guard.

This establishes only that this proposal violated that numerical limit. It
provides no measured effect on actual abstention, answer correctness or capability.
The larger realized limit of 0.50 does not waive the distinct ideal headroom
check. No post-result threshold change, rescale or replacement was performed.

Authoritative [AMENDMENT section 8](../../../experiments/qwen35-4b-astra-broader-weight-edit/AMENDMENT.md#8-outcome),
with authenticated [construction evidence](../../../experiments/qwen35-4b-astra-broader-weight-edit/analysis-committed/astra_construction_outcome.json).
SUPERSEDES: none; neither the method nor earlier behavioral results are overturned.
