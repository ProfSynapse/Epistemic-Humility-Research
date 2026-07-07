---
aliases:
- PPL
- language modeling perplexity
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:perplexity
  type: metric
  status: canonical
area: metrics
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: measured_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

Perplexity is the exponentiated average negative log-likelihood of a model on a text corpus. Lower perplexity indicates that the model assigns higher probability to the observed sequence, making it a standard fluency and language-modeling utility metric.

**Why it matters here:** Refusal or abstention interventions can appear behaviorally successful while degrading general modeling quality. Tracking perplexity helps distinguish targeted safety behavior from broad model damage.

**Lineage:** standard language-modeling metric; used as a utility guard in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
