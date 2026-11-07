---
title: Fixed Astra R3 broad edit fails the primary truthful-gain gate
aliases:
- Did broader Astra weight editing establish stronger abstention
- Qwen broad permanent edit truthful benefit unestablished
- Astra column budget follow-up primary benefit failure
tags:
- kg/claim
kg:
  id: claim:qwen35-4b-astra-column-budget-followup-primary-truthful-gate-failed
  type: claim
  status: canonical
related:
- '[[qwen35-4b-astra-column-budget-followup]]'
- '[[qwen35-4b-astra-column-budget-followup-committed-evidence]]'
relationships:
- type: supported_by
  target: '[[qwen35-4b-astra-column-budget-followup]]'
  target_id: experiment:qwen35-4b-astra-column-budget-followup
- type: supported_by
  target: '[[qwen35-4b-astra-column-budget-followup-committed-evidence]]'
  target_id: artifact:qwen35-4b-astra-column-budget-followup-committed-evidence
---

The fixed R3 edit of Qwen3.5-4B fails the registered primary SelfAware P-struct
truthful-gain gate while passing the other four primary gates. Actual unknown
abstentions rise from 195/1032 to 201/1032 and known correct totals stay at 687/2337.
Truthful answers rise from 882/3369 to 888/3369: +0.17809439 percentage points,
with paired 95% CI [-0.3874,+0.7421] points. Its lower bound is not strictly above zero.
Of 687 baseline-correct answers, 672 are retained, 15 lost and 15 newly correct.

The registered primary prediction is falsified under the lead's terminal
adjudication. SelfAware P-rc passes its five secondary gates but cannot rescue
the primary. AmbigQA P-struct supplies no transfer support.

Scope is one frozen broad edit, checkpoint and registered evaluation. This
result does not exclude a small benefit, identify a mechanism, or establish
that permanent editing generally fails. R1/R3 baseline comparisons do not
estimate the causal effect of edit size or admission budget.

A PI-approved one-byte opaque-ID correction preceded grade acceptance and
unblinding, with zero judgment changes and preserved raw responses. Intended
row attribution remains a limitation. This is a disclosed grading deviation,
not unchanged preregistration compliance.

Source: [AMENDMENT sections 7 and 8](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/AMENDMENT.md#7-outcome)
and [[qwen35-4b-astra-column-budget-followup-committed-evidence]]. Governed records are pushed on PR #606, not merged at this ingest.

SUPERSEDES: none; R1 concerns a distinct fixed sparse edit and is not rescored.
