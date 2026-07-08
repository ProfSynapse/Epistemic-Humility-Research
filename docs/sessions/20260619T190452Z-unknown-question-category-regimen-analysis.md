---
schema_version: research-session/v1
session_id: 20260619T190452Z-unknown-question-category-regimen-analysis
title: Unknown-Question Category-Regimen Analysis
status: active
created_at: '2026-06-19T19:04:52Z'
updated_at: '2026-06-19T19:04:52Z'
phase: phase1
question: Capture exploratory row-pattern analysis of unknown-question semantic categories
  across SFT, DPO, and KTO regimens.
tags:
- phase1
- exploratory-analysis
- unknown-questions
- semantic-labels
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Exploratory semantic category-regimen analysis exists for answered
    unknown-question rows using v3 labels, but is not publication-grade evidence.
  changed_by_session: Adds a documentation checkpoint for the category-regimen exploratory
    pattern and records follow-up validation work.
checkpoints:
- id: 001-result
  at: '2026-06-19T19:04:52Z'
  kind: result
  title: Category-Regimen Unknown-Question Outputs Captured
  summary: Row-pattern analysis materialized category-regimen outputs using v3 semantic
    labels for unknown-question rows. The join uses v3 labels explicitly and covers
    the answered-by-any-arm unknown-question subset rather than every source unknown
    row.
  evidence:
  - docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md
  run_ids: []
  commands: []
  decisions:
  - Treat the category-regimen outputs as exploratory analysis, not pre-registered
    headline evidence.
  next_steps:
  - Validate semantic labels and quantify category-level effects before using these
    patterns for publication-grade claims.
  signals:
    source_unknown_rows: 12960
    joined_unknown_rows: 9090
    missing_unknown_rows: 3870
    v3_labeled_answered_unknown_questions: 1420
- id: 002-validation
  at: '2026-06-19T19:04:52Z'
  kind: validation
  title: Join Scope Interpreted
  summary: The missing 3,870 source unknown rows are expected under the current label
    artifact scope because v3 semantic labels cover questions answered by at least
    one arm, not always-unanswered unknown questions. This validates the join scope
    as explicit, while also marking the unlabeled always-unanswered rows as a coverage
    gap.
  evidence:
  - docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md
  run_ids: []
  commands: []
  decisions:
  - Do not interpret the joined table as full coverage of unknown-question behavior.
  - Preserve the distinction between source unknown rows, joined unknown rows, and
    unique v3-labeled answered unknown questions.
  next_steps:
  - Add labels for always-unanswered unknown questions before making category-complete
    claims.
  signals:
    label_scope: answered_by_any_arm
    category_join_uses_v3_labels: true
- id: 003-interpretation
  at: '2026-06-19T19:04:52Z'
  kind: interpretation
  title: Exploratory Regimen Pattern
  summary: The exploratory pattern suggests DPO sharply increases answering on unknown
    questions, especially in math_logic, math_word_problem_missing_info, underspecified,
    future_or_unverifiable, religion_philosophy_ethics, and science_health categories.
    KTO appears intermediate and more conservative, while SFT preserves abstention
    most strongly.
  evidence:
  - docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md
  run_ids: []
  commands: []
  decisions:
  - Label this as a broad semantic-pattern readout rather than a gold-label finding.
  - Treat answer_form fields as less reliable than the abstention/answer-on-unknown
    pattern until representative examples are reviewed.
  next_steps:
  - Review representative examples by category and regimen to check whether the apparent
    DPO answer-rate increase reflects real over-answering.
  signals:
    caveats:
    - exploratory_vibes
    - broad_semantic_labels_not_gold
    - answer_form_less_reliable
    - always_unanswered_unknown_questions_not_labeled
- id: 004-follow-up
  at: '2026-06-19T19:04:52Z'
  kind: checkpoint
  title: Publication-Grade Work Deferred
  summary: Follow-up work should label always-unanswered unknown questions, run category-level
    statistical checks, review representative examples, and validate v3 semantic labels
    before using category-regimen effects as publication-grade claims.
  evidence:
  - TODO.md
  - docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md
  run_ids: []
  commands: []
  decisions:
  - Keep the current session note documentation-only; no reruns, code changes, or
    analysis artifact edits were performed.
  next_steps:
  - Use TODO.md to track the deeper category-regimen exploration and validation items.
  signals: {}
legacy_session:
  id: unknown-question-category-regimen-analysis
  path: docs/sessions/0009 - unknown-question-category-regimen-analysis.md
