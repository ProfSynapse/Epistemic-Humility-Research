# LLM-Labeled Unknown Answered Questions

Semantic labeling artifact for the unknown-question exposure analysis. This file labels all rows from `unknown_question_label_manifest.csv` where `answered_by_any_arm=true`.

## Selection

- Source: `unknown_question_label_manifest.csv`
- Included rows: 1420
- Sampling: none; all eligible answered unknown rows were labeled.
- Eligibility inherited from manifest selection: `include_status=include` and `label=unknown` upstream, aggregated by `question_key`.
- Provisional scripted labels were not copied into this artifact. They were treated only as non-authoritative triage context; the assigned fields use the question text and example-answer context.

## Schema

- `question_key`, `question_hash`, `question`, `eval_sets`, `analysis_family_coverage`: original manifest identifiers and source grouping.
- Answered/refusal columns: original arm-level behavior flags and `example_answers_by_arm` copied from the manifest.
- `primary_domain`: one taxonomy domain judged to best describe the question's semantic topic.
- `secondary_domain`: optional second domain for genuinely mixed-domain questions.
- `epistemic_type`: taxonomy class for why the item is unknown/IDK-relevant.
- `answer_form`: expected answer shape implied by the question.
- `label_confidence`: high/medium/low confidence in the semantic label.
- `needs_human_review`: true for low-confidence, ambiguous, or otherwise mixed cases.
- `label_notes`: concise rationale for the assigned labels.

## Counts By Family

- amendment_b: 805
- amendment_a: 615

## Counts By Eval Set

- selfaware: 1361
- kuq: 59

## Counts By Domain

- other_unclear: 577
- everyday_practical_subjective: 248
- religion_philosophy_ethics: 152
- math_logic: 129
- science_health: 114
- people_biography: 70
- geography_places: 36
- history_politics_law: 36
- arts_entertainment_literature: 28
- business_technology: 26
- sports_games: 4

## Counts By Epistemic Type

- subjective_normative: 327
- other_unclear: 313
- obscure_long_tail_fact: 304
- counterfactual_hypothetical: 153
- future_or_unverifiable: 110
- underspecified: 75
- math_word_problem_missing_info: 74
- ambiguous: 42
- impossible_false_premise: 22

## Counts By Answer Form

- yes_no: 619
- other_unclear: 445
- explanation: 187
- entity: 88
- short_phrase: 38
- definition: 24
- number: 16
- list: 3

## Counts By Label Confidence

- low: 703
- high: 401
- medium: 316

## Human Review Flag

- true: 728
- false: 692

## Counts By Arm Behavior

- dpo=true;kto=false;sft_refused=true: 674
- dpo=true;kto=true;sft_refused=true: 348
- dpo=true;kto=true;sft_refused=false: 337
- dpo=false;kto=true;sft_refused=false: 21
- dpo=true;kto=false;sft_refused=false: 19
- dpo=false;kto=false;sft_refused=false: 10
- dpo=false;kto=true;sft_refused=true: 8
- dpo=false;kto=false;sft_refused=true: 3

## Caveats

- These are semantic labels produced for analysis triage, not final scientific claims.
- The pass is conservative: broad metaphysical, wordplay, and mixed-domain questions are usually marked medium/low confidence and/or `needs_human_review=true`.
- The artifact does not run model inference, retrain models, or alter the upstream scripted manifest.
