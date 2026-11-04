---
title: Fixed Astra hs20 edit fails benefit without observed correctness cost
aliases:
- Does sparse permanent hs20 editing improve humility
- Qwen weight editing abstention benefit failed cost passed
tags:
- kg/claim
kg:
  id: claim:qwen35-4b-hs20-native-weight-edit-benefit-gates-failed
  type: claim
  status: canonical
related:
- '[[qwen35-4b-hs20-native-weight-edit]]'
- '[[qwen35-4b-hs20-native-weight-edit-committed-evidence]]'
relationships:
- type: supported_by
  target: '[[qwen35-4b-hs20-native-weight-edit]]'
  target_id: experiment:qwen35-4b-hs20-native-weight-edit
- type: supported_by
  target: '[[qwen35-4b-hs20-native-weight-edit-committed-evidence]]'
  target_id: artifact:qwen35-4b-hs20-native-weight-edit-committed-evidence
---

The registered one-edit prediction was falsified on behavioral benefit,
while all preservation/quality cost gates passed. Unknown refusal decreased
from 229/1032 to 226/1032 and the paired truthful gain 95% CI crossed zero.
Transfer was unsupported. This claim is scoped to the frozen sparse edit,
registered checkpoint, prompts, scoring and existing exploratory benchmarks.

Evidence: [[qwen35-4b-hs20-native-weight-edit-committed-evidence]]; source of truth:
[AMENDMENT section 9](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/ef678d4f068b1cede54af4141de92f445f43e400/experiments/qwen35-4b-hs20-native-weight-edit/AMENDMENT.md#9-outcome). This is a measured outcome claim, not an inferred
causal mechanism. It neither overturns earlier runtime hs20 steering findings
nor demonstrates that a broader or larger edit works.

The lead's 70% no-complete-pass prediction won on outcome only. The predicted
correctness-cost mechanism was not observed. The PI's pass prediction lost;
no PI confidence is supplied or inferred.

SUPERSEDES: none; search audit found no earlier resolved claim for this frozen
edit. Existing runtime steering and source-paper claims have different scope.
