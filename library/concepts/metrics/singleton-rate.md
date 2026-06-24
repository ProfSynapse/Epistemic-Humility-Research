---
aliases:
- training singleton fraction
- singleton frequency
- Turing missing-mass proxy
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:singleton-rate
  type: metric
  status: canonical
area: metrics
related:
- '[[2509.04664--why-language-models-hallucinate]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
- '[[knowledge-gap]]'
- '[[calibration]]'
relationships:
- type: proposed_by
  target: '[[2509.04664--why-language-models-hallucinate]]'
  target_id: paper:2509.04664
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[knowledge-gap]]'
  target_id: term:knowledge-gap
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

The fraction of training prompts that appear exactly once in the training data without abstention responses; derived from Turing's missing-mass estimator (Good-Turing). Serves as a lower bound on the hallucination rate of any pretrained base model on arbitrary-fact queries.

**Why it matters here:** Provides a data-coverage floor on hallucination that applies to any cross-entropy-trained model regardless of architecture, quantifying how much pretraining data sparsity forces irreducible errors.

**Lineage:** Formalized in Theorem 2 (Section 3.3.1) of this paper, building on the Good-Turing estimator (Good 1953) and the earlier Kalai-Vempala (2024) special case without prompts.
