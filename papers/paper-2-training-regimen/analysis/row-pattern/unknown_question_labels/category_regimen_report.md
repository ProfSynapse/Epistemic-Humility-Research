# Category x Regimen Exploratory Analysis

Exploratory join of semantic unknown-question labels to row-level behavior outputs.

## Inputs

- Semantic labels: `llm_labeled_unknown_answered_questions_v3.csv`
- Row masters: `row_master_amendment_a.csv`, `row_master_amendment_b.csv`
- Category axes: `primary_domain`, `epistemic_type`
- Regimen arms: `sft_merged`, `sft_dpo`, `sft_kto`

## Join Coverage

- source_unknown_rows: 12960
- joined_unknown_rows: 9090
- missing_unknown_rows: 3870
- label_questions: 1420
- matched_label_questions: 1420
- unmatched_label_questions: 0
- missing_question_keys: 836

## Top Exploratory Answer-Rate Effects

Ranked by absolute answer-rate delta with `min_cell_n >= 5`.

| family | axis | category | comparison | from_rate | to_rate | delta | min_n |
|---|---|---|---:|---:|---:|---:|---:|
| amendment_a | epistemic_type | math_word_problem_missing_info | dpo_minus_kto | 0.062500 | 1.000000 | 0.937500 | 48 |
| amendment_a | epistemic_type | math_word_problem_missing_info | dpo_minus_sft | 0.083333 | 1.000000 | 0.916667 | 48 |
| amendment_a | primary_domain | math_logic | dpo_minus_sft | 0.100000 | 1.000000 | 0.900000 | 60 |
| amendment_a | primary_domain | math_logic | dpo_minus_kto | 0.100000 | 1.000000 | 0.900000 | 60 |
| amendment_a | epistemic_type | underspecified | dpo_minus_sft | 0.111111 | 0.989899 | 0.878788 | 99 |
| amendment_a | epistemic_type | impossible_false_premise | dpo_minus_sft | 0.125000 | 1.000000 | 0.875000 | 8 |
| amendment_a | primary_domain | religion_philosophy_ethics | dpo_minus_sft | 0.122807 | 0.982456 | 0.859649 | 57 |
| amendment_a | epistemic_type | subjective_normative | dpo_minus_sft | 0.090909 | 0.939394 | 0.848485 | 33 |
| amendment_a | primary_domain | history_politics_law | dpo_minus_sft | 0.153846 | 1.000000 | 0.846154 | 13 |
| amendment_a | primary_domain | history_politics_law | dpo_minus_kto | 0.153846 | 1.000000 | 0.846154 | 13 |
| amendment_a | epistemic_type | future_or_unverifiable | dpo_minus_sft | 0.120000 | 0.960000 | 0.840000 | 25 |
| amendment_a | primary_domain | business_technology | dpo_minus_sft | 0.142857 | 0.952381 | 0.809524 | 21 |
| amendment_a | primary_domain | other_unclear | dpo_minus_sft | 0.196319 | 0.981595 | 0.785276 | 163 |
| amendment_a | epistemic_type | counterfactual_hypothetical | dpo_minus_sft | 0.195122 | 0.975610 | 0.780488 | 41 |
| amendment_a | primary_domain | science_health | dpo_minus_sft | 0.234694 | 0.989796 | 0.755102 | 98 |
| amendment_a | epistemic_type | impossible_false_premise | dpo_minus_kto | 0.250000 | 1.000000 | 0.750000 | 8 |
| amendment_a | epistemic_type | underspecified | dpo_minus_kto | 0.262626 | 0.989899 | 0.727273 | 99 |
| amendment_a | primary_domain | business_technology | dpo_minus_kto | 0.238095 | 0.952381 | 0.714286 | 21 |
| amendment_a | epistemic_type | counterfactual_hypothetical | dpo_minus_kto | 0.317073 | 0.975610 | 0.658537 | 41 |
| amendment_a | primary_domain | religion_philosophy_ethics | dpo_minus_kto | 0.350877 | 0.982456 | 0.631579 | 57 |

## Top Effects By Amendment

| family | axis | category | comparison | from_rate | to_rate | delta | min_n |
|---|---|---|---:|---:|---:|---:|---:|
| amendment_a | epistemic_type | math_word_problem_missing_info | dpo_minus_kto | 0.062500 | 1.000000 | 0.937500 | 48 |
| amendment_a | epistemic_type | math_word_problem_missing_info | dpo_minus_sft | 0.083333 | 1.000000 | 0.916667 | 48 |
| amendment_a | primary_domain | math_logic | dpo_minus_sft | 0.100000 | 1.000000 | 0.900000 | 60 |
| amendment_a | primary_domain | math_logic | dpo_minus_kto | 0.100000 | 1.000000 | 0.900000 | 60 |
| amendment_a | epistemic_type | underspecified | dpo_minus_sft | 0.111111 | 0.989899 | 0.878788 | 99 |
| amendment_b | epistemic_type | future_or_unverifiable | dpo_minus_sft | 0.269841 | 0.857143 | 0.587302 | 63 |
| amendment_b | primary_domain | math_logic | dpo_minus_sft | 0.336735 | 0.911565 | 0.574830 | 294 |
| amendment_b | primary_domain | math_logic | dpo_minus_kto | 0.357143 | 0.911565 | 0.554422 | 294 |
| amendment_b | epistemic_type | underspecified | dpo_minus_sft | 0.205729 | 0.752604 | 0.546875 | 384 |
| amendment_b | epistemic_type | math_word_problem_missing_info | dpo_minus_sft | 0.379167 | 0.916667 | 0.537500 | 240 |

## Caveats

- This is exploratory/vibes analysis, not a confirmatory statistical test.
- Semantic labels are broad analysis labels; they are not gold labels.
- The label artifact covers unknown questions that were answered by at least one arm, so always-unanswered unknown questions are outside the joined category analysis unless separately labeled.
- Small category cells can create large deltas; use `min_cell_n` and confidence intervals before interpreting a cluster.
- `answer_form` is intentionally excluded from the main analysis because it is less reliable than `primary_domain` and `epistemic_type`.
