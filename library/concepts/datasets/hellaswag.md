---
aliases:
- HellaSwag
- Harder Endings Longer contexts and Low-shot Activities For Situations With Adversarial Generations
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:hellaswag
  type: dataset
  status: canonical
area: datasets
related:
- '[[2310.11732--calibration-aligned-multiple-choice]]'
- '[[mmlu]]'
- '[[truthfulqa]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2310.11732--calibration-aligned-multiple-choice]]'
  target_id: paper:2310.11732
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

A commonsense NLI benchmark (Zellers et al. 2019) in which the model must select the most plausible continuation of a given context sentence from four candidates. Constructed via adversarial filtering so surface-level n-gram overlap does not distinguish correct from incorrect continuations.

**Why it matters here:** Used in this paper as one of seven MCQ benchmarks for calibration evaluation; represents the commonsense reasoning domain in the cross-domain ECE comparison.

**Lineage:** Zellers et al. 2019; used in He et al. 2023 (arXiv:2310.11732) as an MCQ calibration benchmark.
