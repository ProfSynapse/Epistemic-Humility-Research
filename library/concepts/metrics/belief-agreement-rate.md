---
aliases:
- agreement rate
- belief agreement rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:belief-agreement-rate
  type: metric
  status: canonical
area: metrics
related:
- '[[2311.09410--llm-sycophantic-behaviour]]'
- '[[sycophancy]]'
- '[[non-contradiction-benchmark]]'
- '[[truthfulness-score]]'
relationships:
- type: proposed_by
  target: '[[2311.09410--llm-sycophantic-behaviour]]'
  target_id: paper:2311.09410
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[non-contradiction-benchmark]]'
  target_id: dataset:non-contradiction-benchmark
  confidence: medium
- type: related_to
  target: '[[truthfulness-score]]'
  target_id: metric:truthfulness-score
  confidence: medium
---

The percentage of model responses that agree with the human belief or viewpoint expressed in the input prompt, measured on open-ended opinion or belief benchmarks (such as NLP-Q, PHIL-Q, POLI-Q). A model with a high belief-agreement rate is one that echoes the user's stated position rather than providing a neutral or contrary response.

**Why it matters here:** Operationalizes sycophancy in the belief domain where there is no objectively correct answer. Distinct from accuracy-based metrics used in factual QA; high belief-agreement rate is interpreted as evidence of sycophancy, not competence.

**Lineage:** Operationalized in Ranaldi and Pucci 2023 (arXiv:2311.09410); extends the analysis of Perez et al. 2022 (arXiv:2212.09251) on the NLP-Q, PHIL-Q, and POLI-Q benchmarks.
