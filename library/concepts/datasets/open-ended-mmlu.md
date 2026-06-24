---
aliases:
- OE MMLU
- open-ended variant of MMLU
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:open-ended-mmlu
  type: dataset
  status: canonical
area: datasets
related:
- '[[2406.08391--taught-to-know-what-they-dont-know]]'
- '[[mmlu]]'
- '[[calibration-tuning]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[selfaware]]'
relationships:
- type: proposed_by
  target: '[[2406.08391--taught-to-know-what-they-dont-know]]'
  target_id: paper:2406.08391
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[calibration-tuning]]'
  target_id: method:calibration-tuning
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: medium
---

An open-ended variant of the MMLU benchmark introduced by Kapoor et al. (2024) in which answer choices are withheld and the model must generate a free-form answer that is then graded for correctness by a strong auxiliary LLM. The dataset spans the same 57 subjects as standard MMLU but removes the multiple-choice scaffold, exposing uncertainty estimation methods to the full difficulty of open-ended generation.

**Why it matters here:** Reveals a fundamental failure mode of prompting-based and perplexity-based uncertainty methods that perform acceptably on multiple-choice MMLU but break down completely on open-ended generation. Serves as a harder, more practically relevant evaluation for calibration and selective-prediction research.

**Lineage:** Introduced in arXiv:2406.08391 as an extension of the standard MMLU benchmark (Hendrycks et al., 2021). Grading via auxiliary LLM is validated against human grading in Appendix A.3 of that paper.
