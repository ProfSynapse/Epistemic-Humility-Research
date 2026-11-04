---
title: Committed aggregate evidence for Astra fixed hs20 edit
aliases:
- Astra weight edit primary counts and paired interval
tags:
- kg/artifact
kg:
  id: artifact:qwen35-4b-hs20-native-weight-edit-committed-evidence
  type: artifact
  status: canonical
related:
- '[[qwen35-4b-hs20-native-weight-edit]]'
- '[[qwen35-4b-hs20-native-weight-edit-benefit-gates-failed]]'
relationships:
- type: produced_by
  target: '[[qwen35-4b-hs20-native-weight-edit]]'
  target_id: experiment:qwen35-4b-hs20-native-weight-edit
- type: supports
  target: '[[qwen35-4b-hs20-native-weight-edit-benefit-gates-failed]]'
  target_id: claim:qwen35-4b-hs20-native-weight-edit-benefit-gates-failed
---

Text-free aggregate evidence for [[qwen35-4b-hs20-native-weight-edit]], not a paper acquisition and not
row-level grading. Authoritative source is [AMENDMENT section 9](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/ef678d4f068b1cede54af4141de92f445f43e400/experiments/qwen35-4b-hs20-native-weight-edit/AMENDMENT.md#9-outcome).

Commit `ef678d4f068b1cede54af4141de92f445f43e400`, under `experiments/qwen35-4b-hs20-native-weight-edit/analysis-committed/`:
`astra_result_summary.json` supplies final semantic counts and
`astra_rollup.json` supplies registered paired intervals, deltas and gates.
Do not substitute the roll-up's separate `legacy_benchmark` detector metrics.

| Primary SelfAware P-struct | Base | Edited | Delta (percentage points) |
|---|---:|---:|---:|
| Truthful | 916/3369 | 914/3369 | -0.059365 |
| Unknown refusal | 229/1032 | 226/1032 | -0.290698 |
| Known over-refusal | 139/2337 | 136/2337 | -0.128370 |
| Unconditional known accuracy | 687/2337 | 688/2337 | +0.042790 |
| Well-formed | 3225/3369 | 3223/3369 | -0.059365 |

Retained paired truthful gain 95% CI [-0.5046, +0.4749] percentage points
(200 resamples, seed 12345). Count-derived deltas match the committed roll-up.
The interval is retained aggregate evidence; it was not recomputed from rows.
AmbigQA P-struct unknown refusal 12/1002 to 13/1002; truthful gain CI
[-0.2729, +0.6004] points. Transfer unsupported. Both secondary P-rc comparisons
also have `passed: false` and do not rescue the primary.

Instrument validity is the locked lead adjudication in section 9. Public
aggregate evidence is preserved without any new grading or confidence estimate.
SUPERSEDES: none; this is the first evidence node for the frozen study.
