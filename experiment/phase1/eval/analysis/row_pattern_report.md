# SFT/DPO/KTO Row-Pattern Exploratory Analysis

Evidence tier: local bounded exploratory/non-headline. This is a deterministic first-pass clustering/tagging pass using mechanical descriptors only; it does not assign final causal or semantic labels.

Validation status: pass
Included inputs: 24; excluded inventory-only inputs: 3
Bad-merge seed2 DPO exclusion present: True

## Amendment A: plain-answer contract

- Rows: 13932
- Paired SFT-to-DPO/KTO transitions: 9288
- Arm rows: sft_dpo=4644, sft_kto=4644, sft_merged=4644
- Top behavior states: known_refused_overrefusal=4810, known_answered_incorrect_failure=3932, unknown_refused_accurate_idk=2639, known_answered_correct_useful=1518, unknown_answered_hallucination_exposure=1033
- Top transitions: unchanged=6433, known_refused_to_incorrect_answer=1963, unknown_refused_to_answered=536, known_refused_to_correct_answer=161, known_correct_to_failure=97, unknown_answered_to_refused=43, known_answered_incorrect_failure__to__known_answered_correct_useful=41, known_answered_incorrect_failure__to__known_refused_overrefusal=14

## Amendment B: stated-confidence contract

- Rows: 30321
- Paired SFT-to-DPO/KTO transitions: 20214
- Arm rows: sft_dpo=10107, sft_kto=10107, sft_merged=10107
- Top behavior states: known_answered_incorrect_failure=9824, known_refused_overrefusal=6607, unknown_refused_accurate_idk=5478, known_answered_correct_useful=4602, unknown_answered_hallucination_exposure=3810
- Top transitions: unchanged=14400, known_refused_to_incorrect_answer=3332, unknown_refused_to_answered=1538, known_correct_to_failure=263, known_refused_to_correct_answer=256, unknown_answered_to_refused=206, known_answered_incorrect_failure__to__known_answered_correct_useful=157, known_answered_incorrect_failure__to__known_refused_overrefusal=62

## Amendment B Confidence Validation

- `answer_text` column present in included B schemas: True
- `stated_confidence` column present in included B schemas: True
- Non-empty `answer_text`: 30321 / 30321
- Non-empty `stated_confidence`: 30291 / 30321
- Blank `stated_confidence` with retry exhaustion: 30
- Blank `stated_confidence` without retry exhaustion: 0

## Generated Tables

- `row_pattern_outputs/input_inventory.csv`
- `row_pattern_outputs/schema_audit.csv`
- `row_pattern_outputs/row_master_amendment_a.csv`
- `row_pattern_outputs/row_master_amendment_b.csv`
- `row_pattern_outputs/paired_transitions_amendment_a.csv`
- `row_pattern_outputs/paired_transitions_amendment_b.csv`
- `row_pattern_outputs/cluster_tag_summary_amendment_a.csv`
- `row_pattern_outputs/cluster_tag_summary_amendment_b.csv`
- `row_pattern_outputs/representative_examples_amendment_a.csv`
- `row_pattern_outputs/representative_examples_amendment_b.csv`
- `row_pattern_outputs/validation_summary.json`
