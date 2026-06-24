# LLM-Labeled Unknown Answered Questions v3

Generated from `llm_labeled_unknown_answered_questions.csv` as a semantic cleanup artifact for exploratory `primary_domain` and `epistemic_type` analysis.

## Scope

- Preserves the original row set, column order, and existing taxonomy values.
- Updates only semantic labeling fields: `primary_domain`, `secondary_domain`, `epistemic_type`, `answer_form`, `label_confidence`, `needs_human_review`, and `label_notes`.
- Enforces identical semantic labels across identical `question_hash` groups.
- Does not update category-regimen outputs or original label files.

## Cleanup Rules

- Reclassified arithmetic word problems with proper names from `people_biography` or `other_unclear` to `math_logic`.
- Routed cosmology, physics, biology, climate, animal, and space-science prompts to `science_health`.
- Routed God, religion, ethics, morality, metaphysics, and philosophy prompts to `religion_philosophy_ethics`.
- Reduced `other_unclear` where question wording provided clear topical or answer-form cues.
- Recomputed `answer_form` from interrogative form and math/quantity cues, especially `how many`, `how much`, `how long`, percentages, and word problems.
- Kept all values inside the taxonomy already present in the source CSV.

## Checks

- Source rows: 1420
- v3 rows: 1420
- Duplicate `question_hash` groups: 550
- Duplicate semantic conflicts before consistency pass: 0
- Duplicate rows overwritten by consistency pass: 0
- Duplicate semantic conflicts after consistency pass: 0
- Taxonomy preservation: passed; no new values introduced in semantic label columns.

## Changed Field Counts

- `epistemic_type`: 863
- `label_confidence`: 677
- `needs_human_review`: 316
- `secondary_domain`: 188
- `primary_domain`: 352
- `answer_form`: 476

## v3 Label Distributions

### primary_domain
- `other_unclear`: 399 (-178)
- `everyday_practical_subjective`: 379 (+131)
- `science_health`: 209 (+95)
- `math_logic`: 158 (+29)
- `religion_philosophy_ethics`: 144 (-8)
- `arts_entertainment_literature`: 38 (+10)
- `geography_places`: 34 (-2)
- `business_technology`: 30 (+4)
- `history_politics_law`: 25 (-11)
- `sports_games`: 2 (-2)
- `people_biography`: 2 (-68)

### epistemic_type
- `obscure_long_tail_fact`: 789 (+485)
- `underspecified`: 227 (+152)
- `math_word_problem_missing_info`: 128 (+54)
- `counterfactual_hypothetical`: 94 (-59)
- `subjective_normative`: 78 (-249)
- `future_or_unverifiable`: 46 (-64)
- `ambiguous`: 32 (-10)
- `impossible_false_premise`: 16 (-6)
- `other_unclear`: 10 (-303)

### answer_form
- `yes_no`: 628 (+9)
- `explanation`: 367 (+180)
- `short_phrase`: 170 (+132)
- `number`: 155 (+139)
- `entity`: 90 (+2)
- `list`: 8 (+5)
- `definition`: 2 (-22)

### label_confidence
- `medium`: 993 (+677)
- `low`: 406 (-297)
- `high`: 21 (-380)

### needs_human_review
- `false`: 1008 (+316)
- `true`: 412 (-316)

## Caveats

- This is a deterministic semantic cleanup, not model inference and not a final scientific coding adjudication.
- Labels remain broad exploratory categories; borderline philosophy/science and subjective/factual prompts may still need human review for publication-grade claims.
- `label_notes` retain prior notes after a v3 cleanup prefix for auditability.
