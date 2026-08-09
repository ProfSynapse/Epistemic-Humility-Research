# wrong-answer-cell-power-fix -- real-run gate table

extraction_dir: `experiments/wrong-answer-cell-power-fix/analysis/hidden_states/wrong-answer-cell-power-fix-arm-a/extraction/extraction__ab37a32e61a9`  
extraction_config_sha: `ab37a32e61a95268`  
primary layer: L35, band L30-L36, n_boot=2000, seed=20260808

## G0 gates

| Gate | Measured | Threshold | Pass |
|---|---|---|---|
| G0-1 render parity | 0/50 mismatches | 0 mismatches | True |
| G0-2 join integrity | 0+0 unmatched, 0+0 dup ids | 0/0/0/0 | True |
| G0-4 grader parity (grpov2) | 1.0000 | >= 0.995 | True |
| G0-4 grader parity (cleansft) | 1.0000 | >= 0.995 | True |
| G0-5 data adequacy (grpov2) | correct=420 wrong=360 | >=300/>=300 | True |
| G0-5 data adequacy (cleansft) | correct=469 wrong=524 | >=300/>=300 | True |

## grpov2 -- L35 primary (GATED per gates.yaml)

| Metric | Value |
|---|---|
| A1 internal refit AUROC | 0.5597 (CI 0.5185, 0.5993) |
| A2 frozen-axis raw projection AUROC (descriptive) | 0.5159 |
| A3 emitted AUROC | 0.5207 |
| A4 gap (A1-A3) | 0.0390 (CI -0.0163, 0.0942) |
| A5 internal ECE raw / reweighted | 0.0474 / 0.4166 |
| A6 emitted ECE raw / reweighted | 0.2847 / 0.1373 |
| A7 calibration gap raw (CI) | 0.2373 (0.1853, 0.2769) |
| A7 calibration gap reweighted (CI) | -0.2792 (-0.2850, -0.2736) |
| A8 emitted mean/std (n) | 0.8212 / 0.0175 (n=780) |

A9 emitted per-cell means:

| cell | n | emitted mean |
|---|---|---|
| known_correct_answered | 420 | 0.8222 |
| known_answered_wrong | 360 | 0.8200 |
| known_refused | 1557 | 0.8109 |
| unknown_refused | 964 | 0.8111 |
| unknown_answered | 68 | 0.8124 |

| E gate | Pass | Detail |
|---|---|---|
| E1 internal discrimination | False | AUROC=0.5597, ci_lower=0.5185 (need >=0.60 and ci_lower>0.55) |
| E2 primary gap | False | gap=0.0390 (need >=0.05, CI excludes 0) |
| E3 calibration contrast | False | raw+reweighted both >0 with CI excluding 0 |
| E4 ordering (frozen axis) | False | AMBIGUOUS axis choice, see E4_ambiguity_note |
| E4 ordering (fresh axis) | True | AMBIGUOUS axis choice, see E4_ambiguity_note |

## cleansft -- L35 primary (descriptive, not gated)

| Metric | Value |
|---|---|
| A1 internal refit AUROC | 0.5457 (CI 0.5103, 0.5812) |
| A2 frozen-axis raw projection AUROC (descriptive) | 0.5352 |
| A3 emitted AUROC | 0.4894 |
| A4 gap (A1-A3) | 0.0563 (CI 0.0071, 0.1067) |
| A5 internal ECE raw / reweighted | 0.0354 / 0.4842 |
| A6 emitted ECE raw / reweighted | 0.2451 / 0.2414 |
| A7 calibration gap raw (CI) | 0.2096 (0.1606, 0.2442) |
| A7 calibration gap reweighted (CI) | -0.2428 (-0.2470, -0.2388) |
| A8 emitted mean/std (n) | 0.7174 / 0.0171 (n=993) |

A9 emitted per-cell means:

| cell | n | emitted mean |
|---|---|---|
| known_correct_answered | 469 | 0.7176 |
| known_answered_wrong | 524 | 0.7172 |
| known_refused | 1344 | 0.7672 |
| unknown_refused | 898 | 0.7592 |
| unknown_answered | 134 | 0.7192 |

| E gate | Pass | Detail |
|---|---|---|
| E1 internal discrimination | False | AUROC=0.5457, ci_lower=0.5103 (need >=0.60 and ci_lower>0.55) |
| E2 primary gap | True | gap=0.0563 (need >=0.05, CI excludes 0) |
| E3 calibration contrast | False | raw+reweighted both >0 with CI excluding 0 |
| E4 ordering (frozen axis) | False | AMBIGUOUS axis choice, see E4_ambiguity_note |
| E4 ordering (fresh axis) | True | AMBIGUOUS axis choice, see E4_ambiguity_note |

## E5

status: not_computed -- Arm B not built

## Verdict (raw; lead adjudicates)

**FAILURE** -- primary falsifier fired (grpov2, L35)

## Ambiguity flagged

cell.yaml pins A1's estimator (fold-wise-refit axis + 1-D logistic) but that estimator is undefined for known_refused/unknown_refused rows (they are never part of the answered-known CV population). A9's per-cell means and E4's ordering check need a projection defined on all four behavior cells. This module reports E4 under TWO readings without picking one: (a) the FROZEN L35 axis (doubt_direction_L35.json, external, never trained on this cell's data), and (b) a FRESH full-population axis (unit(mean(known_correct_answered) - mean(unknown_refused)), no fold exclusion, this cell's own data, cell.yaml's literal `construction` formula). Neither is the pinned A1 estimator; the lead should adjudicate which (if either) satisfies gates.yaml E4's wording.
