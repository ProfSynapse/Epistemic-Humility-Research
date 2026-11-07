---
title: 'Sparks of Weight-Space Programming: LLMs can natively read & write neural
  network weights'
arxiv: ''
year: 2026
url: https://rikiyat.github.io/blog/weight-space-programming/
source_type: author_blog_with_experiment_logs
published: '2026-11-02'
area: steering
status: verified
verification_scope: Source and released logs read; empirical claims are author-reported,
  not independently reproduced here.
tags:
- paper
- epistemic-humility
- steering
- kg/paper
authors:
- Rikiya Takehi
- Jayden Teoh
- Alex Zhang
- Omar Khattab
models:
- Qwen3.5-0.8B
- Gemma 3 270M
metrics:
- MATH-500 accuracy
- GSM8K accuracy
- IFEval strict accuracy
pdf: ''
kg:
  id: paper:web-20261102-weight-space-programming
  type: paper
  status: canonical
aliases:
- weight space programming
- direct neural weight programming
- LLM reasoning-loop weight repair
related:
- '[[weight-space-programming]]'
- '[[rank-one-model-editing]]'
- '[[gsm8k]]'
- '[[ifeval]]'
- '[[sparse-mlp-loop-direction-removal-releases-existing-reasoning]]'
relationships:
- type: proposes
  target: '[[weight-space-programming]]'
  target_id: method:weight-space-programming
  confidence: high
- type: uses
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
  confidence: high
- type: evaluates_on
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: high
- type: evaluates_on
  target: '[[ifeval]]'
  target_id: dataset:ifeval
  confidence: high
- type: supports
  target: '[[sparse-mlp-loop-direction-removal-releases-existing-reasoning]]'
  target_id: mechanism:sparse-mlp-loop-direction-removal-releases-existing-reasoning
  confidence: medium
source_sha256:
  web-20261102-weight-space-programming-final-answer.md: 497ea024210e9bbc10826756997ef41b454dd524390fff1b2d4cdec6782c30d1
  web-20261102-weight-space-programming.html: 60e015f47e4c011297229519a93e36f845883303d80912f48328d8b00de33df9
  web-20261102-weight-space-programming-exp8.md: 473e386ade21ff52240103003b6b125e4362d9fa11010916c1b770ddb0edcbbd
---

## Source status

This is the authors' November 2 research blog and released experiment logs. The
alphaXiv address uses a descriptive identifier; this note does not assign an
arXiv paper number or claim peer review. Private acquisition copies are under
`library/fulltext/`, with hashes above. Logs/code are linked at the source.

## Abstract

The source has no separate formal abstract. Its question is whether a general
purpose LLM can inspect and directly program neural weights under natural
language goals, with bounded tools and without gradient-based training.

## Summary

Experiment 8 gives an editor access to tensors and budgeted practice-set forward
queries. The editor diagnoses repetitive thinking, then uses matched productive
and repetitive contexts to locate MLP output writers. Its final edit removes a
repetition direction from selected columns. The reasoning is that a localized
failure can obstruct an existing ability; a sparse repair can remove that
obstacle. The Gemma follow-up did not establish a capability gain when errors
were ordinary reasoning failures rather than repetition.

## Extracted numbers

Author-reported, not independently reproduced here:

| Qwen3.5-0.8B | MATH-500 | GSM8K | IFEval |
|---|---:|---:|---:|
| Base | 7.9% | 13.8% | 21.0% |
| 50-pass edit | 48.1% | 67.1% | 62.3% |

Source: article Experiment 8 table and released `exp8_math/README.md`, result-file
mapping to `eval/{unedited,p50c}/merged.json`.

The final edit targets 64 MLP output columns in each of layers15 and19:
131,072 touched entries. The released README distinguishes130,188 entries that
actually differ after bf16 rounding. Its 10/25/50 budgets count batched tool
queries, not individual examples or a universal compute budget.

## Claims

- Evidence label: author-reported intervention. Matched contexts, dose response,
  layer isolation and a norm-matched random control support the selected loop
  edit (released p50c final answer, Diagnosis and evidence).
- Evidence label: author-reported paired practice confirmation. Most rescues
  were formerly truncated outputs; this supports obstacle removal rather than
  learning new mathematical knowledge (same final answer, paired confirmation).
- Evidence label: author-reported negative follow-up. The article's Gemma
  experiment does not establish a math gain without the looping failure.

## Relevance to experiment

A prospective EHR transfer is to diagnose a missing relationship between
answerability information and response behavior, identify the writers carrying
that relationship, and evaluate a small permanent edit on benefit and known-item
cost. An answerability readout alone does not establish a causal actuator.

The earlier unsigned multi-candidate hs20 draft was replaced before evaluation
by one fixed Astra-designed sparse edit. That study is now terminal `falsified`,
with a valid instrument: both primary benefit gates failed while all three
preservation/quality cost gates passed; transfer was unsupported.
See [the governed AMENDMENT section 9 at ef678d4f](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/ef678d4f068b1cede54af4141de92f445f43e400/experiments/qwen35-4b-hs20-native-weight-edit/AMENDMENT.md#9-outcome)
(PR #604 merged on 2026-11-04). This is an exploratory EHR
adaptation, not a replication or refutation of the authors' loop-repair result.
The separate broader R3 follow-up [[qwen35-4b-astra-column-budget-followup]] is now terminal `falsified`,
with a disclosed PI-approved grading deviation. Its primary truthful-gain gate
fails; the other four primary gates pass. Secondary P-rc success does not rescue
the primary and transfer is unsupported. See [R3 Outcome and grading deviation](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/8184c32d93eda1e5d0b50787bdd4d15de4e3c509/experiments/qwen35-4b-astra-column-budget-followup/AMENDMENT.md#7-outcome).
Its governed record is pushed on PR #606, not merged at this update. This
exploratory EHR adaptation does not refute the authors' loop-repair result or
establish that permanent editing generally fails. No source-paper claim, R1
grading or R1 outcome is revised here.

## Sources

- [Author report](https://rikiyat.github.io/blog/weight-space-programming/)
- [Released Experiment8 protocol and result mapping](https://github.com/RikiyaT/lm_understand-logs/blob/main/exp8_math/README.md)
- [Final edit diagnosis and paired practice evidence](https://github.com/RikiyaT/lm_understand-logs/blob/main/exp8_math/runs/p50c/final_answer.md)
