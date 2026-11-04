---
title: 'Astra R2 broader edit: terminal construction refusal'
aliases:
- Did the wider Qwen weight edit run
- Astra 1024 column two sigma proposal stopped before evaluation
tags:
- kg/experiment
kg:
  id: experiment:qwen35-4b-astra-broader-weight-edit
  type: experiment
  status: canonical
related:
- '[[weight-space-programming]]'
- '[[qwen35-4b-hs20-native-weight-edit]]'
- '[[qwen35-4b-astra-broader-weight-edit-construction-evidence]]'
- '[[qwen35-4b-astra-broader-weight-edit-ideal-column-norm-refusal]]'
relationships:
- type: uses
  target: '[[weight-space-programming]]'
  target_id: method:weight-space-programming
- type: builds_on
  target: '[[qwen35-4b-hs20-native-weight-edit]]'
  target_id: experiment:qwen35-4b-hs20-native-weight-edit
- type: produces
  target: '[[qwen35-4b-astra-broader-weight-edit-construction-evidence]]'
  target_id: artifact:qwen35-4b-astra-broader-weight-edit-construction-evidence
- type: supports
  target: '[[qwen35-4b-astra-broader-weight-edit-ideal-column-norm-refusal]]'
  target_id: claim:qwen35-4b-astra-broader-weight-edit-ideal-column-norm-refusal
---

Resolved 2026-11-04 as `construction_refused`. The one fixed 1,024-column,
two-sigma mathematical proposal exceeded its ideal per-column norm limit:
0.45768700324076517 against 0.45. The other ideal guards passed. No bf16 patch
was serialized or applied, no checkpoint was exported, and no inference ran.

The abstention/correctness prediction remains untested. This is not a behavioral
null, an observed correctness tradeoff, or evidence that broad editing generally
fails. No WIN/LOSS is assigned. No rescaling or replacement occurred.

Source of truth: [AMENDMENT section 8](../../../experiments/qwen35-4b-astra-broader-weight-edit/AMENDMENT.md#8-outcome)
and the hash-only [construction outcome](../../../experiments/qwen35-4b-astra-broader-weight-edit/analysis-committed/astra_construction_outcome.json).
The signed source was commit 620942f5c2ef1256fed51c784e254985a8070ca7.

SUPERSEDES: none. This is a distinct fixed proposal; the earlier experiment's
behavioral result remains separate and is not rescored.
