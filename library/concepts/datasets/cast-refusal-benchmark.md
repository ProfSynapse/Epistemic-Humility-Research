---
aliases:
- CAST
- CAST refusal benchmark
- contrastive harmful-benign refusal benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:cast-refusal-benchmark
  type: dataset
  status: canonical
area: safety-evaluation
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[contrastive-refusal-mask]]'
relationships:
- type: proposed_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
- type: used_by
  target: '[[contrastive-refusal-mask]]'
  target_id: method:contrastive-refusal-mask
  confidence: high
---

CAST is the paired harmful-vs-benign refusal evaluation used in Faithfulness to Refusal. It includes harmful prompts and matched benign prompts across hate, crime, adult, medical, and legal domains, allowing a refusal intervention to be tested for both malign refusal and benign over-refusal.

**Why it matters here:** CAST operationalizes a key epistemic-humility distinction: refusal should track the real unsafe condition rather than superficial topical similarity. It is useful for testing whether an intervention installs domain-sensitive refusal or merely raises blanket refusal.

**Lineage:** introduced by [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]] for contrastive refusal auditing.
