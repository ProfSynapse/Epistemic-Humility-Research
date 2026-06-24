---
aliases:
- imitative falsehood
- imitative falsehoods
- training-distribution falsehood
tags:
- kg/term
- concept
- term
kg:
  id: term:imitative-falsehood
  type: term
  status: canonical
area: terms
related:
- '[[2109.07958--truthfulqa]]'
- '[[truthfulqa]]'
- '[[hallucination]]'
- '[[sycophancy]]'
- '[[high-capacity-training-degrades-calibration]]'
- '[[dominant-uncertainty-source-shifts-with-model-scale]]'
relationships:
- type: proposed_by
  target: '[[2109.07958--truthfulqa]]'
  target_id: paper:2109.07958
  confidence: high
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[high-capacity-training-degrades-calibration]]'
  target_id: mechanism:high-capacity-training-degrades-calibration
  confidence: medium
- type: related_to
  target: '[[dominant-uncertainty-source-shifts-with-model-scale]]'
  target_id: mechanism:dominant-uncertainty-source-shifts-with-model-scale
  confidence: medium
---

A false answer that a language model produces because it has high likelihood on the model's training distribution, not because the model fails to generalize. The model is in effect imitating the false beliefs and misconceptions embedded in human-generated training text. Imitative falsehoods are distinguished from non-imitative falsehoods, which arise from syntactic or stylistic artifacts of a question rather than from training-distribution incentives.

**Why it matters here:** Imitative falsehoods are predicted to worsen with scale (as larger models learn the training distribution more thoroughly), making them a qualitatively different problem from capability failures. This mechanism motivates evaluation benchmarks like TruthfulQA that specifically target questions where training-distribution pressure favors a false answer, and it frames fine-tuning with non-imitation objectives as the primary remedy.

**Lineage:** Introduced in TruthfulQA (Lin et al., 2021, arXiv 2109.07958) as the core phenomenon the benchmark is designed to measure.
