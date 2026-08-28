---
aliases:
- Phi-2
- Microsoft Phi-2
- microsoft/phi-2
tags:
- kg/model
- concept
- model
kg:
  id: model:phi-2
  type: model
  status: canonical
area: models
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuitkit]]'
relationships:
- type: studied_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: medium
- type: studied_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[circuitkit]]'
  target_id: method:circuitkit
  confidence: medium
---

Phi-2 is Microsoft's roughly 2.7-billion-parameter decoder-only transformer, trained predominantly on curated synthetic and filtered web data. Its architecture includes parallel attention and MLP blocks with partial rotary embeddings.

**Why it matters here:** Confidence-regulation work uses Phi-2 to test whether entropy-neuron mechanisms recur outside standard web-pretraining mixtures, while CircuitKIT uses it to test circuit discovery and intervention portability across model architectures.

**Lineage:** Studied in [[2406.16254--confidence-regulation-neurons-language-models]] and [[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]].