---
# 0009 - Unknown-Question Category-Regimen Analysis

## Status

This note captures an exploratory analysis checkpoint only. It does not change
the protocol, authorize reruns, or convert the category-regimen pattern into
pre-registered headline evidence.

## Summary

Row-pattern analysis produced category-regimen outputs for unknown questions
using v3 semantic labels. The category-regimen join uses v3 labels explicitly.
The v3 label artifact covers 1,420 answered-unknown questions: questions that
were answered by at least one arm. At the row level, the source unknown pool has
12,960 rows, the joined unknown table has 9,090 rows, and 3,870 rows are missing
from the join because always-unanswered unknown questions are outside the
current label artifact scope.

The exploratory pattern is that DPO sharply increases answer-on-unknown behavior,
especially in `math_logic`, `math_word_problem_missing_info`, `underspecified`,
`future_or_unverifiable`, `religion_philosophy_ethics`, and `science_health`.
KTO appears intermediate and more conservative. SFT preserves abstention most.

These are exploratory/vibes-level findings. The semantic labels are broad and
not gold labels, `answer_form` is less reliable than the answer/abstain signal,
and always-unanswered unknown questions are not yet labeled.

## Checkpoints

### 001-result - Category-Regimen Unknown-Question Outputs Captured

- at: `2026-06-19T19:04:52Z`
- kind: `result`
- summary: Row-pattern analysis materialized category-regimen outputs using v3 semantic labels for unknown-question rows. The join uses v3 labels explicitly and covers the answered-by-any-arm unknown-question subset rather than every source unknown row.
- evidence:
  - `docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md`
- decisions:
  - Treat the category-regimen outputs as exploratory analysis, not pre-registered headline evidence.
- next steps:
  - Validate semantic labels and quantify category-level effects before using these patterns for publication-grade claims.
- signals:
  - source unknown rows: `12960`
  - joined unknown rows: `9090`
  - missing unknown rows: `3870`
  - v3 labeled answered unknown questions: `1420`

### 002-validation - Join Scope Interpreted

- at: `2026-06-19T19:04:52Z`
- kind: `validation`
- summary: The missing 3,870 source unknown rows are expected under the current label artifact scope because v3 semantic labels cover questions answered by at least one arm, not always-unanswered unknown questions. This validates the join scope as explicit, while also marking the unlabeled always-unanswered rows as a coverage gap.
- evidence:
  - `docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md`
- decisions:
  - Do not interpret the joined table as full coverage of unknown-question behavior.
  - Preserve the distinction between source unknown rows, joined unknown rows, and unique v3-labeled answered unknown questions.
- next steps:
  - Add labels for always-unanswered unknown questions before making category-complete claims.
- signals:
  - label scope: `answered_by_any_arm`
  - category join uses v3 labels: `true`

### 003-interpretation - Exploratory Regimen Pattern

- at: `2026-06-19T19:04:52Z`
- kind: `interpretation`
- summary: The exploratory pattern suggests DPO sharply increases answering on unknown questions, especially in math_logic, math_word_problem_missing_info, underspecified, future_or_unverifiable, religion_philosophy_ethics, and science_health categories. KTO appears intermediate and more conservative, while SFT preserves abstention most strongly.
- evidence:
  - `docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md`
- decisions:
  - Label this as a broad semantic-pattern readout rather than a gold-label finding.
  - Treat answer_form fields as less reliable than the abstention/answer-on-unknown pattern until representative examples are reviewed.
- next steps:
  - Review representative examples by category and regimen to check whether the apparent DPO answer-rate increase reflects real over-answering.
- signals:
  - caveats: `exploratory_vibes`, `broad_semantic_labels_not_gold`, `answer_form_less_reliable`, `always_unanswered_unknown_questions_not_labeled`

### 004-follow-up - Publication-Grade Work Deferred

- at: `2026-06-19T19:04:52Z`
- kind: `checkpoint`
- summary: Follow-up work should label always-unanswered unknown questions, run category-level statistical checks, review representative examples, and validate v3 semantic labels before using category-regimen effects as publication-grade claims.
- evidence:
  - `TODO.md`
  - `docs/sessions/20260619T190452Z-unknown-question-category-regimen-analysis.md`
- decisions:
  - Keep the current session note documentation-only; no reruns, code changes, or analysis artifact edits were performed.
- next steps:
  - Use TODO.md to track the deeper category-regimen exploration and validation items.
