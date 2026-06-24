---
aliases:
- decisiveness scorer
- LLM-as-judge decisiveness
- hedge decisiveness LLM judge
- decisiveness score
tags:
- kg/method
- concept
- method
kg:
  id: method:linguistic-decisiveness-scorer
  type: method
  status: canonical
area: methods
related:
- '[[2606.03969--faithful-calibration-framework]]'
- '[[cmfg-star]]'
- '[[faithful-calibration]]'
- '[[verbalized-confidence]]'
- '[[llm-as-judge]]'
relationships:
- type: proposed_by
  target: '[[2606.03969--faithful-calibration-framework]]'
  target_id: paper:2606.03969
  confidence: high
- type: related_to
  target: '[[cmfg-star]]'
  target_id: metric:cmfg-star
  confidence: medium
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
---

An LLM-as-judge system (implemented with Gemini-2.5-Flash in batched-20 mode) that reads a model's final answer and assigns a scalar decisiveness score reflecting how hedged or definitive the verbal expression of confidence is. Achieves Pearson r=0.884 and Spearman r=0.869 against human ratings on a 300-example short-form validation set. Used as the verbal-confidence component in the cMFG* faithful calibration metric.

**Why it matters here:** Operationalizes linguistic decisiveness as a measurable scalar, enabling quantitative comparison of verbal confidence expression across models, training regimes, and prompts, and making it composable with internal confidence estimators in the cMFG* compound metric.

**Lineage:** Introduced in Gani et al. 2026 (arXiv:2606.03969) as part of their faithful calibration framework for large reasoning models.
