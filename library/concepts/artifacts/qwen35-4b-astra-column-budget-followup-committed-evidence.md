---
title: Committed aggregate evidence for Astra R3 broad weight edit
aliases:
- Astra R3 semantic abstention counts and paired interval
- Broad Qwen weight edit primary gates aggregate evidence
tags:
- kg/artifact
kg:
  id: artifact:qwen35-4b-astra-column-budget-followup-committed-evidence
  type: artifact
  status: canonical
related:
- '[[qwen35-4b-astra-column-budget-followup]]'
- '[[qwen35-4b-astra-column-budget-followup-primary-truthful-gate-failed]]'
relationships:
- type: produced_by
  target: '[[qwen35-4b-astra-column-budget-followup]]'
  target_id: experiment:qwen35-4b-astra-column-budget-followup
- type: supports
  target: '[[qwen35-4b-astra-column-budget-followup-primary-truthful-gate-failed]]'
  target_id: claim:qwen35-4b-astra-column-budget-followup-primary-truthful-gate-failed
---

Public aggregate evidence for [[qwen35-4b-astra-column-budget-followup]], without question or answer text,
row-level judgments, maps or tokens. Governed interpretation and deviation:
[AMENDMENT sections 7 and 8](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/AMENDMENT.md#7-outcome).
Sources are pushed on PR #606, not merged at this ingest.

The [semantic aggregates](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/analysis-committed/astra_semantic_aggregates_20261107.json)
contain final detector-plus-adjudicated counts; the [registered roll-up](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/analysis-committed/astra_rollup_20261107.json)
contains paired intervals and gates. Do not substitute its separate legacy
metrics. The [adjudication report](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/analysis-committed/astra_adjudication_report_20261107.json)
and [construction summary](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/analysis-committed/astra_construction_summary.json)
record calibration and numerical provenance.

| Primary SelfAware P-struct | Base | Edited |
|---|---:|---:|
| Unknown abstentions |195/1032|201/1032|
| Known abstentions |142/2337|131/2337|
| Known correct |687/2337|687/2337|
| Truthful |882/3369|888/3369|
| Well-formed |3225/3369|3226/3369|

Truthful gain is +0.17809439 percentage points, retained paired 95% CI
[-0.3874, +0.7421] points, 200 resamples, seed 12345. The truthful-gain gate
fails; recall-gain and all three cost gates pass. Retention is 672/687,
with 15 lost and 15 newly correct. These are retained aggregate intervals,
not a new bootstrap from private rows.

SelfAware P-rc abstentions rise from 379/1032 to 400/1032, known correct from 690/2337 to 687/2337,
and truthful answers from 1069/3369 to 1087/3369. These results pass all five secondary gates. Its truthful
95% CI is [+0.0289,+1.0099] points. It cannot rescue the primary.
AmbigQA P-struct abstentions stay at 10/1002; correct answers decline from 227/830 to 220/830;
truthful answers decline from 237/1832 to 230/1832. Both benefit gates fail; cost gates pass.
AmbigQA P-rc also fails truthful gain; transfer is unsupported.

All 20,804 initial answers completed in 22,470 attempts. All 357 accepted shards
passed CG1, with 8925/8925 positive agreement and blind lead agreement 30/30.
The edit changed 2,489,947 BF16 entries in 1024 columns of one tensor, with 737
other tensors unchanged. The PI-approved one-byte ID correction changed zero
judgments before grade acceptance and unblinding. Raw responses are retained;
intended row attribution remains a limitation. Disclose this grading deviation.

SUPERSEDES: none; this is aggregate evidence for a separate fixed R3 treatment.
