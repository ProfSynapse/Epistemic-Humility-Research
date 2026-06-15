---
aliases:
- MATH
- MATH dataset
- competition-level MATH
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:math-benchmark
  type: dataset
  status: canonical
area: datasets
related:
- '[[gsm8k]]'
- '[[deepseekmath-corpus]]'
relationships:
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
- type: related_to
  target: '[[deepseekmath-corpus]]'
  target_id: dataset:deepseekmath-corpus
---

The MATH benchmark (Hendrycks et al., 2021) is a competition-level mathematics
dataset covering algebra, number theory, counting and probability, geometry,
intermediate algebra, precalculus, and prealgebra, with problems drawn from AMC,
AIME, and similar olympiad-style contests. Problems are tagged by subject and
difficulty level (1-5), and each includes a full worked solution, enabling
chain-of-thought evaluation. It is one of the standard benchmarks for gauging
LLM mathematical reasoning.

**Why it matters here:** MATH is used as an evaluation target in work on
reasoning fine-tuning and GRPO-based post-training, which is background context
for how online RL affects model knowledge and, by extension, abstention behavior.

**Lineage:** companion benchmark to [[gsm8k]] (which tests grade-school
arithmetic); both are standard evaluation targets used alongside
[[deepseekmath-corpus]] in the DeepSeekMath line of work.
