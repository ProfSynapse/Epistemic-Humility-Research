---
aliases:
- perplexity
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
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: measured_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: measured_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

Perplexity is the exponentiated average negative log-likelihood that a language model assigns to held-out text. Lower perplexity indicates that the model assigns higher probability to the observed sequence, making it a standard language-modeling quality metric.

**Why it matters here:** Refusal, abstention, and activation interventions can appear behaviorally successful while degrading general modeling quality. The cited papers use perplexity as a utility guard when testing refusal masks and interventions on massive activations or attention sinks.

**Lineage:** Standard language-modeling metric; used as a utility guard in [[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]] and [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
