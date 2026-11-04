---
title: 'Astra fixed hs20 weight edit: primary prediction falsified'
aliases:
- Qwen3.5 permanent edit abstention result
- Astra sparse weight edit no complete pass
tags:
- kg/experiment
kg:
  id: experiment:qwen35-4b-hs20-native-weight-edit
  type: experiment
  status: canonical
related:
- '[[weight-space-programming]]'
- '[[selfaware]]'
- '[[qwen35-4b-hs20-native-weight-edit-committed-evidence]]'
- '[[qwen35-4b-hs20-native-weight-edit-benefit-gates-failed]]'
relationships:
- type: uses
  target: '[[weight-space-programming]]'
  target_id: method:weight-space-programming
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
- type: produces
  target: '[[qwen35-4b-hs20-native-weight-edit-committed-evidence]]'
  target_id: artifact:qwen35-4b-hs20-native-weight-edit-committed-evidence
- type: supports
  target: '[[qwen35-4b-hs20-native-weight-edit-benefit-gates-failed]]'
  target_id: claim:qwen35-4b-hs20-native-weight-edit-benefit-gates-failed
---

Resolved 2026-11-04: terminal status `falsified`, verdict
`primary_prediction_falsified`, instrument valid, transfer false. The one fixed
Astra sparse edit failed the two primary SelfAware P-struct benefit gates;
all three preservation/quality cost gates passed. This exploratory result
applies to this frozen edit on the registered Qwen3.5-4B checkpoint and scaffold.
It is not evidence that permanent editing generally fails.

The PI predicted pass (LOSS; confidence not supplied). The lead predicted no
complete pass at 70% (WIN on outcome only); its hypothesized correctness-cost
mechanism was not observed. No new outcome adjudication is made here.

Source of truth: [AMENDMENT section 9](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/ef678d4f068b1cede54af4141de92f445f43e400/experiments/qwen35-4b-hs20-native-weight-edit/AMENDMENT.md#9-outcome) and the retained manifest at the
same commit. PR #604 merged on 2026-11-04. The commit-pinned citations remain
valid; the experiment is also available on main.

The broader-weight successor is a separately authorized draft with no results.
The cap-limited write reported in section 9 motivates it, without establishing
that more weight coverage or a larger edit will help. Benchmark reuse is
exploratory. The first study is not rescored.

SUPERSEDES: none. Searches for Qwen hs20 weight edits, native refusal/preservation
and permanent-edit abstention (including deprecated nodes; see handoff audit)
found no prior resolved node for this edit. The reused weight-space programming
method and prior runtime hs20 result address different interventions; neither
is overturned.
