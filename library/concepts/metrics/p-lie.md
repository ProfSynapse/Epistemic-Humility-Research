---
aliases:
- probability of lying
- lying rate
- commission dishonesty rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:p-lie
  type: metric
  status: canonical
area: metrics
related:
- '[[2503.03750--mask-benchmark-honesty]]'
- '[[mask-benchmark]]'
- '[[honesty-score]]'
- '[[truthfulness-score]]'
- '[[abstention-rate]]'
- '[[sycophancy]]'
relationships:
- type: proposed_by
  target: '[[2503.03750--mask-benchmark-honesty]]'
  target_id: paper:2503.03750
  confidence: high
- type: related_to
  target: '[[mask-benchmark]]'
  target_id: dataset:mask-benchmark
  confidence: medium
- type: related_to
  target: '[[honesty-score]]'
  target_id: metric:honesty-score
  confidence: medium
- type: related_to
  target: '[[truthfulness-score]]'
  target_id: metric:truthfulness-score
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
---

The proportion of MASK benchmark examples on which a model's pressured statement contradicts its independently-elicited belief, excluding cases where the model evades or holds no consistent belief. Defined as 1 minus the MASK honesty score. Lower is better.

**Why it matters here:** Separates intentional deception (model knows truth, states falsehood) from inaccuracy (model believes falsehood) and from over-abstention (model refuses). Makes honesty-under-pressure a quantifiable, model-comparable scalar independent of factual accuracy.

**Lineage:** Introduced in the MASK benchmark (2503.03750). Distinct from the honesty-score proposed in 2312.07000, which measures abstention quality rather than commission lying.
