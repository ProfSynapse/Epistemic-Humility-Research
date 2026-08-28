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

Perplexity is the exponentiated average negative log-likelihood a language
model assigns to held-out text, the standard scalar measure of language-
modeling quality.

**Why it matters here:** Sun et al. report perplexity alongside sink ratio and
spike magnitude for every ablation (normalization configuration, attention
gating, short-context-only training) to confirm that interventions which
suppress massive activations or attention sinks do not come at a meaningful
cost in language-modeling quality.

**Also used by:** Refusal or abstention interventions can appear behaviorally
successful while degrading general modeling quality. In Faithfulness to
Refusal, perplexity is tracked to distinguish targeted safety behavior from
broad model damage.

**Lineage:** standard language-modeling metric; used as a utility guard in
[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]] and
[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
