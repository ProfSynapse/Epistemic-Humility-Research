---
title: 'Astra R3 broad weight edit: primary prediction falsified'
aliases:
- Does a broader permanent weight edit improve actual abstention
- Astra column budget follow-up behavioral result
- Qwen3.5 broad weight edit stronger abstention
tags:
- kg/experiment
kg:
  id: experiment:qwen35-4b-astra-column-budget-followup
  type: experiment
  status: canonical
related:
- '[[weight-space-programming]]'
- '[[selfaware]]'
- '[[qwen35-4b-hs20-native-weight-edit]]'
- '[[qwen35-4b-astra-column-budget-followup-committed-evidence]]'
- '[[qwen35-4b-astra-column-budget-followup-primary-truthful-gate-failed]]'
relationships:
- type: uses
  target: '[[weight-space-programming]]'
  target_id: method:weight-space-programming
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
- type: builds_on
  target: '[[qwen35-4b-hs20-native-weight-edit]]'
  target_id: experiment:qwen35-4b-hs20-native-weight-edit
  note: Separate frozen broader intervention; R1 keeps its own outcome and scores.
- type: produces
  target: '[[qwen35-4b-astra-column-budget-followup-committed-evidence]]'
  target_id: artifact:qwen35-4b-astra-column-budget-followup-committed-evidence
- type: supports
  target: '[[qwen35-4b-astra-column-budget-followup-primary-truthful-gate-failed]]'
  target_id: claim:qwen35-4b-astra-column-budget-followup-primary-truthful-gate-failed
---

Resolved `falsified` on 2026-11-07, with the approved grading deviation below.
The registered roll-up returns `primary_prediction_falsified` and transfer false.
The primary SelfAware P-struct truthful-gain gate fails; the other four gates pass.
This is a completed behavioral evaluation, not a numerical refusal.

The fixed two-sigma edit changed 2,489,947 BF16 entries in 1024 columns of one
layer19 down-projection tensor. All 737 other tensors remained byte-identical.
R3 followed R2 numerical feedback, raising the ideal column cap from 0.45 to
0.46 while retaining the treatment and behavioral gates. This is exploratory,
not an independent replication or a new editing method.

Actual unknown abstentions rose from 195/1032 to 201/1032; known correct totals
stayed 687/2337. Of the baseline correct set, 672 were retained: 15 lost and
15 newly correct. Truthful answers rose from 882/3369 to 888/3369, with gain
+0.17809439 percentage points and paired 95% CI [-0.3874, +0.7421] points.
Secondary SelfAware P-rc passes all five gates but cannot rescue the primary.
AmbigQA P-struct supplies no transfer support.

The PI approved a one-byte opaque-ID correction for shard_288 before grade
acceptance and unblinding. Zero judgment values changed; raw responses remain
preserved. This disclosed grading deviation is not unchanged preregistration
compliance. The byte evidence cannot establish intended grader row attribution.

Editor Astra's all-five-primary-gates prediction is a LOSS. No R3 PI or lead
prediction was recorded, so the two-sided prediction tally stays unchanged.
No general claim that permanent editing fails follows. Comparing R1 and R3
baselines does not identify a causal effect of edit size or admission budget.

Source: [AMENDMENT sections 7 and 8](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/AMENDMENT.md#7-outcome),
[manifest](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/experiment.yaml), and [[qwen35-4b-astra-column-budget-followup-committed-evidence]].
These sources are pushed on [PR #606](https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/606), not merged at this ingest.

SUPERSEDES: none. Searches for native weight edit benefit gates failed, fixed
broad weight edit abstention, and Astra column budget stronger abstention,
including deprecated nodes, found R1's distinct scoped result. R1 is not rescored.
