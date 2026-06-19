# Unknown Question Label Manifest Summary

Evidence tier: exploratory. Labels are provisional deterministic heuristics for human labeling triage, not scientific taxonomy claims.

- Unique unknown question rows in manifest: 2256
- Unique unknown questions answered by any arm: 1420
- Unique unknown questions answered by DPO: 1378
- Unique unknown questions answered by KTO: 714

## Counts By Family

- amendment_a: 1224
- amendment_b: 1032

## Counts By Provisional Primary Domain

- other_unclear: 1061
- everyday_practical_subjective: 301
- business_technology: 206
- science_health: 157
- math_logic: 143
- people_biography: 135
- geography_places: 90
- history_politics_law: 64
- religion_philosophy_ethics: 47
- arts_entertainment_literature: 32
- sports_games: 20

## Counts By Provisional Epistemic Type

- other_unclear: 708
- subjective_normative: 529
- future_or_unverifiable: 328
- counterfactual_hypothetical: 268
- obscure_long_tail_fact: 226
- ambiguous: 112
- underspecified: 51
- math_word_problem_missing_info: 30
- impossible_false_premise: 4

## Counts By Arm Behavior

- any_answered=false;dpo_answered=false;kto_answered=false;sft_merged_refused=true: 836
- any_answered=true;dpo_answered=true;kto_answered=false;sft_merged_refused=true: 674
- any_answered=true;dpo_answered=true;kto_answered=true;sft_merged_refused=true: 348
- any_answered=true;dpo_answered=true;kto_answered=true;sft_merged_refused=false: 337
- any_answered=true;dpo_answered=false;kto_answered=true;sft_merged_refused=false: 21
- any_answered=true;dpo_answered=true;kto_answered=false;sft_merged_refused=false: 19
- any_answered=true;dpo_answered=false;kto_answered=false;sft_merged_refused=false: 10
- any_answered=true;dpo_answered=false;kto_answered=true;sft_merged_refused=true: 8
- any_answered=true;dpo_answered=false;kto_answered=false;sft_merged_refused=true: 3

## Top Family/Domain Clusters

- amendment_a / other_unclear: 573
- amendment_b / other_unclear: 488
- amendment_a / everyday_practical_subjective: 158
- amendment_b / everyday_practical_subjective: 143
- amendment_a / business_technology: 117
- amendment_b / business_technology: 89
- amendment_a / science_health: 87
- amendment_a / math_logic: 76
- amendment_a / people_biography: 74
- amendment_b / science_health: 70
- amendment_b / math_logic: 67
- amendment_b / people_biography: 61

## Top Family/Epistemic-Type Clusters

- amendment_a / other_unclear: 386
- amendment_b / other_unclear: 322
- amendment_a / subjective_normative: 283
- amendment_b / subjective_normative: 246
- amendment_a / future_or_unverifiable: 193
- amendment_a / counterfactual_hypothetical: 140
- amendment_b / future_or_unverifiable: 135
- amendment_b / counterfactual_hypothetical: 128
- amendment_a / obscure_long_tail_fact: 118
- amendment_b / obscure_long_tail_fact: 108
- amendment_a / ambiguous: 58
- amendment_b / ambiguous: 54

## Top Answered-By-Any-Arm Domains

- other_unclear: 623
- everyday_practical_subjective: 260
- business_technology: 107
- math_logic: 94
- science_health: 93
- people_biography: 91
- geography_places: 63
- history_politics_law: 35
- religion_philosophy_ethics: 26
- arts_entertainment_literature: 16
- sports_games: 12

## Top Answered-By-Any-Arm Epistemic Types

- other_unclear: 441
- subjective_normative: 397
- counterfactual_hypothetical: 174
- obscure_long_tail_fact: 158
- future_or_unverifiable: 124
- ambiguous: 65
- underspecified: 38
- math_word_problem_missing_info: 20
- impossible_false_premise: 3

## Selection Rules

- Source files: row_master_amendment_a.csv and row_master_amendment_b.csv.
- Include only rows with include_status=include and label=unknown.
- Aggregate at question_key = analysis_family + normalized-question SHA-256 prefix, keeping Amendment A and Amendment B separate.
- Treat behavior_state=unknown_answered_hallucination_exposure as answered; otherwise use refused to distinguish answered/refused.
- Preserve Amendment B stated confidence only as max_confidence_if_b.
