---
aliases:
- HaluEval
- HaluEval hallucination benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:halu-eval
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[hallucination]]'
- '[[faithful-calibration]]'
relationships:
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: medium
---

HaluEval is a hallucination-evaluation benchmark used to test whether language models produce or identify unsupported content. In this paper it appears as one of the 10 faithful-calibration evaluation datasets and as an alternative training task for robustness checks.

**Why it matters here:** Hallucination benchmarks probe whether a model can communicate uncertainty around unsupported or risky generations, making them natural tests for epistemic humility and faithful calibration.

**Lineage:** Related to hallucination and knowledge-boundary evaluation datasets, but represented here as a reusable dataset atom because multiple training and evaluation papers name it explicitly.
